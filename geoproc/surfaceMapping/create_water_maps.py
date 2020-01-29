import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
import os, time, sys
import xarray as xr
from glob import glob
from geoproc.surfaceMapping.lakes import WaterMapGenerator
from geoproc.data.mwp import MWPDataManager
from geoproc.data.shapefiles import ShapefileManager
from geoproc.xext.xrio import XRio
from geoproc.util.configuration import sanitize, ConfigurableObject as BaseOp
from geoproc.plot.animation import SliceAnimation
import matplotlib.pyplot as plt
import numpy as np
from geoproc.xext.xplot import XPlot
import os

mask_value = 5
mismatch_value = 6
mask_color = [0.25, 0.25, 0.25]
jet_colors2 = plt.cm.jet(np.linspace(0, 1, 128))
jet_colors2[127] = mask_color + [ 1.0 ]

colors3 = [ ( 0, 'undetermined', (1, 1, 0) ),
            ( 1, 'land',  (0, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ) ]

colors4 = [ ( 0, 'nodata', (0, 0, 0)),
            ( 1, 'land',   (0, 1, 0)),
            ( 2, 'water',  (0, 0, 1)),
            ( 3, 'interp land',   (0, 0.5, 0)),
            ( 4, 'interp water',  (0, 0, 0.5)),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ),
            ( mismatch_value, 'mismatches', (1, 1, 0) ) ]

debug = False
SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
dat_url = "https://floodmap.modaps.eosdis.nasa.gov/Products"
savePath = DATA_DIR + "/LakeMap_counts_diagnostic_animation.gif"
location: str = locations[0]
product: str = products[1]
year_range = ( 2018, 2020 ) if debug else ( 2014, 2020 )
download = True
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
threshold = 0.5
binSize = 8

resolution = (250,250)
time_range = [0,40] if debug else [0,360]
land_water_thresholds = [ 0.08, 0.92 ]

use_existing_water_masks = None
use_existing_cropped_data = True
show_water_probability = True
use_existing_water_probability = False

def get_date_from_filename( filename: str ):
    from datetime import datetime
    toks = filename.split("_")
    result = datetime.strptime( toks[1], '%Y%j').date()
    return np.datetime64(result)

def get_persistent_classes( water_probability: xr.DataArray, thresholds: List[float] ) -> xr.DataArray:
    perm_water_mask = water_probability > thresholds[1]
    perm_land_mask =  water_probability < thresholds[0]
    boundaries_mask = water_probability > 1.0
    return xr.where( boundaries_mask, mask_value,
                         xr.where(perm_water_mask, 2,
                             xr.where(perm_land_mask, 1, 0)) )

def get_water_prob( cropped_data, yearly = False ):
    from datetime import datetime
    water = cropped_data.isin( [2,3] )
    land = cropped_data.isin( [1] )
    masked = cropped_data[0].isin( [mask_value] ).drop_vars( cropped_data.dims[0] )
    if yearly:
        water_cnts = water.groupby("time.year").sum()
        land_cnts  = land.groupby("time.year").sum()
    else:
        water_cnts = water.sum(axis=0)
        land_cnts = land.sum(axis=0)
    visible_cnts = (water_cnts + land_cnts)
    water_prob: xr.DataArray = water_cnts / visible_cnts
    water_prob = water_prob.where( masked == False, 1.01 )
    water_prob.name = "water_probability"
    if yearly:
        time_values = np.array( [ np.datetime64( datetime( year, 7, 1 ) ) for year in water_prob.year.data ], dtype='datetime64[ns]' )
        water_prob = water_prob.assign_coords( year=time_values ).rename( year='time' )
    return water_prob

lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )

cropped_data_file = DATA_DIR + f"/SaltLake_cropped_data.nc"
if use_existing_cropped_data:

    cropped_data_dataset: xr.Dataset = xr.open_dataset(cropped_data_file)
    cropped_data: xr.DataArray = cropped_data_dataset.cropped_data
    cropped_data.attrs['cmap'] = dict(colors=colors4)
else:
    dataMgr = MWPDataManager(DATA_DIR, dat_url)
    dataMgr.setDefaults(product=product, download=download, years=range(*year_range), start_day=time_range[0], end_day=time_range[1])
    file_paths = dataMgr.get_tile(location)

    dem_arrays: List[xr.DataArray] = dataMgr.get_array_data( glob( DEMs ) )
    dem_array: xr.DataArray = dem_arrays[0]
    xc=dem_array.coords['x']
    yc=dem_array.coords['y']

    time_values = np.array( [ get_date_from_filename( os.path.basename(path) ) for path in file_paths ], dtype='datetime64[ns]' )
    cropped_data: xr.DataArray = XRio.load( file_paths, mask = lake_mask, band=0, mask_value=mask_value, index=time_values )

    cropped_data_dset = xr.Dataset(dict(cropped_data=sanitize(cropped_data)))
    cropped_data_dset.to_netcdf(cropped_data_file)
    print(f"Saved cropped_data to {cropped_data_file}")

if show_water_probability:

    yearly = True
    water_probability_file = DATA_DIR + ( f"/SaltLake_yearly_water_probability.nc" if yearly else f"/SaltLake_water_probability.nc" )

    if use_existing_water_probability:
        water_probability_dataset: xr.Dataset = xr.open_dataset(water_probability_file)
        water_probability: xr.DataArray = water_probability_dataset.water_probability
    else:
        water_probability = get_water_prob(cropped_data, yearly)
        result = xr.Dataset(dict(water_probability=sanitize(water_probability)))
        result.to_netcdf( water_probability_file )
        print( f"Saved water_probability to {water_probability_file}")

    persistent_classes = get_persistent_classes( water_probability, land_water_thresholds )
    persistent_classes.attrs['cmap'] = dict(colors=colors3)
    water_probability.attrs['cmap'] = dict(colors=jet_colors2)

    animation = SliceAnimation( [ water_probability, persistent_classes ], overlays=dict( red=lake_mask.boundary ) )
    animation.show()

if use_existing_water_masks is not None:
    if use_existing_water_masks:
        result_file = DATA_DIR + f"/SaltLake_water_masks.nc"
        water_masks_dataset: xr.Dataset = xr.open_dataset(result_file)
        water_masks: xr.DataArray = water_masks_dataset.water_masks
    else:
        waterMapGenerator = WaterMapGenerator()
        masking_results = waterMapGenerator.get_water_masks( cropped_data, binSize, threshold, mask_value )
        water_masks: xr.DataArray = masking_results["mask"]

        result = xr.Dataset(dict(water_masks=sanitize(water_masks)))
        result_file = DATA_DIR + f"/SaltLake_water_masks.nc"
        result.to_netcdf(result_file)
        print(f"Saved water_masks to {result_file}")

