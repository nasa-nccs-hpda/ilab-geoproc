import matplotlib.animation as animation
from matplotlib.image import AxesImage
from geoproc.util.configuration import Region
from matplotlib.colors import LinearSegmentedColormap, Normalize
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely.geometry import *
from PIL import Image
from typing import List
import time
import xarray as xr
from geoproc.surfaceMapping.dev.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager
from osgeo import osr
from geoproc.data.grid import GDALGrid

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

masking_results: xr.Dataset = waterMapGenerator.get_water_masks(data_array, binSize, threshold, minH20)
waterMask = masking_results["mask"]
reliability = masking_results["reliability"]
print("waterMask.shape = " + str(waterMask.shape))

print("Downloaded tile data")
utm_sref: osr.SpatialReference = waterMask.xgeo.getUTMProj()
gdalWaterMask: GDALGrid = waterMask.xgeo.to_gdalGrid()
utmGdalWaterMask = gdalWaterMask.reproject(utm_sref, resolution=(250, 250))
utmWaterMask = utmGdalWaterMask.xarray("utmWaterMask")

gdalReliability: GDALGrid = reliability.xgeo.to_gdalGrid()
reliabilityMap = gdalReliability.reproject(utm_sref, resolution=(250, 250))
utmReliability = reliabilityMap.xarray("utmReliability")

print( "Reprojected tile data")

gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
gdLakeShape: gpd.GeoDataFrame = shpManager.extractTile(gdFrame, location, 10)
geoPoly, geoRegions = shpManager.getRegion( gdLakeShape, "Lake_Name", LakeIndex )
geoBounds = geoPoly.envelope.bounds
utmLakeShape: gpd.GeoDataFrame = gdLakeShape.to_crs(crs=utm_sref.ExportToProj4())

utmPoly, utmRegions = shpManager.getRegion(utmLakeShape, "Lake_Name", LakeIndex, 2000 )
utmCroppedWaterMask: xr.DataArray = utmWaterMask.xgeo.crop_to_poly(utmPoly)
utmCutoutWaterMask: xr.DataArray = shpManager.crop(utmCroppedWaterMask, utmRegions)
utmCroppedReliability: xr.DataArray = utmReliability.xgeo.crop_to_poly(utmPoly)
utmCutoutReliability: xr.DataArray = shpManager.crop(utmCroppedReliability, utmRegions)

croppedWaterMask = waterMask.xgeo.crop( *geoBounds )

counts = utmCutoutWaterMask.xgeo.countInstances([2, 3])
norm = counts.max( dim="time" )
counts = counts/norm
reliability_series = reliability.sum( dim=['x','y'] )
rnorm = reliability_series.max( dim="time_bins" )
norm_reliability: xr.DataArray = reliability_series/rnorm

t0 = time.time()
cm_colors = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)]
bar_colors = [ (1, 1, 0), (0, 0, 1), (0,0,0) ]
normalize = Normalize(0, len(cm_colors))
cm = LinearSegmentedColormap.from_list("tmp-colormap", cm_colors, N=len(cm_colors))
subtitle_size = 10
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

figure, axes = plt.subplots( 2, 3 )
figure.suptitle( "Lake Mapping Analysis", fontsize=16)
figure.canvas.mpl_connect('button_press_event', onClick)
titles = [ "Water Mask", "Clipped WMask", "Projected+cut" ]

images: List[AxesImage] = []
for iAxis in range(len(data_arrays)):
    axis = axes[ 0, iAxis ]
    axis.set_title(titles[iAxis], size=subtitle_size)
    image_data = data_arrays[iAxis][0]
    image: Image = axis.imshow(image_data, cmap=cm, norm=normalize)
    axis.set_yticklabels([]); axis.set_xticklabels([])
    images.append(image)

axis = axes[ 1, 0 ]
axis.set_title("Reliability", size=subtitle_size)
axis.set_yticklabels([]); axis.set_xticklabels([])
rnormalize = Normalize( 0.0, 1.0 )
reliability_image: Image = axis.imshow(reliability[0], cmap="jet", norm=rnormalize )
divider = make_axes_locatable(axis)
cax = divider.append_axes('bottom', size='5%', pad=0.05 )
figure.colorbar( reliability_image, cax=cax, orientation='horizontal' )

axis = axes[ 1, 1 ]
axis.set_title("Projected+cut", size=subtitle_size)
axis.set_yticklabels([]); axis.set_xticklabels([])
rnormalize = Normalize( 0.0, 1.0 )
cutout_reliability_image: Image = axis.imshow(utmCutoutReliability[0], cmap="jet", norm=rnormalize )

init_counts = counts[0].values
init_bar_heights = [ init_counts[0], init_counts[1], norm_reliability.values[0] ]
axis = axes[1,2]
barplot = axis.bar( [0, 1, 2], init_bar_heights, color = bar_colors )
axis.set_yticklabels([]); axis.set_xticklabels([])
axis.set_title("Counts+Reliability", size=subtitle_size)

def animate(frameIndex):
    frame_data = [ data_array[frameIndex] for data_array in data_arrays ]
    for data, image in zip( frame_data, images ): image.set_array( data )
    reliability_image.set_array( reliability[frameIndex] )
    cutout_reliability_image.set_array( utmCutoutReliability[frameIndex] )
    bar_heights = counts[frameIndex]
    barplot[0].set_height( bar_heights[0] )
    barplot[1].set_height( bar_heights[1] )
    barplot[2].set_height( norm_reliability.values[frameIndex] )

anim = animation.FuncAnimation( figure, animate, frames=nFrames, interval=1000.0 / fps, blit=False)

if savePath is not None:
    anim.save(savePath, fps=fps)
    print(f" Animation saved to {savePath}")

plt.tight_layout()
plt.show()

