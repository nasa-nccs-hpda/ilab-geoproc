import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
import os, time, sys, json
import xarray as xr
import matplotlib.pyplot as plt
from glob import glob
from geoproc.data.mwp import MWPDataManager
from geoproc.plot.animation import SliceAnimation
from geoproc.data.shapefiles import ShapefileManager
from geoproc.util.configuration import sanitize, ConfigurableObject as BaseOp
from geoproc.xext.xrio import XRio
from geoproc.xext.xplot import XPlot
import os

mask_value = 5
colors3 = [ ( 0, 'land',  (0, 1, 0) ),
            ( 1, 'undetermined', (1, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ) ]

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
location: str = locations[0]
product: str = products[1]
year_range = ( 2014, 2020 )  # Data changes resolution at the beginning of 2014
download = True
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
threshold = 0.5
binSize = 8
matchSliceIndex = 17
resolution = (250,250)
time_range = [0,40]
view_data = False
subset = None
animate = True
plot_dem = True
land_water_thresholds = [ 0.25, 0.75 ]

t0 = time.time()

lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )
water_prob_maps = []
water_prob_classes = []

def get_water_prob( cropped_data ):
    perm_water = (cropped_data == 2)
    fld_water = (cropped_data == 3)
    water = (perm_water + fld_water)
    land = (cropped_data == 1)
    masked = cropped_data[0] == mask_value

    water_cnts = water.sum(axis=0)
    land_cnts = land.sum(axis=0)

    visible_cnts = (water_cnts + land_cnts + 1)
    water_prob: xr.DataArray = xr.where(masked, 1.01, water_cnts / visible_cnts)
    water_prob.attrs = cropped_data.attrs
    water_prob.name = "WaterProbability"
    return water_prob

with xr.set_options(keep_attrs=True):


    dataMgr = MWPDataManager(DATA_DIR, dat_url)
    dataMgr.setDefaults(product=product, download=download, year=range(*year_range), start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)
    cropped_data: xr.DataArray = XRio.load( file_paths, mask = lake_mask, band=0, mask_value=mask_value ) # , chunks={'x': 600, 'y': 600} )

    print(f" cropped_data dtype={cropped_data.dtype} ")
    print(f" cropped_data attrs={cropped_data.attrs} ")

    print( f"\n Computing water probability map for year range {year_range}\n" )

    water_prob = get_water_prob( cropped_data )

    print( f" water_prob dtype={water_prob.dtype} " )
    print(f" water_prob attrs={water_prob.attrs} ")



 #    thresholded_map: xr.DataArray = xr.where(  masked, mask_value, xr.where( water_prob > land_water_thresholds[1], 2, (water_prob > land_water_thresholds[0]) ) )

#    water_prob_maps.append( water_prob )
#    water_prob_classes.append( thresholded_map )


#     water_prob_map: xr.DataArray = BaseOp.time_merge(water_prob_maps)
#     water_prob_map.name = "WaterProbablity"
#     water_prob_map.attrs['cmap'] = json.dumps( dict( cmap = "jet" ) )
#  #   water_prob_map.xgeo.to_tif( DATA_DIR + f"/WaterProbabilityMap.tif" )
#
#     water_prob_class = BaseOp.time_merge(water_prob_classes)
#     water_prob_class.name = "Classification"
#     water_prob_class.attrs['cmap'] = json.dumps( dict( colors = colors3 ) )
#  #   water_prob_class.xgeo.to_tif( DATA_DIR + f"/WaterProbabilityClasses.tif" )
#
#     print( f'Completed computation in {(time.time()-t0)/60.0} mins')
#
# #    animation = SliceAnimation( [water_prob_map,water_prob_class], overlays=dict(red=lake_mask.boundary) )
# #    animation.show()
#

    result = xr.Dataset( dict( probabilitiy=water_prob ) )
    result_file = DATA_DIR + f"/WaterProbabilityMaps.nc"
    result.to_netcdf( result_file )
    print( f"Saved result to {result_file}")
