import xarray as xa
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Union, Tuple, Optional
import os, math


iband = 200
nodata_value = -9999
input_file = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris/processed/ang20170713t030114_corr_v2p9.tif"
input_data: xa.DataArray = xa.open_rasterio( input_file )

print( input_data.shape )
print( input_data.dims )

band: xa.DataArray = input_data.isel(band=iband)
band: xa.DataArray = band.where(band != nodata_value)

print( band.shape )
print( band.dims )
print( band.count().data )

# band.plot.imshow()
# plt.show()