from geoproc.plot.animation import SliceAnimation
from typing import List, Union, Tuple, Dict, Optional
import yaml, os, xarray as xa
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pandas as pd

data_dir= "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"

mask_value = 5
water_map_colors = dict( colors =
            [ (0, 'nodata', (0, 0, 0)),
              (1, 'land', (0, 1, 0)),
              (2, 'water', (0, 0, 1)),
              (3, 'int-land', (0, 0.6, 0)),
              (4, 'int-water', (0, 0, 0.6)),
              (mask_value, 'mask', (1, 1, 0.7)) ] )

water_maps_file = os.path.join( data_dir, "saltlakemasked_water_maps.nc")
water_prob_file = os.path.join( data_dir, "SaltLake_water_probability.nc")
SHAPEFILE = os.path.join( data_dir, "saltLake/GreatSalt.shp" )

water_maps: xa.DataArray = xa.open_dataset( water_maps_file ).water_maps
water_maps.name = "water_maps"
water_maps.attrs['cmap'] = water_map_colors

water_probability: xa.DataArray = xa.open_dataset( water_prob_file ).water_probability
permanent_water = np.logical_and( water_probability < 1.0, water_probability > 0.95 )
mismatches: xa.DataArray = water_maps.where( permanent_water, 0 ) == 1
mismatch_count = mismatches.sum( dim=["x","y"] )
plt.show()

lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )



animation = SliceAnimation( water_maps, overlays=dict(red=lake_mask.boundary), metrics=dict(blue=mismatch_count) )
animation.show()