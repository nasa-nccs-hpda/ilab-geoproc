import geopandas as gpd
from shapely.geometry import *
from typing import List
import xarray as xr
from glob import glob
from geoproc.surfaceMapping.dev.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
savePath = DATA_DIR + "/LakeMap_counts_diagnostic_animation.gif"
location: str = locations[0]
product: str = products[1]
year = 2015
download = True
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
animate = True
plot_dem = True

lake_boundary = gpd.read_file( SHAPEFILE ).boundary

dataMgr = MWPDataManager(DATA_DIR, dat_url)
dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
file_paths = dataMgr.get_tile(location)

dem_arrays: List[xr.DataArray] = dataMgr.get_array_data( glob( DEMs ) )
xc=dem_arrays[0].coords['x']
yc=dem_arrays[0].coords['y']
dem_array: xr.DataArray = dem_arrays[0]

waterMapGenerator = WaterMapGenerator()
data_array: xr.Dataset = waterMapGenerator.createDataset(file_paths)
cropped_data = data_array.xgeo.crop( xc[0], yc[-1], xc[-1], yc[0] )

masking_results = waterMapGenerator.get_water_masks(cropped_data, binSize, threshold, minH20)
water_masks = masking_results["mask"]

overlaid_dem_arrays = []
resampled_dem_array: xr.DataArray = dem_array.xgeo.resample_to_target( water_masks[0], dict( x='x', y='y' ) ) - 1275
overlaid_dem_array = xr.where( water_masks == 1, resampled_dem_array, water_masks )

overlaid_dem_array.xplot.animate(overlays=dict(black=lake_boundary), cmap="jet", range=(0, 30))

