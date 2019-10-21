# Adapted from https://github.com/snowman2/pangaea.git
from affine import Affine
import numpy as np
from osgeo import osr, gdalconst, gdal
import pandas as pd
from pyproj import Proj, transform
from geoproc.data.grid import (geotransform_from_yx, resample_grid, utm_proj_from_latlon, ArrayGrid)
import xarray as xr


@xr.register_dataarray_accessor('geoproc')
class GeoProc(object):
    """  This is an extension for xarray to provide an interface to GDAL capabilities """

    def __init__(self, xarray_obj: xr.DataArray):
        self._obj: xr.DataArray = xarray_obj
        self._projection = None
        self._epsg = None
        self._geotransform = None
        self._affine = None
        self._center = None
        self._y_inverted = None

        # set variable information
        self.y_coord = 'lat'
        self.x_coord = 'lon'
        self.time_coord = 'time'
        # set dimension information
        self.y_dim = -2
        self.x_dim = -1
        self.time_dim = -3
        # convert lon from [0 to 360] to [-180 to 180]
        self.lon_to_180 = False
        # coordinates are projected already
        self.coords_projected = False

    def to_datetime(self):
        """Converts time to datetime."""
        time_values = self._obj.coords[self.time_coord].values
        if 'datetime' not in str(time_values.dtype):
            try:
                time_values = [time_val.decode('utf-8') for
                               time_val in time_values]
            except AttributeError:
                pass

            try:
                datetime_values = pd.to_datetime(time_values)
            except ValueError:
                # WRF DATETIME FORMAT
                datetime_values = \
                    pd.to_datetime(time_values,
                                   format="%Y-%m-%d_%H:%M:%S")

            self._obj.coords[self.time_coord].values = datetime_values

    @property
    def y_inverted(self):
        """Is the y-coord inverted"""
        if self._y_inverted is None:
            y_coords = self._obj.coords[self.y_coord].values
            if y_coords.ndim == 3:
                y_coords = y_coords[0]
            if y_coords.ndim == 2:
                self._y_inverted = (y_coords[-1, 0] > y_coords[0, 0])
            else:
                self._y_inverted = (y_coords[-1] > y_coords[0])
        return self._y_inverted

    @property
    def datetime(self):
        """Get datetime object for time variable"""
        self.to_datetime()
        return pd.to_datetime(self._obj.coords[self.time_coord].values)

    @property
    def projection(self) -> osr.SpatialReference:
        """  The projection for the data array. """
        if self._projection is None:
            # read projection information from global attributes
            map_proj4 = self._obj.attrs.get('proj4')
            if map_proj4 is not None:
                self._projection = osr.SpatialReference()
                self._projection.ImportFromProj4(str(map_proj4))
            else:
                # default to EPSG 4326
                self._projection = osr.SpatialReference()
                self._projection.ImportFromEPSG(4326)
            # make sure EPSG loaded if possible
            self._projection.AutoIdentifyEPSG()
        return self._projection

    @property
    def epsg(self):
        """str: EPSG code"""
        if self._epsg is None:
            self._epsg = self.projection.GetAuthorityCode(None)
        return self._epsg

    @property
    def dx(self):
        """float: Pixel size in x direction."""
        return self.geotransform[1]

    @property
    def dy(self):
        """float: Pixel size in y direction."""
        return -self.geotransform[-1]

    @property
    def geotransform(self):
        """:obj:`tuple`: The geotransform for grid."""
        if self._geotransform is None:
            if self._obj.attrs.get('transform') is not None:
                self._geotransform = [float(g) for g in self._obj.attrs.get('transform')]

            elif str(self.epsg) != '4326':
                proj_y, proj_x = self.coords
                self._geotransform = geotransform_from_yx(proj_y, proj_x)
            else:
                self._geotransform = geotransform_from_yx(*self.latlon)

        return self._geotransform

    @property
    def affine(self):
        """:func:`Affine`: The affine for the transformation."""
        if self._affine is None:
            self._affine = Affine.from_gdal(*self.geotransform)
        return self._affine

    @property
    def x_size(self):
        """int: Number of columns in the dataset."""
        return self._obj.shape[self.x_dim]

    @property
    def y_size(self):
        """int: Number of rows in the dataset."""
        return self._obj.shape[self.y_dim]

    @property
    def _raw_coords(self):
        """Gets the raw coordinated of dataset"""
        x_coords = self._obj.coords[self.x_coord].values
        y_coords = self._obj.coords[self.y_coord].values

        if x_coords.ndim == 3:
            x_coords = x_coords[0]
        if y_coords.ndim == 3:
            y_coords = y_coords[0]

        if x_coords.ndim < 2:
            x_coords, y_coords = np.meshgrid(x_coords, y_coords)

        if self.y_inverted:
            x_coords = x_coords[::-1]
            y_coords = y_coords[::-1]

        return y_coords, x_coords

    @property
    def latlon(self):
        """ Returns lat,lon arrays  """
        lat, lon = self._raw_coords
        if self.coords_projected:
            lon, lat = transform(Proj(self.projection.ExportToProj4()), Proj(init='epsg:4326'), lon,  lat)

        if self.lon_to_180:  lon = (lon + 180) % 360 - 180  # convert [0, 360] to [-180, 180]

        return lat, lon

    @property
    def coords(self):
        """Returns y, x coordinate arrays  """
        if not self.coords_projected:
            lat, lon = self.latlon
            x_coords, y_coords = transform(Proj(init='epsg:4326'),  Proj(self.projection.ExportToProj4()), lon, lat)
            return y_coords, x_coords
        return self._raw_coords

    @property
    def center(self):
        """Return the geographic center point of this dataset."""
        if self._center is None:
            lat, lon = self.latlon
            self._center = (float(np.nanmean(lon)), float(np.nanmean(lat)))
        return self._center


    def resample(self, match_grid: gdal.Dataset ):
        """ Resample data to grid. """
        new_data = []
        for band in range(self._obj.dims[self.time_dim]):
            data = self._obj.values
            arr_grid = ArrayGrid(in_array=data, wkt_projection=self.projection.ExportToWkt(), geotransform=self.geotransform)
            resampled_data_grid = resample_grid(original_grid=arr_grid, match_grid=match_grid,  as_gdal_grid=True)
            new_data.append(resampled_data_grid.np_array())

        self.to_datetime()
        return self._export_dataset(np.array(new_data), resampled_data_grid)

    def to_projection( self, target_projection: osr.SpatialReference ) -> xr.Dataset:
        """Convert Grid to New Projection. """
        new_data = []
        for band in range(self._obj.dims[self.time_dim]):
            arr_grid = ArrayGrid(in_array=self._obj[band].values, wkt_projection=self.projection.ExportToWkt(), geotransform=self.geotransform)
            ggrid = arr_grid.to_projection( target_projection, gdalconst.GRA_Average )
            new_data.append(ggrid.np_array())

        self.to_datetime()
        return self._export_dataset( np.array(new_data), ggrid )

    def to_utm( self, variable_name: str ) -> xr.Dataset:
        """Convert Grid to UTM projection at center of grid.  """
        # get utm projection
        center_lon, center_lat = self.center
        dst_proj = utm_proj_from_latlon( center_lat, center_lon, as_osr=True )
        return self.to_projection( variable_name, dst_proj )

    def to_tif( self, variable: str, time_index: int, out_path: str ):
        """Dump a variable at a time index to a geotiff.  """
        arr_grid = ArrayGrid(in_array=self._obj[time_index].values,  wkt_projection=self.projection.ExportToWkt(), geotransform=self.geotransform)
        arr_grid.to_tif(out_path)



if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
#    from geoproc.xext.xgdal import GeoProc

    locations = ["120W050N", "100W040N"]
    products = ["1D1OS", "2D2OT", "3D3OT"]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    location: str = locations[0]
    product: str = products[1]
    year = 2019
    download = True
    binSize = 8
    time_range = [200, 205]
    #    subset = [500,100]
    subset = None

    dataMgr = MWPDataManager(DATA_DIR, dat_url)
    dataMgr.setDefaults(product=product, download=download, year=year, start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)
    arrays = dataMgr.get_array_data( file_paths )
    test_array = arrays[0].rename( {'x':'lon', 'y':'lat'} )
    utm_test_array = test_array.geoproc.to_utm( )

    print( test_array.shape )


