import xarray as xa
import numpy as np
from typing import List, Union, Tuple, Optional
import os, math
from geoproc.plot.animation import SliceAnimation

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris/processed/"
aviris_tile = "ang20170701t182520"

input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9.tif" )

input_data: xa.DataArray = xa.open_rasterio( input_file )

anim = SliceAnimation( input_data )

anim.show()
