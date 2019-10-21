import geopandas as gpd
import matplotlib.pyplot as plt
from geoproc.util.configuration import ConfigurableObject
from typing import Dict, List, Tuple, Union
from shapely.geometry import *
import xarray as xa
import regionmask
from geoproc.util.crs import CRS
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

    def getRegions( self, region_name: str, name_col: str, shape: gpd.GeoDataFrame ) -> Regions_cls:
        poly_index = 6
        names = [ shape[name_col].tolist()[poly_index] ]
        poly: Polygon = self.remove_third_dimension( shape.geometry.values[poly_index] )
        print( f" Creating region for polygon with bounds = {poly.envelope.bounds}" )
        return regionmask.Regions_cls( region_name, list(range(len(names))), names, names, [poly] )

    def getRegion( self, shape: gpd.GeoDataFrame, name_col: str, poly_index ) -> Tuple[Polygon,Region_cls]:
        poly_name: str = [ shape[name_col].tolist()[poly_index] ]
        poly: Polygon = self.remove_third_dimension( shape.geometry.values[poly_index] )
        print( f" Creating region for polygon with bounds = {poly.envelope.bounds}" )
        return poly, regionmask.Region_cls( poly_index, poly_name, poly_name, poly )

    def crop(self, image: xa.DataArray, regions: Regions_cls ):
        # bounds = { k:(c.values[0],c.values[-1]) for (k,c) in image.coords.items() if k in image.dims }
        # print(f" Cropping region for image with bounds = {bounds}")
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
    from osgeo import gdal, gdalconst, ogr, osr
    from geoproc.util.visualization import TilePlotter
    from geoproc.xext.xgeo import XGeo
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
    shpManager = ShapefileManager()
    locPoint: Point = shpManager.parseLocation(location)

    tData: xr.DataArray = XGeo.loadRasterFile("/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/120W050N/MWP_2019280_120W050N_1D1OS.tif")
    coords = tData.coords
    x = coords['x'].values
    y = coords['y'].values
    xbounds = [ round(x[0]), round(x[-1]) ]
    ybounds = [ round(y[0]), round(y[-1]) ]
    print( f" xbounds = {xbounds}, ybounds = {ybounds} " )

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults(product=product, download=download, year=2019, start_day=1, end_day=365)
    data_arrays = dataMgr.get_tile_data(location)
    utm_sref: osr.SpatialReference = data_arrays[0].xgeo.getUTMProj()
    print( "Downloaded tile data")

    gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
    gdFrameTile: gpd.GeoDataFrame = shpManager.extractTile( gdFrame, location, 10 )
    gdFrameTile.plot( ax=axes[1] )

    utmFrameTile = gdFrameTile.to_crs( crs=utm_sref.ExportToProj4() )

    poly, region = shpManager.getRegion( gdFrameTile, "Lake_Name", 6 )
    cropped_data_array = data_arrays[0].xgeo.crop_to_poly( poly )
    croppedTileImage = shpManager.crop( cropped_data_array, region )

    tilePlotter = TilePlotter()
    tilePlotter.plot( axes[0], croppedTileImage )

    plt.show()