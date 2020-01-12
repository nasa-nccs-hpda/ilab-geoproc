from typing import Dict, List, Tuple, Union
from geoproc.xext.xgeo import XGeo
from glob import glob
import xarray as xr
import matplotlib.pyplot as plt

product = "1D1OS"
band = -1
region = None
files = glob( f'/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/100W040N/MWP_*_100W040N_{product}.tif' )

data_arrays: List[xr.DataArray ] =  XGeo.loadRasterFiles(files, band=band, region=region )

data_arrays[100].plot.imshow(cmap="jet")
plt.tight_layout()
plt.show()