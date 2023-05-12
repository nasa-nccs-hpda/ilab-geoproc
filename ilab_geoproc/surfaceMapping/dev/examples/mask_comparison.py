from geoproc.plot.animation import SliceAnimation
from typing import List, Union, Tuple, Dict, Optional
import yaml, os, xarray as xa
import geopandas as gpd
import pandas as pd

data_dir= "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
mask_value = 5
water_map_colors = dict( colors =
            [ (0, 'nodata', (0, 0, 0)),
              (1, 'land', (0, 1, 0)),
              (2, 'water', (0, 0, 1)),
              (3, 'int-land', (0, 0.6, 0)),
              (4, 'int-water', (0, 0, 0.6)),
              (mask_value, 'mask', (1, 1, 0.7)) ] )

water_maps_file = os.path.join( data_dir, "saltlakemasked_water_maps.nc")
water_maps: xa.Dataset = xa.open_dataset( water_maps_file ).water_maps
water_maps.name = "water_maps"
water_maps.attrs['cmap'] = water_map_colors

water_maps_with_mask_file = os.path.join( data_dir, "saltlakemasked_patched_water_masks.nc")
water_maps_with_mask: xa.DataArray = xa.open_dataset( water_maps_with_mask_file ).Water_Maps
water_maps_with_mask.name = "water_maps_with_mask_file"

water_maps_without_mask_file = os.path.join( data_dir, "saltlakemasked_patched_water_masks.nc")
water_maps_without_mask: xa.DataArray = xa.open_dataset( water_maps_without_mask_file ).Water_Maps
water_maps_without_mask.name = "water_maps_without_mask"

roi = '/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt/saltLake/GreatSalt.shp'
lake_mask: gpd.GeoSeries = gpd.read_file(roi)

animation = SliceAnimation( [ water_maps_with_mask, water_maps_without_mask, water_maps ], overlays=dict(red=lake_mask.boundary) )
animation.show()