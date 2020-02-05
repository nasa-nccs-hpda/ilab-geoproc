import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
from geoproc.util.configuration import sanitize, ConfigurableObject as BaseOp
import os, time, sys, json
import matplotlib.pyplot as plt
from glob import glob
import numpy as np
from geoproc.plot.animation import SliceAnimation
import xarray as xr

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
yearly_water_mask = DATA_DIR + f"/SaltLakeWaterMasks.nc"

mask_value = 5
mask_color = [0.25, 0.25, 0.25]
jet_colors2 = plt.cm.jet(np.linspace(0, 1, 128))
jet_colors2[127] = mask_color + [ 1.0 ]

colors3 = [ ( 0, 'land',  (0, 1, 0) ),
            ( 1, 'undetermined', (1, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', mask_color ) ]

dataset = xr.open_dataset( result_file )