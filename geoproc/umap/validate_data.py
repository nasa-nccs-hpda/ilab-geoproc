import xarray as xa
import numpy as np
from typing import List, Union, Tuple, Optional
import sys
import os, math

if len(sys.argv) < 3: print( "Usage: validate_data <data_location> <tile_id>")

DATA_DIR = sys.argv[1]   # "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris/processed/"
aviris_tile = sys.argv[2]   # "ang20170701t182520"
nodata_value = -9999

input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9.tif" )
input_data: xa.DataArray = xa.open_rasterio( input_file )

for ib in range(1,400,10):
    band: xa.DataArray= input_data.isel( band = ib )
    band: xa.DataArray = band.where( band != nodata_value )
    print( f" {ib}: {band.count().data}" )
