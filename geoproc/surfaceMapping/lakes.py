import xarray as xr
from  xarray.core.groupby import DatasetGroupBy
import numpy as np
from geoproc.util.configuration import ConfigurableObject, Region
from typing import List, Union, Tuple
import os, time


class WaterMapGenerator(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def temporal_interpolate(self, water_masks: xr.DataArray, current_slice_index: int, **kwargs):
        overlap_class = kwargs.get('overlap_class',2)
        mismatch_weight = kwargs.get('mismatch_weight',2)
        mismatch_value = kwargs.get('overlap_class', 6)

        full_water_mask: xr.DataArray =  water_masks == overlap_class
        slice_water_mask = full_water_mask[current_slice_index]

        full_valid_mask: xr.DataArray =  water_masks > 0
        slice_valid_mask = full_valid_mask[current_slice_index]
        valid_area = np.logical_and( full_valid_mask, slice_valid_mask )

        matches = full_water_mask == slice_water_mask
        valid_matches = matches.where( valid_area, False )
        match_count = valid_matches.sum( dim=["x","y"])
        match_count.name = "Overlap"

        mismatches = np.logical_not( matches )
        valid_mismatches = mismatches.where(valid_area, False)
        mismatch_count = valid_mismatches.sum(dim=["x", "y"]) * mismatch_weight
        mismatch_count.name = "Mismatch"
        mismatch_count = mismatch_count.where( match_count > mismatch_count, match_count )
        overlap_maps = water_masks.where( np.logical_not(valid_mismatches), mismatch_value  )

        match_score: xr.DataArray = match_count - mismatch_count
        match_score.name = "Similarity"
        matching_slice = self.get_matching_slice( water_masks, match_score, current_slice_index )
        current_slice = water_masks[current_slice_index]
        interp_slice: xr.DataArray = current_slice.where( current_slice != 0, matching_slice + 2)
#        slices: List = [ water_masks[i] for i in range(water_masks.shape[0]) ]
        water_masks[ current_slice_index ] = interp_slice

        return dict( match_score=match_score, match_count=match_count, mismatch_count=mismatch_count, overlap_maps=overlap_maps,
                     matching_slice=matching_slice, interp_water_masks = water_masks )

    def get_matching_slice(self, water_masks: xr.DataArray, match_score: xr.DataArray, current_slice: int ):
        scores: np.ndarray = match_score.values.copy( )
        scores[ current_slice ] = 0
        matching_slice = water_masks[ scores.argmax() ]
        return matching_slice

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

    def createDataset(self,  files: List[str], band=-1, subset = None ) ->  xr.DataArray:
        from geoproc.xext.xgeo import XGeo
        t0 = time.time()
        print("\n Executing createDataset ")
        region = Region([subset[0],subset[0]], subset[1] ) if subset is not None else None
        data_arrays: List[xr.DataArray ] =  XGeo.loadRasterFiles(files, band=band, region=region )
        merged_data_array: xr.DataArray = self.time_merge(data_arrays)
        print( f" Completed createDataset  in {time.time()-t0:.3f} seconds" )
        return merged_data_array

if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
    from geoproc.util.visualization import ArrayAnimation

    t0 = time.time()
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "2D2OT", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    location: str = locations[0]
    product: str = products[1]
    year = 2014
    minH20 = 1
    threshold = 0.5
    download = True
    binSize = 8
    time_range = [ 1, 365 ]
    view_data = True
#    subset = [500,100]
    subset = None

    dataMgr = MWPDataManager( DATA_DIR, dat_url )
    dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)

    waterMapGenerator = WaterMapGenerator()
    data_array: xr.DataArray = waterMapGenerator.createDataset( file_paths, subset = subset )
    print(f" Data Array {data_array.name}: shape = {data_array.shape}, dims = {data_array.dims}")

    animator = ArrayAnimation()
    floodMapAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_floodMap-m{minH20}.gif')
    animator.create_array_animation( data_array, floodMapAnimationFile, overwrite = True, display = view_data )

    if not view_data:

        waterMask = waterMapGenerator.get_water_masks( data_array, binSize, threshold, minH20 )
        print( f"Water map variables: {waterMask.data_vars.keys()}")
        waterMaskArrays = list(waterMask.data_vars.values())

        animator = ArrayAnimation()
        waterMaskAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_waterMask-m{minH20}.gif')
        animator.create_array_animation( waterMaskArrays[0], waterMaskAnimationFile, overwrite = True, display = True )

        print( f"\n ** Done: total execution time = {time.time()-t0:.3f} seconds" )