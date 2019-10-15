import math, rasterio
import xarray as xa
import numpy as np

class CRS:

    @classmethod
    def get_utm_crs( cls, longitude: float, north: bool = True ) -> str:
        if longitude > 180: long = longitude - 360
        zone = math.floor((longitude + 180)/6) + 1
        result =  f"+proj=utm +zone={zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        if not north: result = result + " +south"
        return result


    @classmethod
    def to_geotiff(cls, array: xa.DataArray, output_filename: str):
        array = array.load()

        if len(array.shape) == 2:
            count = 1
            height = array.shape[0]
            width = array.shape[1]
            band_indicies = 1
        else:
            count = array.shape[0]
            height = array.shape[1]
            width = array.shape[2]
            band_indicies = np.arange(count) + 1

        processed_attrs = {}
        try:
            from rasterio import Affine
            val = array.attrs.get( 'transform', array.attrs['affine'] )
            processed_attrs['transform'] = Affine.from_gdal(*val)
        except Exception as ex:
            print( f"Error processing transform: {ex}")

        try:
            from rasterio import crs
            val = array.attrs['crs']
            processed_attrs['crs'] = crs.CRS.from_string(val)
        except Exception as ex:
            print( f"Error processing crs: {ex}")

        with rasterio.open(output_filename, 'w', driver='GTiff',  height=height, width=width,  dtype=str(array.dtype), count=count,  **processed_attrs) as dst:
            dst.write(array.values, band_indicies)




