import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
from geoproc.util.configuration import ConfigurableObject, Region
from matplotlib.colors import LinearSegmentedColormap, Normalize
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import *
from PIL import Image
from typing import Dict, List, Tuple, Union
import os, time, sys
import xarray as xr
from geoproc.surfaceMapping.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager
from osgeo import gdal, gdalconst, ogr, osr
from geoproc.data.grid import GDALGrid
import os

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/shp/MEASURESLAKESSHAPES.shp"
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
time_range = [0, 365] # [200,216] #
#    subset = [500,100]
subset = None
anim_running = True

dataMgr = MWPDataManager(DATA_DIR, dat_url)
dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
file_paths = dataMgr.get_tile(location)

waterMapGenerator = WaterMapGenerator()
data_array: xr.DataArray = waterMapGenerator.createDataset(file_paths, subset=subset)
print(f" Data Array {data_array.name}: shape = {data_array.shape}, dims = {data_array.dims}")

waterMask = waterMapGenerator.get_water_masks(data_array, binSize, threshold, minH20)
print("waterMask.shape = " + str(waterMask.shape))

print("Downloaded tile data")
utm_sref: osr.SpatialReference = waterMask.xgeo.getUTMProj()
gdalWaterMask: GDALGrid = waterMask.xgeo.to_gdalGrid()
utmGdalWaterMask = gdalWaterMask.reproject(utm_sref, (250, 250))
utmWaterMask = utmGdalWaterMask.xarray("utmDataArray")
print( "Reprojected tile data")

gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
gdLakeShape: gpd.GeoDataFrame = shpManager.extractTile(gdFrame, location, 10)
geoPoly, geoRegions = shpManager.getRegion( gdLakeShape, "Lake_Name", LakeIndex )
geoBounds = geoPoly.envelope.bounds
utmLakeShape: gpd.GeoDataFrame = gdLakeShape.to_crs(crs=utm_sref.ExportToProj4())

utmPoly, utmRegions = shpManager.getRegion(utmLakeShape, "Lake_Name", LakeIndex, 2000 )
utmCroppedWaterMask: xr.DataArray = utmWaterMask.xgeo.crop_to_poly(utmPoly)
utmCroppedWaterMask.xgeo.to_gdalGrid()
utmCutoutWaterMask: xr.DataArray = shpManager.crop(utmCroppedWaterMask, utmRegions)

croppedWaterMask = waterMask.xgeo.crop( *geoBounds )

counts = utmCutoutWaterMask.xgeo.countInstances([2, 3])
norm = counts.max( dim="time" )
counts = counts/norm

t0 = time.time()
cm_colors = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)]
bar_colors = cm_colors[2:]
norm = Normalize(0, len(cm_colors))
cm = LinearSegmentedColormap.from_list("tmp-colormap", cm_colors, N=len(cm_colors))
fps =  1.0
roi: Region = None
print("\n Executing create_array_animation ")
data_arrays = [waterMask, croppedWaterMask, utmCutoutWaterMask]
numAnalysisPlots = 1
nFrames = data_arrays[0].shape[0]

def onClick(event):
    global anim_running
    if anim_running:
        anim.event_source.stop()
        anim_running = False
    else:
        anim.event_source.start()
        anim_running = True

figure, axes = plt.subplots( 2, 2 )
figure.suptitle( "Lake Mapping Analysis", fontsize=16)
figure.canvas.mpl_connect('button_press_event', onClick)
titles = [ "Raw Data", "Clipped to Lake", "UTM Projected and Masked" ]

images: List[AxesImage] = []
for iAxis in range(len(data_arrays)):
    axis = axes[ iAxis//2, iAxis%2 ]
    axis.title.set_text(titles[iAxis])
    image_data = data_arrays[iAxis][0]
    image: Image = axis.imshow(image_data, cmap=cm, norm=norm)
    axis.set_yticklabels([]); axis.set_xticklabels([])
    images.append(image)

bar_heights = counts[0]
axis = axes[1,1]
barplot = axis.bar( [0, 1], bar_heights.values, color = bar_colors )
axis.set_yticklabels([]); axis.set_xticklabels([])
axis.title.set_text("Normalized Class Counts")

def animate(frameIndex):
    frame_data = [ data_array[frameIndex] for data_array in data_arrays ]
    for data, image in zip( frame_data, images ):
        image.set_array( data )
    bar_heights = counts[frameIndex]
    for rect, y in zip( barplot, bar_heights ):
        rect.set_height(y)

anim = animation.FuncAnimation( figure, animate, frames=nFrames, interval=1000.0 / fps, blit=False)

if savePath is not None:
    anim.save(savePath, fps=fps)
    print(f" Animation saved to {savePath}")

plt.tight_layout()
plt.show()

