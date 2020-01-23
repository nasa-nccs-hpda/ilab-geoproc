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
    land_mask = persistent_classes == 0
    water_mask = persistent_classes == 2
    persistent_class_map = land_mask + water_mask
    result = persistent_classes.where( persistent_class_map, input_array )
    return result

def patch_water_maps_dask( persistent_classes: xr.DataArray, inputs: xr.DataArray  ) -> xr.DataArray:
    patch_func = functools.partial(patch_water_map,persistent_classes)
    return xr.apply_ufunc( patch_func, inputs, input_core_dims= [ [inputs.dims[0]], ] )

def patch_water_maps_mp( persistent_classes: xr.DataArray, inputs: xr.DataArray, nProcesses: int = 8  ) -> xr.DataArray:
    slices = [ slice.reset_coords(inputs.dims[0]).variables[slice.name] for slice in inputs ]
    patch_func = functools.partial(patch_water_map, persistent_classes)
    with Pool(nProcesses) as p:
        patched_slices = p.map( patch_func, slices, nProcesses )
    return BaseOp.time_merge( patched_slices, dim="frames" )

def get_persistent_classes( water_probability: xr.DataArray, thresholds: List[float] ) -> xr.DataArray:
    return xr.where(water_probability > 1.0, mask_value, xr.where(water_probability > thresholds[1], 2, (water_probability > thresholds[0])))


# dask_client = Client(LocalCluster(n_workers=8))
# with ClusterManager( cluster_parameters ) as clusterMgr:
with xr.set_options(keep_attrs=True):

    water_masks_dataset = xr.open_dataset( f"{DATA_DIR}/SaltLake_water_masks.nc" )
    water_masks: xr.DataArray = water_masks_dataset.water_masks
    water_masks.attrs['cmap'] = dict(colors=colors4)

    water_probability_dataset = xr.open_dataset(f"{DATA_DIR}/SaltLake_water_probability.nc")
    water_probability: xr.DataArray = water_probability_dataset.water_probability
    water_probability.attrs['cmap'] = dict(colors=jet_colors2)

    persistent_classes: xr.DataArray = get_persistent_classes( water_probability, land_water_thresholds )
    persistent_classes.attrs['cmap'] = dict(colors=colors3)

#    animation = SliceAnimation( [water_probability,persistent_classes], overlays=dict(red=lake_mask.boundary) )
#    animation.show()

    patched_water_maps: xr.DataArray = patch_water_maps_mp( persistent_classes, water_masks )
    patched_water_maps.attrs['cmap'] = dict(colors=colors4)

    animation = SliceAnimation( [water_masks,patched_water_maps], overlays=dict(red=lake_mask.boundary) )
    animation.show()

 #    thresholded_map: xr.DataArray = xr.where(  masked, mask_value, xr.where( water_prob > land_water_thresholds[1], 2, (water_prob > land_water_thresholds[0]) ) )

#    water_prob_maps.append( water_prob )
#    water_prob_classes.append( thresholded_map )


#     water_prob_map: xr.DataArray = BaseOp.time_merge(water_prob_maps)
#     water_prob_map.name = "WaterProbablity"
#     water_prob_map.attrs['cmap'] = json.dumps( dict( cmap = "jet" ) )
#  #   water_prob_map.xgeo.to_tif( DATA_DIR + f"/WaterProbabilityMap.tif" )
#
#     water_prob_class = BaseOp.time_merge(water_prob_classes)
#     water_prob_class.name = "Classification"
#     water_prob_class.attrs['cmap'] = json.dumps( dict( colors = colors3 ) )
#  #   water_prob_class.xgeo.to_tif( DATA_DIR + f"/WaterProbabilityClasses.tif" )
#
#     print( f'Completed computation in {(time.time()-t0)/60.0} mins')
#
# #    animation = SliceAnimation( [water_prob_map,water_prob_class], overlays=dict(red=lake_mask.boundary) )
# #    animation.show()
#
