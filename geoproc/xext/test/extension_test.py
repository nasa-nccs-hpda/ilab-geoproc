from geoproc.data.mwp import MWPDataManager
from typing import Dict, List, Tuple
from osgeo import osr, gdalconst, gdal
from pyproj import Proj, transform
from geoproc.data.grid import GDALGrid
import xarray as xr
import numpy as np

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
location = "120W050N"
dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
dataMgr.setDefaults( product="1D1OS", download=True, year=2019, start_day=200, end_day=205 )
files = dataMgr.get_tile(location, download=False)

arrays: List[xr.DataArray] = dataMgr.get_array_data(files)
data_array: xr.DataArray = arrays[0]
data_array1: xr.DataArray = arrays[1]
data_array.xgeo.set_persistent_attribute( "version", "T1" )
mag = lambda x, y: np.sqrt( x ** 2 + y ** 2 )

with xr.set_options(keep_attrs=True):
    mean_axis_0 = data_array.mean( axis=0 )
    global_sum = data_array + 1.0
    abs_value =  np.abs( data_array )
    mag_value = xr.apply_ufunc( mag, data_array, data_array1 )
    mag_value1 = xr.apply_ufunc(mag, data_array, data_array1, keep_attrs=True)

    print( f" INIT: {data_array.xgeo.get_persistent_attribute('version')}" )
    print( f" AFTER MEAN: {mean_axis_0.xgeo.get_persistent_attribute('version')}" )
    print( f" AFTER SUM: {global_sum.xgeo.get_persistent_attribute('version')}" )
    print( f" AFTER ABS: {abs_value.xgeo.get_persistent_attribute('version')}" )
    print( f" AFTER UFUNC: {mag_value.xgeo.get_persistent_attribute('version') }")
    print( f" AFTER UFUNC+KEEP-ATTR: {mag_value1.xgeo.get_persistent_attribute('version')}" )