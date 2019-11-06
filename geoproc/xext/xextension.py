import numpy as np, os
from osgeo import osr
import xarray as xr

class XExtension(object):
    """  This is the base class for xarray extensions """

    StandardAxisNames = { 'x': [ 'x', 'lon' ], 'y': [ 'y', 'lat' ], 't': [ 't', 'time' ] }
    StandardAxisPositions = {'x': -1, 'y': -2, 't': 0 }

    def __init__(self, xarray_obj: xr.DataArray):
        self._obj: xr.DataArray = xarray_obj
        self.y_coord = self.getCoordName('y')
        self.x_coord = self.getCoordName('x')
        self.time_coord = self.getCoordName('t')
        self._crs: osr.SpatialReference = self.getSpatialReference()
        self._geotransform = self.getTransform()
        self._y_inverted = self.ycoords[0] > self.ycoords[-1]

    @property
    def xcoords(self)-> np.ndarray:
        return self._obj[self.x_coord].values

    @property
    def ycoords(self)-> np.ndarray:
        return self._obj[self.y_coord].values

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

    @property
    def resolution(self):
        transform = self.getTransform()
        return [ transform[1], -transform[5] ]

    def getTransform(self):
        transform = self._obj.attrs.get("transform")
        if transform is None:
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
            transform = min_x_tl, x_cell_size, 0, max_y_tl, 0, -y_cell_size
            self._obj.attrs['transform'] = transform
        return transform
