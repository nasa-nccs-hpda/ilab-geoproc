import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
import os, time, sys
import xarray as xr
from glob import glob
from geoproc.surfaceMapping.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager
from geoproc.xext.xrio import XRio
from geoproc.xext.xplot import XPlot
import os

mask_value = 5
mismatch_value = 6
colors4 = [ ( 0, 'nodata', (0, 0, 0)),
            ( 1, 'land',   (0, 1, 0)),
            ( 2, 'water',  (0, 0, 1)),
            ( 3, 'interp land',   (0, 0.5, 0)),
            ( 4, 'interp water',  (0, 0, 0.5)),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ),
            ( mismatch_value, 'mismatches', (1, 1, 0) ) ]

colors3 = [ ( 0, 'nodata', (0, 0, 0)),
            ( 1, 'land',   (0, 1, 0)),
            ( 2, 'perm water',  (0, 0, 1)),
            ( 3, 'flood water', (0, 1, 1)),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ) ]

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
savePath = DATA_DIR + "/LakeMap_counts_diagnostic_animation.gif"
location: str = locations[0]
product: str = products[1]
years = [2019]
download = True
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
threshold = 0.5
binSize = 8
matchSliceIndex = 17
resolution = (250,250)
time_range = [0,360]
view_data = False
subset = None
animate = True
plot_dem = True

lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

dataMgr = MWPDataManager(DATA_DIR, dat_url)
dataMgr.setDefaults(product=product, download=download, years=years, start_day=time_range[0], end_day=time_range[1])
file_paths = dataMgr.get_tile(location)

dem_arrays: List[xr.DataArray] = dataMgr.get_array_data( glob( DEMs ) )
dem_array: xr.DataArray = dem_arrays[0]
xc=dem_array.coords['x']
yc=dem_array.coords['y']

waterMapGenerator = WaterMapGenerator()
cropped_data: xr.DataArray = XRio.load( file_paths, mask = lake_mask, band=0, mask_value=mask_value )

if view_data:
    cropped_data.xplot.animate( overlays=dict(red=lake_mask.boundary), colors=colors3 )

else:
    masking_results = waterMapGenerator.get_water_masks( cropped_data, binSize, threshold )
    water_masks: xr.DataArray = masking_results["mask"]
    ms = waterMapGenerator.temporal_interpolate(water_masks, matchSliceIndex)
    ms['interp_water_masks'].xplot.animate( overlays=dict(red=lake_mask.boundary),
                                            colors=colors4,
                                            metrics=dict( blue=ms['match_score'], green=ms['match_count'], red=ms['mismatch_count'], markers=dict( cyan=matchSliceIndex ) ),
                                            auxplot=ms['overlap_maps'] )

