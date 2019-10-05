import xarray as xr
from  xarray.core.groupby import DatasetGroupBy
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from matplotlib.figure import Figure
import cartopy.crs as ccrs
import urllib.request
from typing import Dict, List
from urllib.error import HTTPError
import os, time, array, sys

def download_MWP_files( data_dir: str, year: int = 2019, start_day: int = 1, end_day: int = 365, location: str = "120W050N", product: str = "1D1OS", download = False ):
    t0 = time.time()
    print(" Executing download_MWP_files " )
    files = []
    for iFile in range(start_day,end_day+1):
        target_file = f"MWP_{year}{iFile}_{location}_{product}.tif"
        target_file_path = os.path.join( data_dir, target_file )
        if not os.path.exists( target_file_path ):
            if download:
                target_url = f"https://floodmap.modaps.eosdis.nasa.gov/Products/{location}/{year}/{target_file}"
                try:
                    urllib.request.urlretrieve( target_url, target_file_path )
                    print(f"Downloading url {target_url} to file {target_file_path}")
                    files.append(target_file)
                except HTTPError:
                    print( f"     ---> Can't access {target_url}")
        else:
            files.append( target_file_path )
    print( " Completed download_MWP_files in " + str( time.time() - t0 ) + " seconds")
    return files

def create_animation( files: List[str], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
    images = []
    t0 = time.time()
    print(" Executing create_animation ")
    figure: Figure = plt.figure()

    for file in files:
        da: xr.DataArray = xr.open_rasterio(file)
        im = plt.imshow(da[0].values, animated=True)
        images.append([im])
    anim = animation.ArtistAnimation( figure, images, interval=50, blit=True, repeat_delay=1000)
    if savePath is not None and ( overwrite or not os.path.exists( savePath )):
        anim.save( savePath )
        print( f"Animation saved to {savePath}" )
    print(" Completed create_animation in " + str(time.time() - t0) + " seconds")
    plt.show()
    return anim

def get_nearest_nonzero_value( array: np.ndarray, index: int )-> np.ndarray:
    return array

def get_water_mask( da: xr.DataArray, threshold = 0.4 )-> xr.DataArray:
    bin_counts = np.apply_along_axis( np.bincount, axis=0, arr=da.values, minlength=4 )
    nonzero_counts = np.sum( bin_counts[1:], 0 )
    bin_freq = np.divide( bin_counts, nonzero_counts, where= nonzero_counts != 0  )
    prob_h20 = bin_freq[2] + bin_freq[3]
    water_mask = prob_h20 >= threshold
    result = xr.DataArray( water_mask, coords = { d:da.coords[d] for d in da.dims[1:] }, dims = da.dims[1:] )
    return result

def get_water_masks(data_array: xr.DataArray, binSize ) -> xr.DataArray:
    print(" Executing get_water_masks ")
    t0 = time.time()
    time_bins = list( range( 0, data_array.shape[0]+1, binSize ) )
    grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins )
    result = grouped_data.apply( get_water_mask, threshold = 0.5 )
    print(" Completed get_water_masks in " + str(time.time() - t0) + " seconds")
    return result

def createDataset( files: List[str], band=0, subset = None ) ->  xr.DataArray:
    t0 = time.time()
    print(" Executing createDataset ")
    if subset is not None:
        offset = subset[0]
        size = subset[1]
        data_arrays: List[xr.DataArray ] = [ xr.open_rasterio(file)[band,offset:offset+size,offset:offset+size] for file in files ]
    else:
        data_arrays: List[xr.DataArray] = [xr.open_rasterio(file)[band] for file in files]
    merged_data_array: xr.DataArray = xr.concat( data_arrays, xr.DataArray( range(len(files)), name='time', dims="time" ) )
    print(" Completed createDataset in " + str(time.time() - t0) + " seconds")
    return merged_data_array


if __name__ == '__main__':

    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = "120W050N"
    product: str = "1D1OS"
    year = 2019
    viewRawData = False

    files = download_MWP_files( DATA_DIR, year, 1, 365, location, product )

    if viewRawData:
        animationFile =  os.path.join( DATA_DIR, f'MWP_{year}_{location}_{product}.gif' )
        create_animation( files, animationFile )

    data_array: xr.DataArray = createDataset( files )
    print(f" Data Array {data_array.name}: shape = {data_array.shape}, dims = {data_array.dims}")

    result = get_water_masks( data_array, 8 )
    print( result.shape )

    print(" ** done **")