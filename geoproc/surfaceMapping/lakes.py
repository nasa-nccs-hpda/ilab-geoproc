import xarray as xr
from  xarray.core.groupby import DatasetGroupBy
import numpy as np
from geoproc.util.configuration import ConfigurableObject
from typing import Dict, List
import os, time, sys, wget

class WaterMapGenerator(ConfigurableObject):

    def __init__(self, data_dir: str, data_source_url: str, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        self.data_dir = data_dir
        self.data_source_url = data_source_url

    def __get_water_mask(self,  da: xr.DataArray, threshold = 0.4 )-> xr.DataArray:
        land = ( da == 1 ).sum( axis=0 )
        perm_water = ( da == 2 ).sum( axis=0 )
        fld_water = ( da == 3 ).sum( axis=0 )
        water = (perm_water + fld_water)
        visible = ( water + land )
        prob_h20 = water / visible
        water_mask = prob_h20 >= threshold
        result =  water_mask*2 + ( visible > 0 )
        return result

    def get_water_masks(self, data_array: xr.DataArray, binSize ) -> xr.DataArray:
        print("\n Executing get_water_masks ")
        t0 = time.time()
        time_bins = list( range( 0, data_array.shape[0]+1, binSize ) )
        grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins )
        result = grouped_data.apply( self.__get_water_mask, threshold = 0.5 )
        print( f" Completed get_water_masks in {time.time()-t0:.3f} seconds" )
        return result

    def createDataset(self,  files: List[str], band=0, subset = None ) ->  xr.DataArray:
        t0 = time.time()
        print("\n Executing createDataset ")
        if subset is not None:
            offset = subset[0]
            size = subset[1]
            data_arrays: List[xr.DataArray ] = [ xr.open_rasterio(file)[band,offset:offset+size,offset:offset+size] for file in files ]
        else:
            data_arrays: List[xr.DataArray] = [xr.open_rasterio(file)[band] for file in files]
        merged_data_array: xr.DataArray = xr.concat( data_arrays, xr.DataArray( range(len(files)), name='time', dims="time" ) )
        print( f" Completed createDataset  in {time.time()-t0:.3f} seconds" )
        return merged_data_array

if __name__ == '__main__':
    t0 = time.time()
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = locations[1]
    product: str = products[1]
    year = 2019
    viewRawData = True

    file_paths = download_MWP_files( DATA_DIR, year, 1, 365, location, product )

    if viewRawData:
        animationFile =  os.path.join( DATA_DIR, f'MWP_{year}_{location}_{product}.gif' )
        create_file_animation( file_paths, animationFile )

    data_array: xr.DataArray = createDataset( file_paths ) # , subset = [500,5] )
    print(f" Data Array {data_array.name}: shape = {data_array.shape}, dims = {data_array.dims}")

    waterMask = get_water_masks( data_array, 8 )
    print( waterMask.shape )

    waterMaskAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_waterMask.gif')
    create_array_animation( waterMask, waterMaskAnimationFile )

    print( f"\n ** Done: total execution time = {time.time()-t0:.3f} seconds" )