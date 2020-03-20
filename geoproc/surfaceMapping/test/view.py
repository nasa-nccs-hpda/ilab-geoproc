import geopandas as gpd
import rasterio
import xarray as xr
from geoproc.xext.xgeo import XGeo
from geoproc.xext.xrio import XRio
import matplotlib.pyplot as plt
from shapely.geometry import box, mapping
import rioxarray

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"

lake_boundary: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

lake_file = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/MOD44W/new/lake1341_MOD44W_2000_C6.tif"
lake_file1 = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/MOD44W/2000/334_2000.tif"

dest_file = "/tmp/test.tif"
# dataset = XRio.open( raster_file, mask=lake_boundary )
# dataset = rasterio.open( raster_file )


# rxds = xds.xgeo.reproject( nx=xds.shape[-1], ny=xds.shape[-2])
XRio.convert( lake_file, dest_file )

xds = rioxarray.open_rasterio(dest_file)

xds.plot()

plt.show()


