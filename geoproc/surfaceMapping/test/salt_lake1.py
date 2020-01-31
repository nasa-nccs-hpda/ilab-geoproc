import geopandas as gpd
import pandas as pd
from shapely.geometry import *
from geoproc.plot.animation import SliceAnimation
from typing import List, Union, Tuple
from geoproc.data.mwp import MWPDataManager
from geoproc.xext.xrio import XRio
import xarray as xr
from glob import glob
import functools
from multiprocessing import Pool
from xarray.core.groupby import DatasetGroupBy
from geoproc.util.configuration import sanitize, ConfigurableObject
import matplotlib.pyplot as plt
from geoproc.surfaceMapping.lakeExtentMapping import WaterMapGenerator
import numpy as np
import os, time

mask_value = 5
mismatch_value = 6
mask_color = [0.25, 0.25, 0.25]
jet_colors2 = plt.cm.jet(np.linspace(0, 1, 128))
jet_colors2[127] = mask_color + [ 1.0 ]

colors3 = [ ( 0, 'undetermined', (1, 1, 0) ),
            ( 1, 'land',  (0, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ) ]

colors4 = [ ( 0, 'nodata', (0, 0, 0)),
            ( 1, 'land',   (0, 1, 0)),
            ( 2, 'water',  (0, 0, 1)),
            ( 3, 'interp land',   (0, 0.5, 0)),
            ( 4, 'interp water',  (0, 0, 0.5)),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ),
            ( mismatch_value, 'mismatches', (1, 1, 0) ) ]

debug = False
SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
savePath = DATA_DIR + "/LakeMap_counts_diagnostic_animation.gif"
location: str = locations[0]
product: str = products[1]
year_range = ( 2018, 2020 ) if debug else ( 2014, 2020 )
from geoproc.data.shapefiles import ShapefileManager
download = True
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
threshold = 0.5
binSize = 8

resolution = (250,250)
time_range = [0,40] if debug else [0,360]
land_water_thresholds = [ 0.08, 0.92 ]

use_existing_water_masks = True
use_existing_cropped_data = True
show_water_probability = False
use_existing_water_probability = False


SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

cropped_data_file = DATA_DIR + f"/SaltLake_cropped_data.nc"

opspec = {}

maskGenerator = WaterMapGenerator()

cropped_data: xr.DataArray = maskGenerator.getMPWData(opspec)

if show_water_probability is not None:

    yearly = True
    water_probability_file = DATA_DIR + (f"/SaltLake_yearly_water_probability.nc" if yearly else f"/SaltLake_water_probability.nc")

    if use_existing_water_probability:
        water_probability_dataset: xr.Dataset = xr.open_dataset(water_probability_file)
        water_probability: xr.DataArray = water_probability_dataset.water_probability
    else:
        water_probability = maskGenerator.get_water_prob(cropped_data, yearly)
        result = xr.Dataset(dict(water_probability=sanitize(water_probability)))
        result.to_netcdf(water_probability_file)
        print(f"Saved water_probability to {water_probability_file}")

    persistent_classes = maskGenerator.get_persistent_classes(water_probability, land_water_thresholds)
    persistent_classes.attrs['cmap'] = dict(colors=colors3)
    water_probability.attrs['cmap'] = dict(colors=jet_colors2)

    if show_water_probability:
        animation = SliceAnimation([water_probability, persistent_classes], overlays=dict(red=lake_mask.boundary))
        animation.show()

if use_existing_water_masks is not None:
    if use_existing_water_masks:
        result_file = DATA_DIR + f"/SaltLake_water_masks.nc"
        water_masks_dataset: xr.Dataset = xr.open_dataset(result_file)
        water_masks: xr.DataArray = water_masks_dataset.water_masks
    else:
        masking_results = maskGenerator.get_water_masks(cropped_data, binSize, threshold, mask_value)
        water_masks: xr.DataArray = masking_results["mask"]

        result = xr.Dataset(dict(water_masks=sanitize(water_masks)))
        result_file = DATA_DIR + f"/SaltLake_water_masks.nc"
        result.to_netcdf(result_file)
        print(f"Saved water_masks to {result_file}")