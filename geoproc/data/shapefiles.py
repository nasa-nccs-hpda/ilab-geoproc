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

    def getRegion( self, shape: gpd.GeoDataFrame, name_col: str, poly_index, buffer: float = 0.0 ) -> Tuple[Polygon,Regions_cls]:
        poly_name: str = [ shape[name_col].tolist()[poly_index] ]
        poly: Polygon = self.remove_third_dimension( shape.geometry.values[poly_index] )
        if buffer > 0: poly = poly.buffer( buffer )
        print( f" Creating region for polygon with bounds = {poly.envelope.bounds}" )
        return poly, regionmask.Regions_cls( poly_name, [0], [poly_name], [poly_name], [poly] )

    def crop(self, image: xa.DataArray, regions: Regions_cls ) -> xa.DataArray:
        region_mask = regions.mask( image, lat_name=image.dims[-2], lon_name=image.dims[-1] )
        return image.where( region_mask == 0 )

    def extractTile(self, gdFrame: gpd.GeoDataFrame, location: str, size: int = 10) -> LinearRing:
        origin: Point = self.parseLocation(location)
        return gdFrame.cx[ origin.x: origin.x+size, origin.y: origin.y-size ]

    def getLatLonBoundingBox(self, origin: Point, size: Point ) -> LinearRing:
        x = origin.x + 360.0
        coords = [ (x, origin.y), (x + size.x, origin.y), (x + size.x, origin.y + size.y), (x, origin.y + size.y) ]
        print( f"BBox coords: {coords}")
        return LinearRing( coords )

if __name__ == '__main__':
    from geoproc.surfaceMapping.lakes import WaterMapGenerator
    from geoproc.data.mwp import MWPDataManager
    from osgeo import gdal, gdalconst, ogr, osr
    from geoproc.util.visualization import TilePlotter, ArrayAnimation
    from geoproc.data.grid import GDALGrid
    import os
#    from geoproc.xext.xgeo import XGeo
    import xarray as xr
    SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/shp/MEASURESLAKESSHAPES.shp"
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    location: str = locations[0]
    product: str = products[0]
    year = 2019
    download = False
    shpManager = ShapefileManager()
    locPoint: Point = shpManager.parseLocation(location)
    minH20 = 2
    threshold = 0.5
    binSize = 8
    time_range = [1, 365]
    #    subset = [500,100]
    subset = None

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
    gdalGrid: GDALGrid = waterMask.xgeo.to_gdalGrid()
    utmGdalGrid = gdalGrid.reproject( utm_sref, (250,250) )
    utmDataArray = utmGdalGrid.xarray( "utmDataArray" )
    print( "Reprojected tile data")

    gdFrame: gpd.GeoDataFrame = shpManager.read( SHAPEFILE )
    gdFrameTile: gpd.GeoDataFrame = shpManager.extractTile( gdFrame, location, 10 )
    utmFrameTile = gdFrameTile.to_crs(crs=utm_sref.ExportToProj4())

    poly, regions = shpManager.getRegion( utmFrameTile, "Lake_Name", 6 )
    cropped_data_array: xa.DataArray = utmDataArray.xgeo.crop_to_poly( poly, 2000 )
    croppedTileImage: xa.DataArray = shpManager.crop( cropped_data_array, regions )

    animator = ArrayAnimation()
    waterMaskAnimationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_Lake-mask-m{minH20}.gif')
    animator.create_multi_array_animation( "Water Mask Segmentation", [ waterMask, cropped_data_array, croppedTileImage ], waterMaskAnimationFile, overwrite = True )

    plt.show()