import geopandas as gpd
import rasterio
import xarray as xr
import matplotlib.pyplot as plt
from shapely.geometry import box, mapping
import rioxarray

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"

lake_boundary: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

lake_file = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/lake1005_MOD44W_2000_C6.tif"
# dataset = XRio.open( raster_file, mask=lake_boundary )
# dataset = rasterio.open( raster_file )
xds = rioxarray.open_rasterio(lake_file)

# clipped = xds.rio.clip( lake_boundary.geometry.apply(mapping), lake_boundary.crs  )

xds.plot()

plt.show()


