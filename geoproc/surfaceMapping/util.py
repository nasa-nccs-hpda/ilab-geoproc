import xarray as xa
import geopandas as gpd
from math import floor, ceil
from typing import List, Union, Tuple, Optional

class TileLocator:

    @classmethod
    def floor10(cls, fval: float) -> int:
        return abs( int(floor(fval / 10.0)) * 10 )

    @classmethod
    def ceil10(cls, fval: float) -> int:
        return abs( int(ceil(fval / 10.0)) * 10 )

    @classmethod
    def unwrap(cls, coord: float) -> float:
        return coord if coord < 180 else coord - 360

    @classmethod
    def lon_label(cls, lon: float ) -> str:
        ulon = cls.unwrap( lon )
        if ulon < 0: return f"{cls.floor10(ulon):03d}W"
        else:        return f"{cls.floor10(ulon):03d}E"

    @classmethod
    def lat_label(cls, lat: float ) -> str:
        if lat > 0: return f"{cls.ceil10(lat):03d}N"
        else:       return f"{cls.ceil10(lat):03d}S"

    @classmethod
    def infer_tile_xa( cls, array: xa.DataArray ) -> str:
        x_coord = array.coords['x'].values
        y_coord = array.coords['y'].values
        return cls.get_tile( x_coord[0], x_coord[-1], y_coord[0], y_coord[-1]  )

    @classmethod
    def infer_tile_gpd( cls, series: gpd.GeoSeries ) -> str:
        [xmin, ymin, xmax, ymax] = series.geometry.boundary.bounds.values[0]
        return cls.get_tile( xmin, xmax, ymin, ymax )

    @classmethod
    def get_tile( cls, xmin, xmax, ymin, ymax ) -> Optional[str]:
        xc0, xc1 = cls.lon_label( xmin ), cls.lon_label( xmax )
        yc0, yc1 = cls.lat_label( ymin ), cls.lat_label( ymax )
        if xc0 != xc1:
            print( f"Lake mask straddles lon tiles: {xc0} {xc1}" )
            return None
        if yc0 != yc1:
            print( f"Lake mask straddles lat tiles: {yc0} {yc1}" )
            return None
        result = f"{xc0}{yc0}"
        print( f"Inferring tile {result} from xbounds = {[xmin,xmax]}, ybounds = {[ymin,ymax]}" )
        return result

    @classmethod
    def get_bounds(cls, array: xa.DataArray ) -> List:
        x_coord = array.coords['x'].values
        y_coord = array.coords['y'].values
        return [ x_coord[0], x_coord[-1], y_coord[0], y_coord[-1] ]

if __name__ == '__main__':
    lake_id = 334
    lake_mask_file = f"/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/MOD44W/2005/{lake_id}_2005.tif"
    array: xa.DataArray = xa.open_rasterio( lake_mask_file )
    print( TileLocator.infer_tile_xa(array) )

    roi = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
    roi_bounds: gpd.GeoSeries = gpd.read_file(roi)
    print(TileLocator.infer_tile_gpd(roi_bounds))