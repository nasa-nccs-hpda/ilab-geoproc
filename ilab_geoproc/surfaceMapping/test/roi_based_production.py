from typing import List, Union, Tuple, Dict, Optional
from glob import glob
from geoproc.surfaceMapping.lakeExtentMapping import WaterMapGenerator
import os, time, collections

import yaml
lake_name = "MultiTileLake" # "SingleTileLake" # ""MosulDamLake"  # "MultiTileLake"
CURDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = '/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Birkett'
opspec_file = os.path.join(CURDIR, "specs", "test_multi_tile.yml")
with open(opspec_file) as f:
    opspecs = yaml.load( f, Loader=yaml.FullLoader )
    waterMapGenerator = WaterMapGenerator(opspecs)
    waterMapGenerator.view_water_map_results( lake_name )
