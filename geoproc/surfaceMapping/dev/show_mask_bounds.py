import xarray as xa
from math import floor, fabs
from typing import List, Union, Tuple
from geoproc.surfaceMapping.util import TileLocator

#    lake_id = 334
#    lake_mask_file = f"/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/MOD44W/2005/{lake_id}_2005.tif"
#    array: xa.DataArray = xa.open_rasterio( lake_mask_file )
#    print( TileLocator.get_gfm_tile(array) )

from geoproc.data.mwp import MWPDataManager
import xarray as xr
from geoproc.xext.xgeo import XGeo

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
location: str = "020E020S"
year = 2014
threshold = 0.5
download = True
binSize = 8
time_range = [0, 3]

dataMgr = MWPDataManager( DATA_DIR, dat_url )
dataMgr.setDefaults(product="2D2OT", download=download, year=year, start_day=time_range[0], end_day=time_range[1])
file_paths = dataMgr.get_tile(location)
data_arrays: List[xr.DataArray ] =  XGeo.loadRasterFiles(file_paths[0:2], band=1 )
print( f"Reading location: {location}")
print( TileLocator.get_bounds(data_arrays[0]) )
print( TileLocator.infer_tile_xa( data_arrays[0] ) )