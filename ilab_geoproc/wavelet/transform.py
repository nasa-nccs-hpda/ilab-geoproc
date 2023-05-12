import numpy as np
import xarray as xr
import os
import matplotlib.pyplot as plt
from typing import List, Union, Tuple
from matplotlib.colors import LinearSegmentedColormap, Normalize
from geoproc.util.cip import CIP
import matplotlib.colors as colors
# from astropy.convolution import convolve
from scipy.signal import convolve
DATA_DIR = '/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Wavelet'
use_cache= True
scale = 0.3

def centered_norm( image: xr.DataArray, iattrs = None ) -> xr.DataArray:
    centered_image = image - image.mean()
    result = centered_image / centered_image.std()
    if iattrs: result.attrs.update( iattrs )
    return result

def norm( image: xr.DataArray ) -> xr.DataArray:
    return image / image.mean()

def get_input_array( collection, variable, index, **kwargs ) -> xr.DataArray:
    cache_file_name = os.path.join( DATA_DIR, f"{collection}.{variable}.{index}.nc")
    cache = kwargs.get( 'use_cache', True )
    if os.path.isfile( cache_file_name ) and cache:
        dataset = xr.open_dataset(cache_file_name)
        print( f"Reading cached array from {cache_file_name}")
        return dataset[ variable ]
    else:
        input_array: xr.DataArray = CIP.data_array( collection, variable )
        norm_array: xr.DataArray = input_array[index]
        norm_array.to_netcdf( cache_file_name )
        return norm_array

cubic_spline_mask = np.array( [ [ 1, 4, 6, 4, 1 ], [ 4, 16, 24, 16, 4 ], [ 6, 24, 36, 24, 6 ], [ 4, 16, 24, 16, 4 ], [ 1, 4, 6, 4, 1 ] ] ) / 256.0
input_array: xr.DataArray = get_input_array( "merra2", "tas", 0, use_cache=use_cache )
convolve_input = input_array.values
smoothed: np.ndarray = convolve( convolve_input, cubic_spline_mask, mode="same" )
wavelet_transform: np.ndarray =  convolve_input - smoothed
result = xr.DataArray( wavelet_transform, dims=input_array.dims, coords=input_array.coords )

#rnormalize = colors.LogNorm( vmin=0.001, vmax=1.0 )

rnormalize = Normalize( -scale, scale )
result.plot.imshow( cmap="jet", norm=rnormalize)
plt.show()


