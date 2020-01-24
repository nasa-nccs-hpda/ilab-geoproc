import geopandas as gpd
from shapely.geometry import *
from typing import Dict, List, Tuple, Union
import os, time, sys, json
import xarray as xr
import matplotlib.pyplot as plt
from glob import glob
from geoproc.data.mwp import MWPDataManager
from geoproc.plot.animation import SliceAnimation
from geoproc.data.shapefiles import ShapefileManager
from geoproc.cluster.manager import ClusterManager
from geoproc.util.configuration import sanitize, ConfigurableObject as BaseOp
from geoproc.xext.xrio import XRio
from geoproc.xext.xplot import XPlot
import functools
import numpy as np
import os
from dask.distributed import Client, Future, LocalCluster

mask_value = 5
mismatch_value = 6
colors3 = [ ( 0, 'land',  (0, 1, 0) ),
            ( 1, 'undetermined', (1, 1, 0) ),
            ( 2, 'water', (0, 0, 1) ),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ) ]

colors4 = [ ( 0, 'nodata', (0, 0, 0)),
            ( 1, 'land',   (0, 1, 0)),
            ( 2, 'water',  (0, 0, 1)),
            ( 3, 'interp land',   (0, 0.5, 0)),
            ( 4, 'interp water',  (0, 0, 0.5)),
            ( mask_value, 'mask', (0.25, 0.25, 0.25) ),
            ( mismatch_value, 'mismatches', (1, 1, 0) ) ]

mask_value = 5
mask_color = [0.25, 0.25, 0.25]
jet_colors2 = plt.cm.jet(np.linspace(0, 1, 128))
jet_colors2[127] = mask_color + [ 1.0 ]

SHAPEFILE = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp"
DEMs = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/DEM/*.tif"
locations = [ "120W050N", "100W040N" ]
products = [ "1D1OS", "2D2OT", "3D3OT" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
cluster_parameters = {'type': 'local'}
location: str = locations[0]
shpManager = ShapefileManager()
locPoint: Point = shpManager.parseLocation(location)
from multiprocessing import Pool

view_data = False
subset = None
animate = True
plot_dem = True
land_water_thresholds = [ 0.03, 0.95 ]

t0 = time.time()

lake_mask: gpd.GeoSeries = gpd.read_file( SHAPEFILE )
water_prob_maps = []
water_prob_classes = []

def patch_water_map( persistent_classes: xr.DataArray, input_array: xr.DataArray  ) -> xr.DataArray:
    dynamics_mask = persistent_classes.isin( [0] )
    result = input_array.where( dynamics_mask, persistent_classes )
    return result

def patch_water_maps( persistent_classes: xr.DataArray, inputs: xr.DataArray, dynamics_class: int = 0  ) -> xr.DataArray:
    dynamics_mask = persistent_classes.isin( [dynamics_class] )
    result = inputs.where( dynamics_mask, persistent_classes )
    return result

def get_persistent_classes( water_probability: xr.DataArray, thresholds: List[float] ) -> xr.DataArray:
    perm_water_mask = water_probability > thresholds[1]
    perm_land_mask =  water_probability < thresholds[0]
    boundaries_mask = water_probability > 1.0
    return xr.where( boundaries_mask, mask_value,
                     xr.where(perm_water_mask, 2,
                             xr.where(perm_land_mask, 1, 0)))

def get_matching_slice( water_masks: xr.DataArray, match_score: xr.DataArray, current_slice: int ):
    match_score[ current_slice ] = 0
    matching_slice = water_masks[ match_score.argmax() ]
    return matching_slice

def get_match_score( water_mask: xr.DataArray, dynamics_mask: xr.DataArray, current_slice: xr.DataArray, **kwargs ) -> xr.DataArray:
    critical_undef_count = xr.where( dynamics_mask, water_mask==0, False ).count()
    valid_mask = np.logical_and( dynamics_mask, water_mask > 0 )
    match_count = xr.where( valid_mask, water_mask == current_slice, False ).count()
    mismatch_count = xr.where( valid_mask, water_mask != current_slice, False).count()
    return xr.DataArray( [ match_count, mismatch_count, critical_undef_count ] )

def temporal_interpolate( persistent_classes: xr.DataArray, water_masks: xr.DataArray, current_slice_index: int, **kwargs ):
    dynamics_mask = persistent_classes.isin( [1] )
    current_slice = water_masks[current_slice_index].drop_vars( water_masks.dims[0] )
    ms = water_masks.groupby( water_masks.dims[0] ).map( get_match_score, args=( dynamics_mask, current_slice ), **kwargs )
    match_count = ms[:,0]
    mismatch_count = ms[:,1]
    critical_undef_count = ms[:,2]
    match_scores = match_count - mismatch_count - critical_undef_count
    matching_slice = get_matching_slice( water_masks, match_scores, current_slice_index )
    interp_slice: xr.DataArray = current_slice.where( current_slice != 0, matching_slice + 2  )
    water_masks[ current_slice_index ] = interp_slice
    return dict( match_scores=match_scores, interp_water_masks = water_masks, match_count = match_count, mismatch_count=mismatch_count,  critical_undef_count=critical_undef_count )

# dask_client = Client(LocalCluster(n_workers=8))
# with ClusterManager( cluster_parameters ) as clusterMgr:

debug = False
with xr.set_options(keep_attrs=True):

    water_masks_dataset = xr.open_dataset( f"{DATA_DIR}/SaltLake_water_masks.nc" )
    water_masks: xr.DataArray = water_masks_dataset.water_masks
    water_masks.attrs['cmap'] = dict(colors=colors4)
    if debug: water_masks = water_masks[0:3]

    water_probability_dataset = xr.open_dataset(f"{DATA_DIR}/SaltLake_water_probability.nc")
    water_probability: xr.DataArray = water_probability_dataset.water_probability
    water_probability.attrs['cmap'] = dict(colors=jet_colors2)

    persistent_classes: xr.DataArray = get_persistent_classes( water_probability, land_water_thresholds )
    persistent_classes.attrs['cmap'] = dict(colors=colors3)

#    animation = SliceAnimation( [water_probability,persistent_classes], overlays=dict(red=lake_mask.boundary) )
#    animation.show()

    patched_water_maps: xr.DataArray = patch_water_maps( persistent_classes, water_masks )
    patched_water_maps.attrs['cmap'] = dict(colors=colors4)

#    animation = SliceAnimation( [water_masks,patched_water_maps], overlays=dict(red=lake_mask.boundary) )
#    animation.show()

    matchSliceIndex = 2
    ms = temporal_interpolate( persistent_classes, patched_water_maps, matchSliceIndex )

    ms['interp_water_masks'].xplot.animate( overlays=dict(red=lake_mask.boundary),
                                            colors=colors4,
                                            metrics=dict( blue=ms['match_scores'], green=ms['match_count'], red=ms['mismatch_count'], black=ms['critical_undef_count'], markers=dict( cyan=matchSliceIndex ) ),
                                            auxplot=water_masks )



