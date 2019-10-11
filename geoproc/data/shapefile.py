import geopandas as gpd
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Tuple
from geoproc.util.configuration import ConfigurableObject, Region
from pandas import DataFrame
from shapely.geometry.polygon import LinearRing
from shapely.geometry import *
import xarray as xa
import regionmask
from regionmask import Regions_cls, Region_cls

class ShapefileManager(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )



    def remove_third_dimension( self, geom ):
        if geom.is_empty:
            return geom

        if isinstance(geom, Polygon):
            exterior = geom.exterior
            new_exterior = self.remove_third_dimension(exterior)

            interiors = geom.interiors
            new_interiors = []
            for int in interiors:
                new_interiors.append(self.remove_third_dimension(int))

            return Polygon(new_exterior, new_interiors)

        elif isinstance(geom, LinearRing):
            return LinearRing([xy[0:2] for xy in list(geom.coords)])

        elif isinstance(geom, LineString):
            return LineString([xy[0:2] for xy in list(geom.coords)])

        elif isinstance(geom, Point):
            return Point([xy[0:2] for xy in list(geom.coords)])

        elif isinstance(geom, MultiPoint):
            points = list(geom.geoms)
            new_points = []
            for point in points:
                new_points.append(self.remove_third_dimension(point))

            return MultiPoint(new_points)

        elif isinstance(geom, MultiLineString):
            lines = list(geom.geoms)
            new_lines = []
            for line in lines:
                new_lines.append(self.remove_third_dimension(line))

    def read(self, shapefilePath: str ) -> gpd.GeoDataFrame:
        return gpd.read_file( shapefilePath )

    def getBoundingBox(self, location: str, size: int = 10) -> LinearRing:
        origin: Point = self.parseLocation(location)
        return self.getLatLonBoundingBox(origin, Point(size, size))

    def getRegion(self, region_name: str, index: int, shape: Polygon) -> Region_cls:
        return regionmask.Region_cls( index, region_name, region_name, shape)

    def reproject(self, shape: gpd.GeoDataFrame, crs: str ) -> gpd.GeoDataFrame:
        current_crs = shape.crs.get("init")
        if crs is None or current_crs == crs: return shape
        return shape.to_crs( crs )


    def getRegions( self, region_name: str, name_col: str, shape: gpd.GeoDataFrame, **kwargs ) -> Regions_cls:
        poly_index = 6
        shape = self.reproject( shape, kwargs.get('crs') )
        names = [ shape[name_col].tolist()[poly_index] ]
        poly: Polygon = self.remove_third_dimension( shape.geometry.values[poly_index] )
        print( f" Creating region for polygon with bounds = {poly.envelope.bounds}" )
        return regionmask.Regions_cls( region_name, list(range(len(names))), names, names, [poly] )

    def crop(self, image: xa.DataArray, regions: Regions_cls, regionIndex = 1 ):
        bounds = { k:(c.values[0],c.values[-1]) for (k,c) in image.coords.items() if k in image.dims }
        print(f" Cropping region for image with bounds = {bounds}")
        region_mask = regions.mask( image, lat_name=image.dims[-2], lon_name=image.dims[-1] )
        return region_mask

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

    shpManager = ShapefileManager()
    gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
    gdFrameTile: gpd.GeoDataFrame = shpManager.extractTile( gdFrame, location, 10 )
    gdFrameTile.plot( ax=axes[1] )

    regions = shpManager.getRegions( "test", "Lake_Name", gdFrameTile )
    croppedTileImage = shpManager.crop( data_arrays[0], regions )

    tilePlotter = TilePlotter()
    tilePlotter.plot( axes[0], croppedTileImage )

    plt.show()