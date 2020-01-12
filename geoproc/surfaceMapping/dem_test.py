import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
from geoproc.util.configuration import ConfigurableObject, Region
from matplotlib.colors import LinearSegmentedColormap, Normalize
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely.geometry import *
from PIL import Image
from typing import Dict, List, Tuple, Union
import os, time, sys
import xarray as xr
import numpy as np
from glob import glob
from geoproc.surfaceMapping.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager
from geoproc.util.visualization import ArrayAnimation
import os

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/shp/MEASURESLAKESSHAPES.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
savePath = DATA_DIR + "/LakeMap_counts_diagnostic_animation.gif"
location: str = locations[0]
product: str = products[0]
year = 2019
download = False
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
minH20 = 2
threshold = 0.5
binSize = 8
LakeIndex = 6
resolution = (250,250)
time_range = [0,360] # [200,216] #
#    subset = [500,100]
subset = None
anim_running = True
plot_dem = True

dataMgr = MWPDataManager(DATA_DIR, dat_url)
dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
file_paths = dataMgr.get_tile(location)

dem_arrays: List[xr.DataArray] = dataMgr.get_array_data( glob( DEMs ) )
xc=dem_arrays[0].coords['x']
yc=dem_arrays[0].coords['y']

dem_array: xr.DataArray = dem_arrays[0]
#dem_array.plot.imshow( cmap="jet", vmin = 1280, vmax = 1285 )
#plt.show()

waterMapGenerator = WaterMapGenerator()
data_array: xr.Dataset = waterMapGenerator.createDataset(file_paths)
cropped_data = data_array.xgeo.crop( xc[0], yc[-1], xc[-1], yc[0] )

masking_results = waterMapGenerator.get_water_masks(cropped_data, binSize, threshold, minH20)
# utmWaterMask = masking_results["mask"].xgeo.to_utm( (250,250) )
water_mask = masking_results["mask"]

#animator = ArrayAnimation()
#waterMaskAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_waterMask-m{minH20}.gif')
#animator.create_array_animation( water_mask, waterMaskAnimationFile, overwrite=True )

overlaid_dem_array = xr.where( water_mask[0] == 1, dem_array, water_mask[0] )

overlaid_dem_array.plot.imshow( cmap="jet", vmin=0,  vmax = 1300 )
plt.show()


# gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
# gdLakeShape: gpd.GeoDataFrame = shpManager.extractTile( gdFrame, location, 10 )
# geoPoly, geoRegions = shpManager.getRegion( gdLakeShape, "Lake_Name", LakeIndex )
# geoBounds = geoPoly.envelope.bounds
# utmLakeShape: gpd.GeoDataFrame = gdLakeShape.to_crs( crs=utm_sref.ExportToProj4() )
#
# utmPoly, utmRegions = shpManager.getRegion(utmLakeShape, "Lake_Name", LakeIndex, 2000 )
# utmCroppedWaterMask: xr.DataArray = utmWaterMask.xgeo.crop_to_poly(utmPoly)
# utmCutoutWaterMask: xr.DataArray = shpManager.crop(utmCroppedWaterMask, utmRegions)
# utmCroppedReliability: xr.DataArray = utmReliability.xgeo.crop_to_poly(utmPoly)
# utmCutoutReliability: xr.DataArray = shpManager.crop(utmCroppedReliability, utmRegions)
#
# print( str(utmPoly.bounds) )
# print( str(utm_dem_array.coords ) )
# utmCroppedDEM: xr.DataArray = utm_dem_array.xgeo.crop_to_poly(utmPoly)
#
# if plot_dem:
#     utmCroppedDEM.plot.imshow( cmap="jet", vmin = 1000, vmax = 3000 )
#     plt.tight_layout()
#     plt.show()
#
#
