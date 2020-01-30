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
land_water_thresholds = [ 0.08, 0.92 ]

def update_metrics( data_array: xr.DataArray, **kwargs ):
    metrics = data_array.attrs.get('metrics', {} )
    metrics.update( **kwargs )
    data_array.attrs['metrics'] = metrics

water_prob_maps = []
water_prob_classes = []

def patch_water_map( persistent_classes: xr.DataArray, input_array: xr.DataArray  ) -> xr.DataArray:
    dynamics_mask = persistent_classes.isin( [0] )
    result = input_array.where( dynamics_mask, persistent_classes )
    return result

def patch_water_maps( persistent_classes: xr.DataArray, inputs: xr.DataArray, dynamics_class: int = 0  ) -> xr.DataArray:
    persistent_classes = persistent_classes.interp_like(water_masks, method='nearest').ffill(persistent_classes.dims[0]).bfill(persistent_classes.dims[0])
    dynamics_mask = persistent_classes.isin( [dynamics_class] )
    result = xr.where( dynamics_mask, inputs, persistent_classes  )
    patched_result: xr.DataArray = result.where( result == inputs, persistent_classes + 2 )
    return patched_result

def get_persistent_classes( water_probability: xr.DataArray, thresholds: List[float] ) -> xr.DataArray:
    perm_water_mask = water_probability > thresholds[1]
    perm_land_mask =  water_probability < thresholds[0]
    boundaries_mask = water_probability > 1.0
    return xr.where( boundaries_mask, mask_value,
                         xr.where(perm_water_mask, 2,
                             xr.where(perm_land_mask, 1, 0)) )

def get_matching_slice( water_masks: xr.DataArray, match_score: xr.DataArray, current_slice: int ):
    match_score[ current_slice ] = 0
    matching_slice = water_masks[ match_score.argmax() ]
    return matching_slice

def temporal_interpolate( persistent_classes: xr.DataArray, water_masks: xr.DataArray, current_slice_index: int, **kwargs ):
    dynamics_mask = persistent_classes == 1
    sdims = water_masks.dims[1:]
    current_slice = water_masks[current_slice_index].drop_vars( water_masks.dims[0] )
    critical_undef_count = xr.where(dynamics_mask, water_masks == 0, 0 ).sum( dim = sdims )
    valid_mask = np.logical_and( dynamics_mask, water_masks > 0 )
    matches = xr.where(valid_mask, water_masks == current_slice, 0)
    match_count = matches.sum( dim = sdims )
    mismatch_count = xr.where( valid_mask, water_masks != current_slice, 0 ).sum( dim = sdims )
    match_scores = match_count - mismatch_count - critical_undef_count
    matching_slice = get_matching_slice( water_masks, match_scores, current_slice_index )
    interp_slice: xr.DataArray = current_slice.where( current_slice != 0, matching_slice + 2  )
    water_masks[ current_slice_index ] = interp_slice
    return dict( match_scores=match_scores, interp_water_masks = water_masks, match_count = match_count, mismatch_count=mismatch_count,  critical_undef_count=critical_undef_count, matches=matches )

def temporal_patch_slice( water_masks: xr.DataArray, slice_index: int, patched_slice=None, patch_slice_index=None  ) -> xr.DataArray:
    current_slice = patched_slice if patched_slice is not None else water_masks[slice_index].drop_vars(water_masks.dims[0])
    undef_Mask: xr.DataArray = ( current_slice == 0 )
    current_patch_slice_index = slice_index - 1 if patch_slice_index is None else patch_slice_index - 1
    if (undef_Mask.count() == 0) or (current_patch_slice_index < 0): return current_slice
    patch_slice = water_masks[ current_patch_slice_index ].drop_vars(water_masks.dims[0])
    recolored_patch_slice = patch_slice.where( patch_slice == 0, patch_slice + 2  )
    current_patched_slice = current_slice.where( current_slice>0, recolored_patch_slice )
    return temporal_patch_slice( water_masks, slice_index, current_patched_slice, current_patch_slice_index )

def temporal_patch( water_masks: xr.DataArray, nProcesses: int = 8  ) -> xr.DataArray:
    slices = list(range( water_masks.shape[0]))
    patcher = functools.partial( temporal_patch_slice, water_masks )
    with Pool(nProcesses) as p:
        patched_slices = p.map( patcher, slices, nProcesses)
        return BaseOp.time_merge( patched_slices, time=water_masks.coords[ water_masks.dims[0] ] )


# dask_client = Client(LocalCluster(n_workers=8))
# with ClusterManager( cluster_parameters ) as clusterMgr:

debug = False
temportal_interp = True
use_previous_patching = False
use_yearly_probabilities = True
view_water_masks = False
view_persistent_classes = False
view_interp_persistent_classes = True

with xr.set_options(keep_attrs=True):

    t0 = time.time()
    lake_mask: gpd.GeoSeries = gpd.read_file(SHAPEFILE)
    water_masks_dataset = xr.open_dataset( f"{DATA_DIR}/SaltLake_water_masks.nc" )
    water_masks: xr.DataArray = water_masks_dataset.water_masks
    water_masks.attrs['cmap'] = dict(colors=colors4)
    space_dims = water_masks.dims[1:]
    if debug: water_masks = water_masks[0:3]

    if view_water_masks:
        animation = SliceAnimation( water_masks, overlays=dict(red=lake_mask.boundary) )
        animation.show()

    if use_previous_patching:
        repatched_water_maps: xr.DataArray = xr.open_dataset(f"{DATA_DIR}/SaltLake_patched_water_masks.nc").water_masks
        repatched_water_maps.attrs['cmap'] = dict(colors=colors4)

    else:
        if use_yearly_probabilities:
            water_probability_dataset = xr.open_dataset(f"{DATA_DIR}/SaltLake_yearly_water_probability.nc")
            water_probability: xr.DataArray = water_probability_dataset.water_probability

        else:
            water_probability_dataset = xr.open_dataset(f"{DATA_DIR}/SaltLake_water_probability.nc")
            water_probability: xr.DataArray = water_probability_dataset.water_probability

        persistent_classes: xr.DataArray = get_persistent_classes( water_probability, land_water_thresholds )
        persistent_classes.attrs['cmap'] = dict(colors=colors3)

        if view_persistent_classes:
            animation = SliceAnimation( [water_probability,persistent_classes], overlays=dict(red=lake_mask.boundary) )
            animation.show()



        patched_water_maps: xr.DataArray = patch_water_maps( persistent_classes, water_masks )

    #    animation = SliceAnimation( [water_masks,patched_water_maps], overlays=dict(red=lake_mask.boundary) )
    #    animation.show()

        repatched_water_maps = temporal_patch( patched_water_maps ) if temportal_interp else patched_water_maps
        result_file = DATA_DIR + ( f"/SaltLake_patched_water_masks.nc" if use_yearly_probabilities else f"/SaltLake_patched_yearly_water_masks.nc" )
        sanitize(repatched_water_maps).to_netcdf( result_file )
        repatched_water_maps.attrs['cmap'] = dict(colors=colors4)


    patched_water_count: xr.DataArray  = (repatched_water_maps == 4).sum( dim=space_dims )
    patched_water_count.name="Patched Water"

    patched_land_count: xr.DataArray  = (repatched_water_maps == 3).sum( dim=space_dims )
    patched_land_count.name="Patched Land"

    print( f"Completed computation in {time.time()-t0} seconds")
    repatched_water_maps.xplot.animate( overlays=dict( red=lake_mask.boundary), auxplot=water_masks, metrics=dict(green=patched_land_count, blue=patched_water_count ) )



