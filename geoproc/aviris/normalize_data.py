import xarray as xa
from typing import List, Union, Tuple
import matplotlib.pyplot as plt
import os

def normalize( input_bands: xa.DataArray, name: str, center = None ) -> Tuple[xa.DataArray,xa.DataArray]:
    x0 = input_bands if center is None else input_bands - center
    scale = x0.std( dim=['x','y'] )
    band_data: xa.DataArray =  x0 / scale
    band_data.name = name
    return band_data.assign_coords( dict( x=input_bands.x, y=input_bands.y ) ), scale

def get_aviris_input( filepath: str ) -> xa.DataArray:
    raw_input_bands: xa.DataArray = xa.open_rasterio( filepath )
    nodata_value = int(raw_input_bands.attrs['data_ignore_value'])
    input_bands: xa.DataArray = raw_input_bands.where(raw_input_bands != nodata_value, float('nan') )
    return input_bands.assign_coords( dict(band=raw_input_bands.wavelength)).drop_vars(['wavelength'])


DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = os.path.join( DATA_DIR, "results" )
if not os.path.exists(outDir): os.makedirs( outDir )
aviris_tile = "ang20170714t213741"
input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rdn_v2p9", f"{aviris_tile}_rdn_v2p9_img" )

norm_band_data = True
norm_training_data = True

input_bands: xa.DataArray =  get_aviris_input( input_file )

if norm_band_data:
    print( "Reading and normalizing band data")
    mean: xa.DataArray  = input_bands.mean( dim=['x','y'])
    std: xa.DataArray  = (input_bands/mean).std( dim=['x','y'] )
    band_data, scale  = normalize( input_bands, "band_data", mean )
    outFile = os.path.join( outDir, f"{aviris_tile}_rdn_v2p9.nc" )
    print( f"Writing feature data to {outFile}")
    dset = xa.Dataset( { "center": mean,  "range": std, "band_data": band_data, "scale": scale } )
    dset.to_netcdf( outFile )

if norm_training_data:
    print( "Reading and normalizing training data")
    nodata_value = int(input_bands.attrs['data_ignore_value'])
    target_file = os.path.join( DATA_DIR, f"{aviris_tile}_Avg-Chl.tif")
    raw_target_band: xa.DataArray = xa.open_rasterio( target_file )
    target_band: xa.DataArray = raw_target_band.where(raw_target_band != nodata_value, float('nan'))
    band_data, scale = normalize( target_band, "band_data" )
    outFile = os.path.join( outDir, f"{aviris_tile}_Avg-Chl.nc" )
    print( f"Writing training data to {outFile}")
    dset = xa.Dataset( { "band_data": band_data, "scale": scale } )
    dset.to_netcdf( outFile )

