import xarray as xa
from typing import List, Union, Tuple
from geoproc.surfaceMapping.util import TileLocator
from geoproc.data.mwp import MWPDataManager
import xarray as xr
from geoproc.xext.xgeo import XGeo

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"

def show_tile_bounds( location: str, year, time_range, download = True ):
    dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    dataMgr = MWPDataManager( DATA_DIR, dat_url )
    dataMgr.setDefaults(product="2D2OT", download=download, year=year, start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)
    data_arrays: List[xr.DataArray ] =  XGeo.loadRasterFiles(file_paths[0:2], band=1 )
    print( f"Reading location: {location}")
    print( TileLocator.get_bounds(data_arrays[0]) )
    print( TileLocator.infer_tile_xa( data_arrays[0] ) )

def show_lake_mask_bounds( lake_id: int ):
    lake_mask_file = f"{DATA_DIR}/MOD44W/2005/{lake_id}_2005.tif"
    array: xa.DataArray = xa.open_rasterio( lake_mask_file )
    bounds = TileLocator.get_bounds(array)
    print( f" X Bounds: {bounds[:2]}")
    print( f" Y Bounds: {bounds[2:]}")
    print( TileLocator.infer_tile_xa(array) )

# show_tile_bounds( "020E020S", 2014, [0, 3] )

show_lake_mask_bounds( 1295 )
