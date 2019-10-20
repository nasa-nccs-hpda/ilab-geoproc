from affine import Affine
import numpy as np
from osgeo import osr, gdalconst, gdal
from pyproj import Proj, transform
from geoproc.xext.grid import GDALGrid
import xarray as xr


@xr.register_dataarray_accessor('xgeo')
class XGeo(object):
    """  This is an extension for xarray to provide an interface to GDAL capabilities """

    StandardAxisNames = { 'x': [ 'x', 'lon' ], 'y': [ 'y', 'lat' ], 't': [ 't', 'time' ] }
    StandardAxisPositions = {'x': -1, 'y': -2, 't': 0 }

    def __init__(self, xarray_obj: xr.DataArray):
        self._obj: xr.DataArray = xarray_obj
        self.y_coord = self.getCoordName('y')
        self.x_coord = self.getCoordName('x')
        self.time_coord = self.getCoordName('t')
        self._crs: osr.SpatialReference = self.getSpatialReference()
        self._geotransform = self.getTransform()
        self._center = None
        self._y_inverted = None

        # convert lon from [0 to 360] to [-180 to 180]
        self.lon_to_180 = False
        # coordinates are projected already
        self.coords_projected = False

    def getCoordName( self, axis: str ) -> str:
        for cname, coord in self._obj.coords.items():
            if str(cname).lower() in self.StandardAxisNames[axis] or coord.attrs.get("axis") == axis:
                return str(cname)
        return  self._obj.dims[ self.StandardAxisPositions[axis] ]


    def getSpatialReference( self ) -> osr.SpatialReference:
        sref = osr.SpatialReference()
        crs = self._obj.attrs.get('crs')
        if crs is None:
            sref.ImportFromEPSG(4326)
        else:
            if "epsg" in crs.lower():
                espg = int(crs.split(":")[-1])
                sref.ImportFromEPSG(espg)
            elif "+proj" in crs.lower():
                sref.ImportFromProj4(crs)
            else:
                raise Exception(f"Unrecognized crs: {crs}")
        return sref


    def getTransform(self):
        y_arr = self._obj.coords[ self.y_coord ]
        x_arr = self._obj.coords[ self.x_coord ]
        res = self._obj.attrs.get('res')

        if y_arr.ndim < 2:
            x_2d, y_2d = np.meshgrid(x_arr, y_arr)
        else:
            x_2d = x_arr
            y_2d = y_arr

        x_cell_size = np.nanmean(np.absolute(np.diff(x_2d, axis=1))) if res is None else res[1]
        y_cell_size = np.nanmean(np.absolute(np.diff(y_2d, axis=0))) if res is None else res[0]

        min_x_tl = x_2d[0, 0] - x_cell_size / 2.0
        max_y_tl = y_2d[0, 0] + y_cell_size / 2.0
        return min_x_tl, x_cell_size, 0, max_y_tl, 0, -y_cell_size

    def to_gdal(self):
        num_bands = 1
        in_array = self._obj.values
        nodata_value = self._obj.attrs.get('nodatavals',[None])[0]
        gdal_dtype = gdalconst.GDT_Float32
        proj = self._crs.ExportToWkt()

        if in_array.ndim == 3:  num_bands, y_size, x_size = in_array.shape
        else:                   y_size, x_size = in_array.shape

        dataset = gdal.GetDriverByName('MEM').Create("GdalDataset", x_size, y_size, num_bands, gdal_dtype)

        dataset.SetGeoTransform( self._geotransform )
        dataset.SetProjection( proj )

        if in_array.ndim == 3:
            for band in range(1, num_bands + 1):
                rband = dataset.GetRasterBand(band)
                rband.WriteArray(in_array[band - 1])
                if nodata_value is not None:
                    rband.SetNoDataValue(nodata_value)
        else:
            rband = dataset.GetRasterBand(1)
            rband.WriteArray(in_array)
            if nodata_value is not None:
                rband.SetNoDataValue(nodata_value)

        return dataset

    def to_gdalGrid(self) -> GDALGrid:
        return GDALGrid( self.to_gdal())

if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    import cartopy.crs as ccrs
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location = "120W050N"
    dataMgr = MWPDataManager( DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products" )
    dataMgr.setDefaults( product = "1D1OS", download = True, year = 2019, start_day = 200, end_day = 205 )
    files = dataMgr.get_tile(location, download = False)

    arrays = dataMgr.get_array_data(files)
    data_array = arrays[0]

    dset: GDALGrid = data_array.xgeo.to_gdalGrid()

    new_proj: osr.SpatialReference = dset.get_utm_proj()
    reprojected_dset: GDALGrid  = dset.to_projection( new_proj )
    grid_data = reprojected_dset.np_array()

    fig = plt.figure(figsize=[10, 5])
    colors = [(0, 0, 0), (0.15, 0.3, 0.5), (0, 0, 1), (1, 1, 0)]
    norm = Normalize(0, 4)
    cm = LinearSegmentedColormap.from_list("lake-map", colors, N=4)

    ax1 = fig.add_subplot( 1, 2, 1 ) # , projection=ccrs.PlateCarree() )
    ax1.imshow(data_array.values, cmap=cm, norm=norm )

    ax2 = fig.add_subplot( 1, 2, 2 )
    ax2.imshow( grid_data, cmap=cm, norm=norm )

    plt.show()


