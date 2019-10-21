import xarray as xr
from  xarray.core.groupby import DatasetGroupBy
import numpy as np
from geoproc.util.configuration import ConfigurableObject, Region
from typing import List, Union
import os, time


class WaterMapGenerator(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def get_water_mask(self, inputs: Union[ xr.DataArray, List[xr.DataArray] ], threshold = 0.5, min_h20 = 1 )-> xr.DataArray:
        da: xr.DataArray = self.time_merge(inputs) if isinstance(inputs, list) else inputs
        land = ( da == 1 ).sum( axis=0 )
        perm_water = ( da == 2 ).sum( axis=0 )
        fld_water = ( da == 3 ).sum( axis=0 )
        water = (perm_water + fld_water)
        visible = ( water + land )
        prob_h20 = water / visible
        water_mask = np.logical_and( prob_h20 >= threshold, fld_water >= min_h20 )
        result =  xr.where( perm_water > 0, 3, xr.where( water_mask, 2, xr.where( land > 0, 1, 0 ) ) )
        return result

    def get_water_masks(self, data_array: xr.DataArray, binSize: int, threshold = 0.5, min_h20 = 1  ) -> xr.DataArray:
        print("\n Executing get_water_masks ")
        t0 = time.time()
        time_bins = np.array( range( 0, data_array.shape[0]+1, binSize ) )
        grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins )
        result: xr.DataArray = grouped_data.apply( self.get_water_mask, threshold = threshold, min_h20 = min_h20 )
        print( f" Completed get_water_masks in {time.time()-t0:.3f} seconds" )
        self.transferMetadata( data_array, result )
        return result

    def createDataset(self,  files: List[str], band=0, subset = None ) ->  xr.DataArray:
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
    product: str = products[2]
    year = 2019
    minH20 = 2
    threshold = 0.5
    download = True
    binSize = 8
    time_range = [ 1, 365 ]
#    subset = [500,100]
    subset = None

    dataMgr = MWPDataManager(DATA_DIR, dat_url )
    dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)

    waterMapGenerator = WaterMapGenerator()
    data_array: xr.DataArray = waterMapGenerator.createDataset( file_paths, subset = subset )
    print(f" Data Array {data_array.name}: shape = {data_array.shape}, dims = {data_array.dims}")

    waterMask = waterMapGenerator.get_water_masks( data_array, binSize, threshold, minH20 )
    print( waterMask.shape )

    animator = ArrayAnimation()
    waterMaskAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_waterMask-m{minH20}.gif')
    animator.create_array_animation( waterMask, waterMaskAnimationFile, overwrite = True )

    print( f"\n ** Done: total execution time = {time.time()-t0:.3f} seconds" )