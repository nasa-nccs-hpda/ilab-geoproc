import geopandas as gpd
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Tuple
from geoproc.util.configuration import ConfigurableObject, Region
from pandas import DataFrame
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Point

class ShapefileManager(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def read(self, shapefilePath: str ) -> gpd.GeoDataFrame:
        return gpd.read_file( shapefilePath )

    def getBoundingBox(self, location: str, size: int = 10) -> LinearRing:
        origin: Point = self.parseLocation(location)
        return self.getLatLonBoundingBox(origin, Point(size, size))

    def extractTile(self, gdFrame: gpd.GeoDataFrame, location: str, size: int = 10) -> LinearRing:
        origin: Point = self.parseLocation(location)
        return gdFrame.cx[ origin.x: origin.x+size, origin.y: origin.y-size ]

    def getLatLonBoundingBox(self, origin: Point, size: Point ) -> LinearRing:
        x = origin.x + 360.0
        coords = [ (x, origin.y), (x + size.x, origin.y), (x + size.x, origin.y + size.y), (x, origin.y + size.y) ]
        print( f"BBox coords: {coords}")
        return LinearRing( coords )

if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
    from geoproc.util.visualization import TilePlotter
    import xarray as xr
    SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/shp/MEASURESLAKESSHAPES.shp"
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = locations[0]
    product: str = products[0]
    year = 2019
    download = False
    figure, axes = plt.subplots(1, 2)

    tData = xr.open_rasterio("/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/120W050N/MWP_2019280_120W050N_1D1OS.tif")
    coords = tData.coords
    x = coords['x'].values
    y = coords['y'].values
    xbounds = [ round(x[0]), round(x[-1]) ]
    ybounds = [ round(y[0]), round(y[-1]) ]
    print( f" xbounds = {xbounds}, ybounds = {ybounds} " )

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults(product=product, download=download, year=2019, start_day=1, end_day=365)
    data_arrays = dataMgr.download_tile_data( location )
    print( "Downloaded tile data")
    tilePlotter = TilePlotter()
    tilePlotter.plot( axes[0], data_arrays )

    shpManager = ShapefileManager()
    gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
    gdFrameTile: gpd.GeoDataFrame = shpManager.extractTile( gdFrame, location, 10 )
    gdFrameTile.plot( ax=axes[1] )

    plt.show()