import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
import os, time, sys
import xarray as xr
from glob import glob
from collections import OrderedDict as odict
from geoproc.surfaceMapping.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager
from geoproc.xext.xrio import XRio
from geoproc.xext.xplot import XPlot
import os

colors4 = odict( nodata=(0.2, 0.0, 0.0), land=(0, 1, 0), pwater=(0, 0, 1), flood=(1, 1, 0) )
SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
savePath = DATA_DIR + "/LakeMap_counts_diagnostic_animation.gif"
location: str = locations[0]
product: str = products[1]
year = 2019
download = True
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
threshold = 0.5
binSize = 8
matchSliceIndex = 0
resolution = (250,250)
time_range = [0,365] # [200,216] #
view_data = False
subset = None
animate = True
plot_dem = True

lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

dataMgr = MWPDataManager(DATA_DIR, dat_url)
dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
file_paths = dataMgr.get_tile(location)

dem_arrays: List[xr.DataArray] = dataMgr.get_array_data( glob( DEMs ) )
dem_array: xr.DataArray = dem_arrays[0]
xc=dem_array.coords['x']
yc=dem_array.coords['y']

waterMapGenerator = WaterMapGenerator()
cropped_data: xr.DataArray = XRio.load( file_paths, mask = lake_mask, band=0 )

if view_data:
 #   dem_array.plot.imshow( )
    cropped_data.xplot.animate( overlays=dict(red=lake_mask.boundary), colors=colors4 )

else:

    masking_results = waterMapGenerator.get_water_masks( cropped_data, binSize, threshold )
    water_masks: xr.DataArray = masking_results["mask"]

    match_score, match_count, mismatch_count, overlap_maps = waterMapGenerator.get_slice_match_scores( water_masks, matchSliceIndex )

    overlap_maps.xplot.animate( overlays=dict(red=lake_mask.boundary), colors=colors4, metrics=dict( blue=match_score, green=match_count, red=mismatch_count ) )

