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

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
result_file = DATA_DIR + f"/WaterProbabilityMaps.nc"
lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )
land_water_thresholds = [ 0.05, 0.85 ]

mask_value = 5
mask_color = [0.25, 0.25, 0.25]
jet_colors2 = plt.cm.jet(np.linspace(0, 1, 128))
jet_colors2[127] = mask_color + [ 1.0 ]

colors3 = [ ( 0, 'land',  (0, 1, 0) ),
            ( 1, 'undetermined', (1, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', mask_color ) ]

dataset = xr.open_dataset( result_file )
water_prob = dataset['probabilitiy']
masked = water_prob > 1.0

thresholded_map: xr.DataArray = xr.where(  masked, mask_value, xr.where( water_prob > land_water_thresholds[1], 2, (water_prob > land_water_thresholds[0]) ) )
thresholded_map.attrs['cmap'] = dict( colors = colors3 )

water_prob.attrs['cmap'] = dict( colors = jet_colors2 )

#water_prob_class = dataset['classification']
#water_prob_class.attrs['cmap'] = dict( colors = colors3 )

#water_prob_map.attrs['cmap'] = dict( cmap = "jet" )

animation = SliceAnimation( [ water_prob, thresholded_map ], overlays=dict(red=lake_mask.boundary) )
animation.show()

# prob_file = DATA_DIR + f"/WaterProbabilityMap.tif"
# water_prob_map: xr.DataArray = xr.open_rasterio( prob_file )
#
# class_file = DATA_DIR + f"/WaterProbabilityClasses.tif"
# water_prob_class: xr.DataArray = xr.open_rasterio( class_file )
#
#



# # sample the colormaps that you want to use. Use 128 from each so we get 256
# # colors in total
#
# # combine them and build a new colormap
# colors = np.vstack((colors1, colors2))
# mymap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors)