import xarray as xa
from typing import List, Union, Tuple
from geoproc.surfaceMapping.util import TileLocator
from geoproc.plot.animation import SliceAnimation
from geoproc.data.mwp import MWPDataManager
from geoproc.xext.xrio import XRio
import os
import numpy as np
import xarray as xr
from geoproc.xext.xgeo import XGeo
colors3 = [ ( 0, 'undetermined', (0, 0, 0) ),
            ( 1, 'land',  (0, 1, 0) ),
            ( 2, 'pwater', (0, 0, 1) ),
            ( 3, 'fwater', (1, 0, 0) ) ]

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"


def get_date_from_filename( filename: str):
    from datetime import datetime
    toks = filename.split("_")
    result = datetime.strptime(toks[1], '%Y%j').date()
    return np.datetime64(result)

def show_tile_bounds( location: str, year, time_range, download = True ):
    dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    dataMgr = MWPDataManager( DATA_DIR, dat_url )
    dataMgr.setDefaults(product="2D2OT", download=download, year=year, start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)
    data_arrays: List[xr.DataArray ] =  XGeo.loadRasterFiles(file_paths[0:2], band=1 )
    print( f"Reading location: {location}")
    print( TileLocator.get_bounds(data_arrays[0]) )
    print( TileLocator.infer_tiles_xa( data_arrays[0] ) )

def show_lake_mask_bounds( lake_id: int ):
    lake_mask_file = f"{DATA_DIR}/MOD44W/2005/{lake_id}_2005.tif"
    array: xa.DataArray = xa.open_rasterio( lake_mask_file )
    bounds = TileLocator.get_bounds(array)
    print( f" X Bounds: {bounds[:2]}")
    print( f" Y Bounds: {bounds[2:]}")
    print( TileLocator.infer_tiles_xa(array) )

# show_tile_bounds( "020E020S", 2014, [0, 3] )

# show_lake_mask_bounds( 1295 )

def show_roi( xbounds, ybounds, year, time_range  ):
    dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
    dataMgr = MWPDataManager( DATA_DIR, dat_url )
    dataMgr.setDefaults(product="2D2OT", year=year, start_day=time_range[0], end_day=time_range[1])
    location = TileLocator.get_tile( *xbounds, *ybounds )
    file_paths = dataMgr.get_tile(location)
    roi_bounds = xbounds + ybounds
    time_values = np.array([ get_date_from_filename(os.path.basename(path)) for path in file_paths], dtype='datetime64[ns]')
    cropped_data: xr.DataArray = XRio.load(file_paths, mask=roi_bounds, band=0, index=time_values)
    cropped_data.attrs['cmap'] = dict(colors=colors3)
    animation = SliceAnimation( cropped_data )
    animation.show()

#show_roi( [ 36.582, 36.566 ], [ 42.492, 42.376 ], 2014, [0, 50]  )

show_roi( [ 41, 46 ], [ 31, 36 ], 2015, [0, 50]  )



