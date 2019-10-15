from geoproc.util.configuration import ConfigurableObject
from typing import Dict, List, Union
from osgeo import ogr
from osgeo import osr
from osgeo import gdal
import xarray as xr


class OsgeoManager(ConfigurableObject):

    def __init__(self, data_dir: str, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        self.data_dir = data_dir

    def reproject(self, array: xr.DataArray, dest_crs: str ) -> xr.DataArray:
        source = osr.SpatialReference()
        espg = int(array.crs.split(":")[1])
        source.ImportFromEPSG( espg )

        target = osr.SpatialReference()
        target.ImportFromProj4( dest_crs )

        transform = osr.CoordinateTransformation(source, target)

        print(".")

def array2raster( newRasterfn, rasterOrigin, pixelWidth, pixelHeight, array ):

    cols = array.shape[1]
    rows = array.shape[0]
    originX = rasterOrigin[0]
    originY = rasterOrigin[1]

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
    from geoproc.util.crs import CRS

    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    data_source_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    location: str = locations[1]
    product: str = products[0]
    year = 2019
    start_day = 171
    num_days = 4
    download = False

    dataMgr = MWPDataManager( DATA_DIR, data_source_url )
    dataMgr.setDefaults(product=product, download=download, year=year, start_day=start_day, end_day=start_day+num_days-1 )
    file_paths = dataMgr.get_tile(location)
    arrays: List[xr.DataArray] = dataMgr.get_array_data( file_paths )
    data_array = arrays[0]

    osgeoManager = OsgeoManager( DATA_DIR )

    xcoord = data_array.coords[data_array.dims[-1]]
    ycoord = data_array.coords[data_array.dims[-2]]
    longitude_location = ( xcoord.values[0] + xcoord.values[-1] )/2.0
    dst_crs =  CRS.get_utm_crs( longitude_location, True )

    osgeoManager.reproject( arrays[0], dst_crs )


