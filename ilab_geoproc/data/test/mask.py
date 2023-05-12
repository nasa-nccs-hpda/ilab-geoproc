import geopandas as gpd
import rasterio
import xarray as xr
import matplotlib.pyplot as plt
from shapely.geometry import box, mapping
import rioxarray

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"


lake_boundary: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

raster_file = '/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/120W050N/MWP_2019222_120W050N_2D2OT.tif'
# dataset = XRio.open( raster_file, mask=lake_boundary )
# dataset = rasterio.open( raster_file )
xds = rioxarray.open_rasterio(raster_file)

clipped = xds.rio.clip( lake_boundary.geometry.apply(mapping), lake_boundary.crs  )

clipped.plot()

# xds.plot()

plt.show()