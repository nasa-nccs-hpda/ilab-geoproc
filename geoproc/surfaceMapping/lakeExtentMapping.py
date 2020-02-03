import geopandas as gpd
import pandas as pd
from shapely.geometry import *
from typing import List, Union, Tuple, Dict, Optional
import xarray as xr
from glob import glob
import functools
from multiprocessing import Pool
from  xarray.core.groupby import DatasetGroupBy
from geoproc.util.configuration import sanitize, ConfigurableObject
import matplotlib.pyplot as plt
import numpy as np
import os, time, collections

class WaterMapGenerator(ConfigurableObject):

    def __init__( self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        pass

    def get_data_colors(self, mask_value=5 ) -> List[Tuple]:
        return [(0, 'undetermined', (1, 1, 0)),
               (1, 'land', (0, 1, 0)),
               (2, 'water', (0, 0, 1)),
               (mask_value, 'mask', (0.25, 0.25, 0.25))]

    def get_water_map_colors(self, mask_value=5, mismatch_value=6 ) -> List[Tuple]:
        return [(0, 'nodata', (0, 0, 0)),
               (1, 'land', (0, 1, 0)),
               (2, 'water', (0, 0, 1)),
               (3, 'interp land', (0, 0.5, 0)),
               (4, 'interp water', (0, 0, 0.5)),
               (mask_value, 'mask', (0.25, 0.25, 0.25)),
               (mismatch_value, 'mismatches', (1, 1, 0))]

    @classmethod
    def get_date_from_year(cls, year: int):
        from datetime import datetime
        result = datetime(year, 1, 1)
        return np.datetime64(result)

    def get_yearly_lake_area_masks( self, opspec: Dict, **kwargs) -> Optional[xr.DataArray]:
        from geoproc.xext.xrio import XRio
        images = {}
        data_dir = opspec.get('data_dir')
        lake_masks_dir = opspec.get('lake_masks_dir', None )
        if lake_masks_dir is None: return None
        lake_index = opspec.get('lake_index')
        lake_id = opspec.get('lake_id', f"lake-{lake_index}" )
        yearly_lake_masks_file = os.path.join(data_dir, f"Lake{lake_id}_fill_masks.nc")
        cache = kwargs.get('cache',True)
        lake_mask_nodata = opspec.get('lake_masks_nodata', 256)
        roi = opspec.get('roi', None)
        lake_mask: gpd.GeoSeries = gpd.read_file(roi) if roi else None
        if cache=="true" and os.path.isfile( yearly_lake_masks_file ):
            yearly_lake_masks_dataset: xr.Dataset = xr.open_dataset(yearly_lake_masks_file)
            yearly_lake_masks: xr.DataArray = yearly_lake_masks_dataset.yearly_lake_masks
        else:
             for sdir in glob( f"{lake_masks_dir}/*" ):
                year = os.path.basename(sdir)
                filepath = f"{lake_masks_dir}/{year}/lake{lake_index}_{year}.tif"
                images[int(year)] = filepath
             sorted_file_paths = collections.OrderedDict(sorted(images.items()))
             time_values = np.array([self.get_date_from_year(year) for year in sorted_file_paths.keys()], dtype='datetime64[ns]')
             yearly_lake_masks: xr.DataArray = XRio.load(list(sorted_file_paths.values()), mask=lake_mask, band=0, mask_value=lake_mask_nodata, index=time_values)

        if cache in [ "true", "update" ]:
            result = xr.Dataset(dict(yearly_lake_masks=sanitize(yearly_lake_masks)))
            result.to_netcdf(yearly_lake_masks_file)
            print(f"Saved cropped_data to {yearly_lake_masks_file}")

        return yearly_lake_masks

    def get_persistent_classes(self, water_probability: xr.DataArray, opspec: Dict, **kwargs) -> xr.DataArray:
        thresholds = opspec.get('water_class_thresholds', [ 0.05, 0.95 ] )
        mask_value = opspec.get('mask_value', 5)
        yearly_lake_masks:  xr.DataArray = self.get_yearly_lake_area_masks( opspec, **kwargs )
        yearly_lake_masks = yearly_lake_masks.interp_like( water_probability, method='nearest' )
        perm_water_mask: xr.DataArray = water_probability > thresholds[1]
        boundaries_mask: xr.DataArray = water_probability > 1.0
        if yearly_lake_masks is None:
            perm_land_mask = water_probability < thresholds[0]
            boundaries_mask = water_probability > 1.0
            return xr.where(boundaries_mask, mask_value,
                            xr.where(perm_water_mask, 2,
                                     xr.where(perm_land_mask, 1, 0)))
        else:
            apply_thresholds_partial = functools.partial(self.apply_thresholds, boundaries_mask, perm_water_mask, mask_value = mask_value )
            return yearly_lake_masks.groupby(yearly_lake_masks.dims[0]).map(apply_thresholds_partial)

    def apply_thresholds(self, boundaries_mask: xr.DataArray, perm_water_mask: xr.DataArray, yearly_lake_mask: xr.DataArray, **kwargs ) -> xr.DataArray:
        mask_value = kwargs.get('mask_value')
        perm_land_mask: xr.DataArray = (yearly_lake_mask == 0)
        return xr.where(boundaries_mask, mask_value,
                        xr.where(perm_water_mask, 2,
                                 xr.where(perm_land_mask, 1, 0)))

    def get_water_probability(self, cropped_data: xr.DataArray, opspec: Dict, **kwargs ) -> xr.DataArray:
        from datetime import datetime
        cache = kwargs.get( "cache", True )
        yearly_lake_masks_dir = opspec.get( 'yearly_lake_masks_dir', None )
        yearly = yearly_lake_masks_dir is not None
        data_dir = opspec.get('data_dir')
        lake_index = opspec.get('lake_index')
        lake_id = opspec.get('lake_id', f"lake-{lake_index}" )
        water_probability_file = os.path.join(data_dir, f"{lake_id}_water_probability.nc")
        mask_value = opspec.get('mask_value',5)

        water = cropped_data.isin([2, 3])
        land = cropped_data.isin([1])
        masked = cropped_data[0].isin([mask_value]).drop_vars(cropped_data.dims[0])

        if cache=="true" and os.path.isfile( water_probability_file ):
            water_probability_dataset: xr.Dataset = xr.open_dataset(water_probability_file)
            water_probability: xr.DataArray = water_probability_dataset.water_probability
        else:
            if yearly:
                water_cnts = water.groupby("time.year").sum()
                land_cnts  = land.groupby("time.year").sum()
            else:
                water_cnts = water.sum(axis=0)
                land_cnts = land.sum(axis=0)
            visible_cnts = (water_cnts + land_cnts)
            water_probability: xr.DataArray = water_cnts / visible_cnts
            water_probability = water_probability.where( masked == False, 1.01 )
            water_probability.name = "water_probability"
            if yearly:
                time_values = np.array( [ np.datetime64( datetime( year, 7, 1 ) ) for year in water_probability.year.data ], dtype='datetime64[ns]' )
                water_probability = water_probability.assign_coords( year=time_values ).rename( year='time' )
            if cache in ["true","update"]:
                result = xr.Dataset(dict(water_probability=sanitize(water_probability)))
                result.to_netcdf(water_probability_file)
                print(f"Saved water_probability to {water_probability_file}")
        return water_probability

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

    def interpolate(self, persistent_classes: xr.DataArray, water_maps: xr.DataArray ) -> xr.DataArray:
        patched_water_maps: xr.DataArray = self.spatial_interpolate( persistent_classes, water_maps )
        return self.temporal_interpolate( patched_water_maps )

    def spatial_interpolate( self, persistent_classes: xr.DataArray, water_maps: xr.DataArray, dynamics_class: int = 0  ) -> xr.DataArray:
        persistent_classes = persistent_classes.interp_like( water_maps, method='nearest' ).ffill(persistent_classes.dims[0]).bfill(persistent_classes.dims[0])
        dynamics_mask = persistent_classes.isin( [dynamics_class] )
        result = xr.where( dynamics_mask, water_maps, persistent_classes  )
        patched_result: xr.DataArray = result.where( result == water_maps, persistent_classes + 2 )
        return patched_result

    def temporal_interpolate_slice( self, water_maps: xr.DataArray, slice_index: int, patched_slice=None, patch_slice_index=None  ) -> xr.DataArray:
        current_slice = patched_slice if patched_slice is not None else water_maps[slice_index].drop_vars(water_maps.dims[0])
        undef_Mask: xr.DataArray = ( current_slice == 0 )
        current_patch_slice_index = slice_index - 1 if patch_slice_index is None else patch_slice_index - 1
        if (undef_Mask.count() == 0) or (current_patch_slice_index < 0): return current_slice
        patch_slice = water_maps[ current_patch_slice_index ].drop_vars(water_maps.dims[0])
        recolored_patch_slice = patch_slice.where( patch_slice == 0, patch_slice + 2  )
        current_patched_slice = current_slice.where( current_slice>0, recolored_patch_slice )
        return self.temporal_interpolate_slice( water_maps, slice_index, current_patched_slice, current_patch_slice_index )

    def temporal_interpolate( self, water_maps: xr.DataArray, nProcesses: int = 8  ) -> xr.DataArray:
        slices = list(range( water_maps.shape[0]))
        patcher = functools.partial( self.temporal_interpolate_slice, water_maps )
        with Pool(nProcesses) as p:
            patched_slices = p.map( patcher, slices, nProcesses)
            return self.time_merge( patched_slices, time=water_maps.coords[ water_maps.dims[0] ] )

    def time_merge( cls, data_arrays: List[xr.DataArray], **kwargs ) -> xr.DataArray:
        time_axis = kwargs.get('time',None)
        frame_indices = range( len(data_arrays) )
        merge_coord = pd.Index( frame_indices, name=kwargs.get("dim","time") ) if time_axis is None else time_axis
        result: xr.DataArray =  xr.concat( data_arrays, dim=merge_coord )
        return result

    def get_date_from_filename(self, filename: str):
        from datetime import datetime
        toks = filename.split("_")
        result = datetime.strptime(toks[1], '%Y%j').date()
        return np.datetime64(result)

    def get_mpw_data(self, opspec: Dict, **kwargs) -> xr.DataArray:
        cache = kwargs.get( "cache", True )
        download = kwargs.get('download', cache)

        data_dir = opspec.get('data_dir')
        lake_index = opspec.get('lake_index',0)
        lake_id = opspec.get('lake_id', f"lake-{lake_index}" )
        cropped_data_file = os.path.join(data_dir, f"/{lake_id}_cropped_data.nc")
        mask_value = opspec.get('mask_value',5)
        roi = opspec.get('roi', None)
        lake_mask: gpd.GeoSeries = gpd.read_file(roi) if roi else None

        if cache=="true" and os.path.isfile( cropped_data_file ):
            cropped_data_dataset: xr.Dataset = xr.open_dataset(cropped_data_file)
            cropped_data: xr.DataArray = cropped_data_dataset.cropped_data
        else:
            from geoproc.data.mwp import MWPDataManager
            from geoproc.xext.xrio import XRio
            data_url = opspec.get('data_url')
            product = opspec.get('product')

            year_range = opspec.get('year_range').split(",")
            day_range = opspec.get('day_range',"0,365").split(",")
            location = opspec.get('location')
            dataMgr = MWPDataManager(data_dir, data_url)

            dataMgr.setDefaults(product=product, download=download, years=range(int(year_range[0]),int(year_range[1])), start_day=int(day_range[0]), end_day=int(day_range[1]))
            file_paths = dataMgr.get_tile(location)
            time_values = np.array([ self.get_date_from_filename(os.path.basename(path)) for path in file_paths], dtype='datetime64[ns]')
            cropped_data: xr.DataArray = XRio.load(file_paths, mask=lake_mask, band=0, mask_value=mask_value, index=time_values)
            if cache in ["true","update"]:
                cropped_data_dset = xr.Dataset(dict(cropped_data=sanitize(cropped_data)))
                cropped_data_dset.to_netcdf(cropped_data_file)
                print(f"Cached cropped_data to {cropped_data_file}")

        cropped_data.assign_attrs( roi = lake_mask )
        return cropped_data

    def get_patched_water_maps(self, opspec: Dict, **kwargs) -> xr.DataArray:
        data_dir = opspec.get('data_dir')
        lake_index = opspec.get('lake_index', 0)
        lake_id = opspec.get('lake_id', f"lake-{lake_index}")
        data_file = f"{data_dir}/{lake_id}_patched_water_masks.nc"
        cache = kwargs.get("cache", "true" )
        if cache=="true" and os.path.isfile(data_file):
            repatched_water_maps: xr.DataArray = xr.open_dataset(data_file).water_masks
            repatched_water_maps.attrs['cmap'] = dict(colors=self.get_water_map_colors())
        else:
            water_masks: xr.DataArray = self.get_mpw_data(opspec)
            repatched_water_maps = self.patch_water_maps( water_masks, opspec, **kwargs )

        return repatched_water_maps

    def patch_water_maps( self, water_maps: xr.DataArray, opspec: Dict, **kwargs ) -> xr.DataArray:
        cache = kwargs.get("cache", "true" )

        water_probability:  xr.DataArray = self.get_water_probability( water_maps, opspec, **kwargs )
        persistent_classes: xr.DataArray = self.get_persistent_classes( water_probability, opspec, **kwargs )
        patched_water_maps: xr.DataArray = self.interpolate( persistent_classes, water_maps )

        if cache:
            data_dir = opspec.get('data_dir')
            lake_index = opspec.get('lake_index', 0)
            lake_id = opspec.get('lake_id', f"lake-{lake_index}")
            result_file = f"{data_dir}/{lake_id}_patched_water_masks.nc"
            sanitize(patched_water_maps).to_netcdf( result_file )

        patched_water_maps.assign_attrs( **water_maps.attrs )
        patched_water_maps.attrs['cmap'] = dict(colors=self.get_water_map_colors())
        return patched_water_maps



if __name__ == '__main__':
    from geoproc.plot.animation import SliceAnimation
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"

    opspec = dict(
        roi="/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp",
        data_url= "https://floodmap.modaps.eosdis.nasa.gov/Products",
        location = "120W050N",
        product =  "2D2OT",
        data_dir = DATA_DIR,
        land_water_thresholds="0.03,0.95",
        lake_index = "19",
        lake_masks_dir = f"{DATA_DIR}/MOD44W",
        lake_masks_nodata = '256',
        year_range = "2018, 2020"
    )

    waterMapGenerator = WaterMapGenerator()

    patched_water_maps = waterMapGenerator.get_patched_water_maps( opspec, cache="update" )
    roi = patched_water_maps.attrs["roi"].boundary

    animation = SliceAnimation( patched_water_maps, overlays=dict(red=roi) )
    animation.show()