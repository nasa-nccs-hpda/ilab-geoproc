from geoproc.util.configuration import ConfigurableObject
from typing import Dict, List, Union
from osgeo import ogr
from osgeo import osr
from osgeo import gdal
import xarray as xr
import numpy as np
import os
from geoproc.xext.grid import (geotransform_from_yx, resample_grid, utm_proj_from_latlon, ArrayGrid)


class OsgeoManager(ConfigurableObject):

    def __init__(self, data_dir: str, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        self.data_dir = data_dir

    def getSpatialReference( self, crs: str ) -> osr.SpatialReference:
        sref = osr.SpatialReference()
        if "epsg" in crs.lower():
            espg = int(crs.split(":")[-1])
            sref.ImportFromEPSG(espg)
        elif "+proj" in crs.lower():
            sref.ImportFromProj4(crs)
        else:
            raise Exception(f"Unrecognized crs: {crs}")
        return sref

    def array2raster( self, newRasterfn, rasterOrigin, pixelWidth, pixelHeight, array ):

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

    def xarray2raster(self, array: xr.DataArray ) -> gdal.Dataset:
        out_dir, out_file = CRS.to_geotiff( array )
        ds: gdal.Dataset = gdal.Open( os.path.join( out_dir, out_file ) )
        return ds

    # def reprojectXarray(self, array: xr.DataArray, target_crs: str  ) -> xr.DataArray:
    #     out_dir, out_file = CRS.to_geotiff(array)
    #     input_raster = os.path.join( out_dir, out_file )
    #     output_raster = os.path.join( out_dir, f"out-{self.randomId(4)}.tif" )
    #     print( f"Reprojecting xarray to crs {target_crs}")
    #     gdal.Warp( output_raster, input_raster, format = 'GTiff', srcSRS=self.getSpatialReference(array.crs), dstSRS=self.getSpatialReference(target_crs), xRes=250, yRes=250  )
    #     da: xr.DataArray = xr.open_rasterio(output_raster)
    #     return da

    def reprojectXarray(self, array: xr.DataArray, resolution: float  ):
        xcoord = array.coords[array.dims[-1]]
        ycoord = array.coords[array.dims[-2]]
        longitude_location: float = (xcoord.values[0] + xcoord.values[-1]) / 2.0
        dest_crs = CRS.get_utm_crs( longitude_location )

        xbounds = [ xcoord.values[0], xcoord.values[-1] ]
        ybounds = [ ycoord.values[0], ycoord.values[-1] ]
        srcSRS = self.getSpatialReference(array.crs)
        dstSRS = self.getSpatialReference(dest_crs)
        transformation = osr.CoordinateTransformation(srcSRS, dstSRS)

        (ulx, uly, ulz ) =  transformation.TransformPoint( xbounds[0], ybounds[0] )
        (lrx, lry, lrz ) =  transformation.TransformPoint( xbounds[1], ybounds[1] )

        out_dir, out_file = CRS.to_geotiff(array)
        g: gdal.Dataset = gdal.Open( os.path.join(out_dir,out_file) )

        mem_drv = gdal.GetDriverByName('MEM')
        nx = int((lrx - ulx) / resolution)
        ny = int((uly - lry) / resolution)
        dest: gdal.Dataset = mem_drv.Create('', nx, ny, 1, gdal.GDT_Float32)
        new_geo = (ulx, resolution, 0.0,  uly, 0.0, -resolution )

        dest.SetGeoTransform( new_geo )
        dest.SetProjection ( dstSRS.ExportToWkt() )

        res = gdal.ReprojectImage( g, dest, srcSRS.ExportToWkt(), dstSRS.ExportToWkt(), gdal.GRA_Bilinear )

        gArray = dest.ReadAsArray()

        return gArray

if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
    from geoproc.util.crs import CRS
    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, Normalize

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
    south = location[-1] == "S"

    dataMgr = MWPDataManager( DATA_DIR, data_source_url )
    dataMgr.setDefaults(product=product, download=download, year=year, start_day=start_day, end_day=start_day+num_days-1 )
    file_paths = dataMgr.get_tile(location)
    arrays: List[xr.DataArray] = dataMgr.get_array_data( file_paths )
    data_array = arrays[0]

    osgeoManager = OsgeoManager( DATA_DIR )
    result:  np.ndarray = osgeoManager.reprojectXarray( arrays[0],  250 )

    print( result.shape )

    colors =  [(0, 0, 0), (0.5, 1, 0.25), (0, 0, 1), (1, 1, 0)]
    norm = Normalize( 0,len(colors) )
    cm = LinearSegmentedColormap.from_list( "geoProc-waterMap", colors, N=len(colors) )

    fig = plt.figure(figsize=[10, 5])

    ax1 = fig.add_subplot( 1, 2, 1 ) # , projection=ccrs.PlateCarree() )
    ax1.imshow(data_array.values, cmap=cm, norm=norm )

#    utm_proj = ccrs.UTM(zone=CRS.get_utm_zone(longitude_location), southern_hemisphere=south )
    ax2 = fig.add_subplot(1, 2, 2 ) # , projection= utm_proj )
    ax2.imshow(result, cmap=cm, norm=norm ) # , transform=ccrs.PlateCarree() )

    plt.show()
