from typing import List, Union, Tuple
import xarray as xr
import pandas as pd
from geoproc.xext.xextension import XExtension
from geopandas import GeoDataFrame
import os, warnings
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
        oargs = argfilter( kwargs, parse_coordinates = None, chunks = None, cache = None, lock = None )
        result: xr.DataArray = rioxarray.open_rasterio( filename, **oargs )
        band = kwargs.pop( 'band', -1 )
        if band >= 0: result = result.isel(band=band)
        if mask is None: return result
        return result.xrio.clip( mask, **kwargs )

    def clip(self, geodf: GeoDataFrame, **kwargs ):
        cargs = argfilter( kwargs, all_touched = True, drop = True )
        mask_value = kwargs.pop( 'mask_value', 255  )
        self._obj.rio.set_nodata(mask_value)
        result = self._obj.rio.clip( geodf.geometry.apply(mapping), geodf.crs, **cargs )
        result.attrs['mask_value'] = mask_value
        return result

    @classmethod
    def load( cls, filePaths: Union[ str, List[str] ], **kwargs ) -> Union[ List[xr.DataArray], xr.DataArray ]:
        merge = kwargs.pop('merge', True)
        mask: GeoDataFrame = kwargs.pop("mask", None)
        if isinstance( filePaths, str ): filePaths = [ filePaths ]
        array_list: List[xr.DataArray] =  [ cls.open( file, mask, **kwargs ) for file in filePaths ]
        if merge and (len(array_list) > 1) and cls.mergable( array_list[0], array_list[1] ):
            return cls.merge( array_list, **kwargs )
        return array_list if (len(array_list) > 1) else array_list[0]

    @classmethod
    def merge( cls, data_arrays: List[xr.DataArray], **kwargs ) -> xr.DataArray:
        new_axis_name = kwargs.get('axis','time')
        indexed = kwargs.get('indexed',True)
        new_axis_values = range( len(data_arrays) ) if indexed else [da.name for da in data_arrays]
        merge_coord = pd.Index( new_axis_values, name=new_axis_name )
        result: xr.DataArray =  xr.concat( objs=data_arrays, dim=merge_coord )
        return result

    @classmethod
    def mergable(cls, a0: xr.DataArray, a1: xr.DataArray) -> bool:
        return a0.shape == a1.shape
