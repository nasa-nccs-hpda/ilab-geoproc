import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
import os, time, sys, json, functools
import xarray as xr
import matplotlib.pyplot as plt
from geoproc.xext.xrio import XRio
import pandas as pd
from glob import glob
from geoproc.plot.animation import SliceAnimation
from geoproc.data.shapefiles import ShapefileManager
from geoproc.util.configuration import sanitize, ConfigurableObject as BaseOp
import numpy as np
import os, collections

mask_data_value = 256
mask_value = 3
mask_color = [0.25, 0.25, 0.25]
colors = [  ( 0, 'land',    (0, 1, 0)),
            ( 1, 'water',   (0, 0, 1)),
            ( mask_value, 'mask',  mask_color) ]

jet_colors2 = plt.cm.jet(np.linspace(0, 1, 128))
jet_colors2[127] = mask_color + [ 1.0 ]

colors3 = [ ( 0, 'undetermined', (1, 1, 0) ),
            ( 1, 'land',  (0, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ) ]

land_water_thresholds = [ 0.03, 0.95 ]
lake_index = 19
spatial_precision = None

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
cluster_parameters = {'type': 'local'}
location: str = locations[0]
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)

lake_mask: gpd.GeoSeries = gpd.read_file(SHAPEFILE)
use_netcdf = True
view_masks = False

def fuzzy_where( cond: xr.DataArray, x, y, join="left" ) -> xr.DataArray:
    from xarray.core import duck_array_ops
    return xr.apply_ufunc( duck_array_ops.where, cond, x, y, join=join, dataset_join=join, dask="allowed" )

def get_date_from_year( year: int ):
    from datetime import datetime
    result = datetime( year, 1, 1 )
    return np.datetime64(result)

def read_lake_mask_geotifs( file_path, **kwargs ):
    images = {}
    precision = kwargs.get('precision', None)
    for sdir in glob( file_path ):
        year = os.path.basename(sdir)
        filepath = f"{DATA_DIR}/MOD44W/{year}/lake{lake_index}_{year}.tif"
        images[int(year)] = filepath
    sorted_file_paths = collections.OrderedDict(sorted(images.items()))

    time_values = np.array([get_date_from_year(year) for year in sorted_file_paths.keys()], dtype='datetime64[ns]')
    yearly_lake_masks: xr.DataArray = XRio.load( list(sorted_file_paths.values()), mask = lake_mask, band=0, mask_value=mask_data_value, index=time_values )
    yearly_lake_masks = set_spatial_precision(yearly_lake_masks, precision)

    result = xr.Dataset(dict(yearly_lake_masks=sanitize(yearly_lake_masks)))
    result_file = DATA_DIR + f"/SaltLake_fill_masks.nc"
    result.to_netcdf(result_file)
    print(f"Saved cropped_data to {result_file}")
    return yearly_lake_masks

def set_spatial_precision( array: xr.DataArray, precision: int ) -> xr.DataArray:
    if precision is None: return array
    sdims = [ array.dims[-2], array.dims[-1] ]
    rounded_coords = { dim: array.coords[dim].round( precision ) for dim in sdims }
    return array.assign_coords( rounded_coords )

def get_permanent_water_mask( **kwargs ) -> xr.DataArray:
    threshold = kwargs.get( 'threshold', 0.95 )
    precision = kwargs.get( 'precision', None )
    grid = kwargs.get( 'grid', None )
    water_probability_dataset = xr.open_dataset(f"{DATA_DIR}/SaltLake_water_probability.nc")
    water_probability: xr.DataArray = water_probability_dataset.water_probability
    water_probability = water_probability if grid is None else water_probability.interp_like( grid )
    water_probability = set_spatial_precision( water_probability, precision )
    perm_water_mask: xr.DataArray = water_probability > threshold
    return perm_water_mask

def get_water_prob( cropped_data ):
    water = cropped_data == 1
    land = cropped_data == 0
    masked = cropped_data[0].isin( [ mask_data_value ] ).drop_vars( cropped_data.dims[0] )
    water_cnts = water.sum(axis=0)
    land_cnts = land.sum(axis=0)
    visible_cnts = (water_cnts + land_cnts)
    water_prob: xr.DataArray = xr.where(masked, 1.01, water_cnts / visible_cnts)
    water_prob.attrs = cropped_data.attrs
    water_prob.name = "WaterProbability"
    return water_prob

def get_persistent_classes( yearly_lake_masks: xr.DataArray, water_probability: xr.DataArray, **kwargs  ) -> xr.DataArray:
    perm_water_mask = get_permanent_water_mask( grid=yearly_lake_masks, **kwargs )
    boundaries_mask = water_probability > 1.0
    apply_thresholds_partial = functools.partial( apply_thresholds, boundaries_mask,  perm_water_mask )
    return yearly_lake_masks.groupby(yearly_lake_masks.dims[0]).map( apply_thresholds_partial )

def apply_thresholds( boundaries_mask: xr.DataArray, perm_water_mask: xr.DataArray, yearly_lake_mask: xr.DataArray ) -> xr.DataArray:
    perm_land_mask: xr.DataArray =  ( yearly_lake_mask == 0 )
    return xr.where( boundaries_mask, mask_value,
                xr.where(perm_water_mask, 2,
                    xr.where( perm_land_mask, 1, 0)) )

def read_lake_mask_netcdf( file_path, **kwargs ):
    precision = kwargs.get('precision', None)
    image_dataset: xr.Dataset = xr.open_dataset(file_path)
    yearly_lake_masks: xr.DataArray = image_dataset.yearly_lake_masks
    result =  set_spatial_precision( yearly_lake_masks, precision )
    return result

with xr.set_options(keep_attrs=True):

    t0 = time.time()

    if use_netcdf:
        yearly_lake_masks: xr.DataArray =  read_lake_mask_netcdf(  f"{DATA_DIR}/SaltLake_fill_masks.nc", precision=spatial_precision )
    else:
        yearly_lake_masks: xr.DataArray =  read_lake_mask_geotifs( f"{DATA_DIR}/MOD44W/*", precision=spatial_precision )

    yearly_lake_masks.attrs['cmap'] = dict(colors=colors)

    if view_masks:
        lake_extent = (yearly_lake_masks == 1).sum( dim=yearly_lake_masks.dims[1:] )
        lake_extent.name = "Water Extent"
        land_extent = (yearly_lake_masks == 0).sum( dim=yearly_lake_masks.dims[1:] )
        land_extent.name = "Land Extent"

        animation = SliceAnimation( yearly_lake_masks, overlays=dict(red=lake_mask.boundary), metrics=dict( blue=lake_extent, green=land_extent ) )
        animation.show()

    else:
        water_probability = get_water_prob( yearly_lake_masks )
        water_probability.attrs['cmap'] = dict(colors=jet_colors2)

        persistent_classes = get_persistent_classes( yearly_lake_masks, water_probability, precision=spatial_precision )
        persistent_classes.attrs['cmap'] = dict(colors=colors3)
        persistent_classes.name = "YearlyInterpClasses"

        result_file = DATA_DIR + f"/SaltLake_YearlyInterpClasses.nc"
        sanitize(persistent_classes).to_netcdf(result_file)

        animation = SliceAnimation( [ yearly_lake_masks, persistent_classes ], overlays=dict(red=lake_mask.boundary) )
        animation.show()