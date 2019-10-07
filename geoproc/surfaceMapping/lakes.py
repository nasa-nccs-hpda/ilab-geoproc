import xarray as xr
from  xarray.core.groupby import DatasetGroupBy
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from matplotlib.figure import Figure
from typing import Dict, List
import os, time, sys, wget

def download_MWP_files( data_dir: str, year: int = 2019, start_day: int = 1, end_day: int = 365, location: str = "120W050N", product: str = "1D1OS", download = False ):
    t0 = time.time()
    print("\n Executing download_MWP_files " )
    files = []
    for iFile in range(start_day,end_day+1):
        target_file = f"MWP_{year}{iFile}_{location}_{product}.tif"
        target_file_path = os.path.join( data_dir, target_file )
        if not os.path.exists( target_file_path ):
            if download:
                target_url = f"https://floodmap.modaps.eosdis.nasa.gov/Products/{location}/{year}/{target_file}"
                try:
                    wget.download( target_url, target_file_path )
                    print(f"Downloading url {target_url} to file {target_file_path}")
                    files.append( target_file_path )
                except Exception:
                    print( f"     ---> Can't access {target_url}")
        else:
            files.append( target_file_path )
    print( f" Completed download_MWP_files  in {time.time()-t0:.3f} seconds" )
    return files

def create_file_animation( files: List[str], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
    data_arrays: List[xr.DataArray] = [ xr.open_rasterio(file)[0] for file in files ]
    return create_animation( data_arrays, savePath, overwrite )

def create_array_animation( data_array: xr.DataArray, savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
    data_arrays: List[xr.DataArray] = [  data_array[iT] for iT in range(data_array.shape[0]) ]
    return create_animation( data_arrays, savePath, overwrite )

def create_animation( data_arrays: List[xr.DataArray], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
    images = []
    t0 = time.time()
    print("\n Executing create_array_animation ")
    figure: Figure = plt.figure()

    for da in data_arrays:
        im = plt.imshow(da.values, animated=True)
        images.append([im])
    anim = animation.ArtistAnimation( figure, images, interval=50, blit=True, repeat_delay=1000)
    if savePath is not None and ( overwrite or not os.path.exists( savePath )):
        anim.save( savePath, fps=2 )
        print( f" Animation saved to {savePath}" )
    else:
        print( f" Animation file already exists at '{savePath}'', set 'overwrite = True'' if you wish to overwrite it." )
    print(f" Completed create_array_animation in {time.time()-t0:.3f} seconds" )
    plt.show()
    return anim

def get_nearest_nonzero_value( array: np.ndarray, index: int )-> np.ndarray:
    return array

# def __get_water_mask1( da: xr.DataArray, threshold = 0.4 )-> xr.DataArray:
#     bin_counts = np.apply_along_axis( np.bincount, axis=0, arr=da.values, minlength=4 )
#     nonzero_counts = np.sum( bin_counts[1:], 0 )
#     bin_freq = np.divide( bin_counts, nonzero_counts, where= nonzero_counts != 0  )
#     prob_h20 = bin_freq[2] + bin_freq[3]
#     water_mask = prob_h20 >= threshold
#     result = xr.DataArray( water_mask, coords = { d:da.coords[d] for d in da.dims[1:] }, dims = da.dims[1:] )
#     return result

def __get_water_mask( da: xr.DataArray, threshold = 0.4 )-> xr.DataArray:
    land = ( da == 1 ).sum( axis=0 )
    perm_water = ( da == 2 ).sum( axis=0 )
    fld_water = ( da == 3 ).sum( axis=0 )
    water = (perm_water + fld_water)
    visible = ( water + land )
    prob_h20 = water / visible
    water_mask = prob_h20 >= threshold
    result =  water_mask*2 + ( visible > 0 )
    return result

def get_water_masks(data_array: xr.DataArray, binSize ) -> xr.DataArray:
    print("\n Executing get_water_masks ")
    t0 = time.time()
    time_bins = list( range( 0, data_array.shape[0]+1, binSize ) )
    grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins )
    result = grouped_data.apply( __get_water_mask, threshold = 0.5 )
    print( f" Completed get_water_masks in {time.time()-t0:.3f} seconds" )
    return result

def createDataset( files: List[str], band=0, subset = None ) ->  xr.DataArray:
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