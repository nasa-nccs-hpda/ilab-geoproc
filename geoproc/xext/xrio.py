from typing import List, Union, Tuple
import xarray as xr
import pandas as pd
from geoproc.xext.xextension import XExtension
from geopandas import GeoDataFrame
import os, warnings
import numpy as np
from shapely.geometry import box, mapping
from geoproc.util.configuration import argfilter
import rioxarray


@xr.register_dataarray_accessor('xrio')
class XRio(XExtension):
    """  This is an extension for xarray to provide an interface to rasterio capabilities """

    def __init__(self, xarray_obj: xr.DataArray):
        XExtension.__init__( self, xarray_obj )

    @classmethod
    def open( cls, filename, mask=None, **kwargs ):
        try:
            oargs = argfilter( kwargs, parse_coordinates = None, chunks = None, cache = None, lock = None )
            result: xr.DataArray = rioxarray.open_rasterio( filename, **oargs )
            band = kwargs.pop( 'band', -1 )
            if band >= 0:
                result = result.isel( band=band, drop=True )
            result.encoding = dict( dtype = str(result.dtype))
            if mask is None: return result
#            x, y = result.coords['x'], result.coords['y']
#            print( f" {filename}:   x[{x.size}]: ( {x.data[0]:.2f}, {x.data[-1]:.2f} ) ")
            return result.xrio.clip( mask, **kwargs )
        except Exception as err:
            print( f"\nError opening file {filename}: {err}\n")
            return None

    def clip(self, geodf: GeoDataFrame, **kwargs ):
        cargs = argfilter( kwargs, all_touched = True, drop = True )
        mask_value = kwargs.pop( 'mask_value', 255  )
        self._obj.rio.set_nodata(mask_value)
        result = self._obj.rio.clip( geodf.geometry.apply(mapping), geodf.crs, **cargs )
        result.attrs['mask_value'] = mask_value
        result.encoding = self._obj.encoding
        return result

    @classmethod
    def load( cls, filePaths: Union[ str, List[str] ], **kwargs ) -> Union[ List[xr.DataArray], xr.DataArray ]:
        merge = kwargs.pop('merge', True)
        mask: GeoDataFrame = kwargs.pop("mask", None)
        if isinstance( filePaths, str ): filePaths = [ filePaths ]
        array_list: List[xr.DataArray] = []
        for file in filePaths:
            data_array = cls.open( file, mask, **kwargs )
            if data_array is not None: array_list.append( data_array )
        if merge and (len(array_list) > 1):
            assert cls.mergable( array_list ), f"Attempt to merge arrays with different shapes"
            result = cls.merge( array_list, **kwargs )
            return result
        return array_list if (len(array_list) > 1) else array_list[0]

    @classmethod
    def merge( cls, data_arrays: List[xr.DataArray], **kwargs ) -> xr.DataArray:
        new_axis_name = kwargs.get('axis','time')
        new_axis_values = kwargs.get('index', range( len(data_arrays) ) )
        merge_coord = pd.Index( new_axis_values, name=new_axis_name )
        result: xr.DataArray =  xr.concat( data_arrays, merge_coord ).astype( data_arrays[0].dtype )
        return result

    @classmethod
    def mergable(cls, arrays: List[xr.DataArray]) -> bool:
        for array in arrays:
            if array.shape != arrays[0].shape: return False
        return True
