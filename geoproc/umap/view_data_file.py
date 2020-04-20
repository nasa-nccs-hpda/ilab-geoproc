import xarray as xa
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Union, Tuple, Optional
import os, math

iband = 200
nodata_value = -9999
input_file = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris/processed/ang20170720t004130_corr_v2p9.tif"
input_data: xa.DataArray = xa.open_rasterio( input_file )
print( input_data.shape )

band: xa.DataArray = input_data[iband,0:2000,0:2000]
print( band.shape )
print( band.dims )

band.plot.imshow(cmap="jet", vmin=0, vmax=10)
plt.show()