import xarray as xr
from  xarray.core.groupby import DatasetGroupBy
import numpy as np
from geoproc.util.configuration import ConfigurableObject
from typing import Dict, List, Union
import os, time, sys, wget

class WaterMapGenerator(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def get_water_mask(self, inputs: Union[ xr.DataArray, List[xr.DataArray] ], threshold = 0.5, min_fld = 1 )-> xr.DataArray:
        da: xr.DataArray = self.time_merge(inputs) if isinstance(inputs, list) else inputs
        land = ( da == 1 ).sum( axis=0 )
        perm_water = ( da == 2 ).sum( axis=0 )
        fld_water = ( da == 3 ).sum( axis=0 )
        water = (perm_water + fld_water)
        visible = ( water + land )
        prob_h20 = water / visible
#        water_mask = np.logical_and( prob_h20 >= threshold, fld_water >= min_fld )
        water_mask = prob_h20 >= threshold
        result =  water_mask*2 + ( visible > 0 )
        return result

    def get_water_masks(self, data_array: xr.DataArray, binSize: int, threshold = 0.5, min_fld = 1  ) -> xr.DataArray:
        print("\n Executing get_water_masks ")
        t0 = time.time()
        time_bins = list( range( 0, data_array.shape[0]+1, binSize ) )
        grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins )
        result: xr.DataArray = grouped_data.apply( self.get_water_mask, threshold = threshold, min_fld = min_fld )
        print( f" Completed get_water_masks in {time.time()-t0:.3f} seconds" )
        for key,value in data_array.attrs.items():
            if key not in result.attrs: result.attrs[key] = value
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
        merged_data_array: xr.DataArray = self.time_merge(data_arrays)
        print( f" Completed createDataset  in {time.time()-t0:.3f} seconds" )
        return merged_data_array

if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
    from geoproc.util.visualization import ArrayAnimation
    from geoproc.util.crs import CRS

    t0 = time.time()
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = locations[1]
    product: str = products[0]
    year = 2019
    download = False

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults(product=product, download=download, year=2019, start_day=1, end_day=365)
    file_paths = dataMgr.get_tile(location)

    waterMapGenerator = WaterMapGenerator()
    data_array: xr.DataArray = waterMapGenerator.createDataset( file_paths ) # , subset = [500,5] )
    print(f" Data Array {data_array.name}: shape = {data_array.shape}, dims = {data_array.dims}")

    waterMask = waterMapGenerator.get_water_masks( data_array, 8, 0.5, 2 )
    print( waterMask.shape )

    output_tiff =  "/tmp/test_watermask_geotiff.tif"
    input_array =  waterMask[0].astype(np.float)
    for key, value in waterMask.attrs.items():
        if key not in input_array.attrs: input_array.attrs[key] = value
    CRS.to_geotiff( input_array, output_tiff )
    print( f"Writing watermask output to {output_tiff}" )

    animator = ArrayAnimation()
    waterMaskAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_waterMask.gif')
    animator.create_array_animation( waterMask, waterMaskAnimationFile, overwrite = True )

    print( f"\n ** Done: total execution time = {time.time()-t0:.3f} seconds" )