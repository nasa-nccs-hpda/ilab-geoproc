import yaml
from typing import List, Union, Tuple, Dict, Optional
import xarray as xr
from glob import glob
from geoproc.surfaceMapping.lakeExtentMapping import WaterMapGenerator
import numpy as np
import os, time, collections

CURDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = '/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Birkett'
opspec_file = os.path.join(CURDIR, "specs", "lakes-test.yml")
with open(opspec_file) as f:
    opspecs = yaml.load(f, Loader=yaml.FullLoader)
    waterMapGenerator = WaterMapGenerator(opspecs)

    LakeId = "Lake334"
    outFile = f"{DATA_DIR}/{LakeId}_MODIS-NRT-250m-8d_v1.txt"
    waterMapGenerator.write_patched_water_maps( LakeId, outFile )