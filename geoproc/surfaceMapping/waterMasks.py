import geopandas as gpd
import pandas as pd
from shapely.geometry import *
from typing import List, Union, Tuple
import xarray as xr
from glob import glob
import functools
from multiprocessing import Pool
from  xarray.core.groupby import DatasetGroupBy
from geoproc.util.configuration import sanitize, ConfigurableObject
import matplotlib.pyplot as plt
import numpy as np
import os, time

class WaterMapGenerator(ConfigurableObject):

    def __init__( self, **kwargs ):
        ConfigurableObject.__init__( **kwargs )
        pass

    def get_persistent_classes(self,  water_probability: xr.DataArray, thresholds: List[float], mask_value ) -> xr.DataArray:
        perm_water_mask = water_probability > thresholds[1]
        perm_land_mask =  water_probability < thresholds[0]
        boundaries_mask = water_probability > 1.0
        return xr.where( boundaries_mask, mask_value,
                             xr.where(perm_water_mask, 2,
                                 xr.where(perm_land_mask, 1, 0)) )

    def get_water_prob(self,  cropped_data, mask_value, yearly = False ):
        from datetime import datetime
        water = cropped_data.isin( [2,3] )
        land = cropped_data.isin( [1] )
        masked = cropped_data[0].isin( [mask_value] ).drop_vars( cropped_data.dims[0] )
        if yearly:
            water_cnts = water.groupby("time.year").sum()
            land_cnts  = land.groupby("time.year").sum()
        else:
            water_cnts = water.sum(axis=0)
            land_cnts = land.sum(axis=0)
        visible_cnts = (water_cnts + land_cnts)
        water_prob: xr.DataArray = water_cnts / visible_cnts
        water_prob = water_prob.where( masked == False, 1.01 )
        water_prob.name = "water_probability"
        if yearly:
            time_values = np.array( [ np.datetime64( datetime( year, 7, 1 ) ) for year in water_prob.year.data ], dtype='datetime64[ns]' )
            water_prob = water_prob.assign_coords( year=time_values ).rename( year='time' )
        return water_prob

    def get_water_mask(self, inputs: Union[ xr.DataArray, List[xr.DataArray] ], threshold = 0.5, mask_value = 0 )-> xr.Dataset:
        da: xr.DataArray = self.time_merge(inputs) if isinstance(inputs, list) else inputs
        binSize = da.shape[0]
        masked = da[0].isin( [mask_value] ).drop_vars( inputs.dims[0] )
        land = da.isin( [1] ).sum( axis=0 )
        water =  da.isin( [2,3] ).sum( axis=0 )
        visible = ( water + land )
        reliability = visible / float(binSize)
        prob_h20 = water / visible
        water_mask = prob_h20 >= threshold
        result =  xr.where( masked, mask_value, xr.where( water_mask, 2, xr.where( land, 1, 0 ) ) )
        return xr.Dataset( { "mask": result,  "reliability": reliability } )

    def get_water_masks(self, data_array: xr.DataArray, binSize: int, threshold = 0.5, mask_value=0  ) -> xr.Dataset:
        print("\n Executing get_water_masks ")
        t0 = time.time()
        bin_indices = list(range( 0, data_array.shape[0]+1, binSize ))
        centroid_indices = list(range(binSize//2, bin_indices[-1], binSize))
        time_axis = data_array.coords[ data_array.dims[0] ].values
        time_bins = np.array( [ time_axis[iT] for iT in bin_indices ], dtype='datetime64[ns]' )
        grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins, right = False )
        results:  xr.Dataset = grouped_data.map( self.get_water_mask, threshold = threshold, mask_value=mask_value )
        print( f" Completed get_water_masks in {time.time()-t0:.3f} seconds" )
        for result in results.values(): self.transferMetadata( data_array, result )
        return results.assign( time_bins = [ time_axis[i] for i in centroid_indices ]  ).rename( time_bins='time' )


    def update_metrics( self, data_array: xr.DataArray, **kwargs ):
        metrics = data_array.attrs.get('metrics', {} )
        metrics.update( **kwargs )
        data_array.attrs['metrics'] = metrics

    def patch_water_map( self, persistent_classes: xr.DataArray, input_array: xr.DataArray  ) -> xr.DataArray:
        dynamics_mask = persistent_classes.isin( [0] )
        result = input_array.where( dynamics_mask, persistent_classes )
        return result

    def patch_water_maps( self, persistent_classes: xr.DataArray, inputs: xr.DataArray, dynamics_class: int = 0  ) -> xr.DataArray:
        persistent_classes = persistent_classes.interp_like( inputs, method='nearest' ).ffill(persistent_classes.dims[0]).bfill(persistent_classes.dims[0])
        dynamics_mask = persistent_classes.isin( [dynamics_class] )
        result = xr.where( dynamics_mask, inputs, persistent_classes  )
        patched_result: xr.DataArray = result.where( result == inputs, persistent_classes + 2 )
        return patched_result

    # def get_matching_slice( self, water_masks: xr.DataArray, match_score: xr.DataArray, current_slice: int ):
    #     match_score[ current_slice ] = 0
    #     matching_slice = water_masks[ match_score.argmax() ]
    #     return matching_slice

    # def temporal_interpolate( self, persistent_classes: xr.DataArray, water_masks: xr.DataArray, current_slice_index: int, **kwargs ):
    #     dynamics_mask = persistent_classes == 1
    #     sdims = water_masks.dims[1:]
    #     current_slice = water_masks[current_slice_index].drop_vars( water_masks.dims[0] )
    #     critical_undef_count = xr.where(dynamics_mask, water_masks == 0, 0 ).sum( dim = sdims )
    #     valid_mask = np.logical_and( dynamics_mask, water_masks > 0 )
    #     matches = xr.where(valid_mask, water_masks == current_slice, 0)
    #     match_count = matches.sum( dim = sdims )
    #     mismatch_count = xr.where( valid_mask, water_masks != current_slice, 0 ).sum( dim = sdims )
    #     match_scores = match_count - mismatch_count - critical_undef_count
    #     matching_slice = get_matching_slice( water_masks, match_scores, current_slice_index )
    #     interp_slice: xr.DataArray = current_slice.where( current_slice != 0, matching_slice + 2  )
    #     water_masks[ current_slice_index ] = interp_slice
    #     return dict( match_scores=match_scores, interp_water_masks = water_masks, match_count = match_count, mismatch_count=mismatch_count,  critical_undef_count=critical_undef_count, matches=matches )

    def temporal_patch_slice( self, water_masks: xr.DataArray, slice_index: int, patched_slice=None, patch_slice_index=None  ) -> xr.DataArray:
        current_slice = patched_slice if patched_slice is not None else water_masks[slice_index].drop_vars(water_masks.dims[0])
        undef_Mask: xr.DataArray = ( current_slice == 0 )
        current_patch_slice_index = slice_index - 1 if patch_slice_index is None else patch_slice_index - 1
        if (undef_Mask.count() == 0) or (current_patch_slice_index < 0): return current_slice
        patch_slice = water_masks[ current_patch_slice_index ].drop_vars(water_masks.dims[0])
        recolored_patch_slice = patch_slice.where( patch_slice == 0, patch_slice + 2  )
        current_patched_slice = current_slice.where( current_slice>0, recolored_patch_slice )
        return self.temporal_patch_slice( water_masks, slice_index, current_patched_slice, current_patch_slice_index )

    def temporal_patch( self, water_masks: xr.DataArray, nProcesses: int = 8  ) -> xr.DataArray:
        slices = list(range( water_masks.shape[0]))
        patcher = functools.partial( self.temporal_patch_slice, water_masks )
        with Pool(nProcesses) as p:
            patched_slices = p.map( patcher, slices, nProcesses)
            return self.time_merge( patched_slices, time=water_masks.coords[ water_masks.dims[0] ] )

    def time_merge( cls, data_arrays: List[xr.DataArray], **kwargs ) -> xr.DataArray:
        time_axis = kwargs.get('time',None)
        frame_indices = range( len(data_arrays) )
        merge_coord = pd.Index( frame_indices, name=kwargs.get("dim","time") ) if time_axis is None else time_axis
        result: xr.DataArray =  xr.concat( data_arrays, dim=merge_coord )
        return result # .assign_coords( {'frames': frame_names } )