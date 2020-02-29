import xarray as xa
import numpy as np
from typing import List, Union, Tuple
import os

def normalize( input_bands: xa.DataArray, name: str, method: str, uniform = False ) -> Tuple[xa.DataArray,xa.DataArray]:
    axes = {} if uniform else dict( dim=['x','y'] )
    scale = input_bands.std( **axes ) if method == "std" else np.abs(input_bands).mean( **axes )
    band_data: xa.DataArray =  input_bands / scale
    band_data.name = name
    return band_data.assign_coords( dict( x=input_bands.x, y=input_bands.y ) ), scale

def get_aviris_input( filepath: str, nbands: int ) -> xa.DataArray:
    full_input_bands: xa.DataArray = xa.open_rasterio( filepath )
    nodata_value = int(full_input_bands.attrs['data_ignore_value'])
    raw_input_bands = full_input_bands[0:nbands,:,:]
    input_bands: xa.DataArray = raw_input_bands.where(raw_input_bands != nodata_value, float('nan') )
    return input_bands.assign_coords( dict(band=raw_input_bands.wavelength)).drop_vars(['wavelength'])


DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9_img" )

norm_band_data = True
norm_training_data = True
n_input_bands = 106
version = "R2"
norm_method = "mean"
uniform = True
input_bands: xa.DataArray =  get_aviris_input( input_file, n_input_bands )

if norm_band_data:

    print( "Reading and normalizing band data")
    band_data, scale =  normalize( input_bands, "band_data", norm_method, uniform )
    outFile = os.path.join( outDir, f"{aviris_tile}_corr_v2p9_{version}_{n_input_bands}.nc" )
    print( f"Writing feature data to {outFile}")
    dset = xa.Dataset( { "band_data": band_data,  "scale": scale } )
    dset.to_netcdf( outFile )

if norm_training_data:
    print( "Reading and normalizing training data")
    nodata_value = int(input_bands.attrs['data_ignore_value'])
    target_file = os.path.join( DATA_DIR, f"{aviris_tile}_Avg-Chl.tif")
    raw_target_band: xa.DataArray = xa.open_rasterio( target_file )
    target_band: xa.DataArray = raw_target_band.where(raw_target_band != nodata_value, float('nan'))
    band_data, scale = normalize( target_band, "band_data", norm_method, uniform )
    outFile = os.path.join( outDir, f"{aviris_tile}_Avg-Chl_{version}.nc" )
    print( f"Writing training data to {outFile}")
    dset = xa.Dataset( { "band_data": band_data, "scale": scale } )
    dset.to_netcdf( outFile )

