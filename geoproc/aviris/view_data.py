import xarray as xa
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from geoproc.plot.animation import SliceAnimation
import os

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
aviris_tile = "ang20170714t213741"
target_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_Avg-Chl.nc")
input_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_rdn_v2p9.nc" )

aviris_dataset: xa.DataArray = xa.open_dataset( input_file )
input_bands = aviris_dataset.band_data
input_bands.attrs['cmap'] = dict(range=[-2,2])
median = input_bands.median( dim=['x','y'] )*5
median.name = "median"
metrics = dict( blue=aviris_dataset.scale, red=aviris_dataset.center, green=aviris_dataset.range, black= median )

target_dataset: xa.DataArray = xa.open_dataset( target_file )
target_band: xa.DataArray = target_dataset.band_data
target_band.attrs['cmap'] = dict(range=[0,5])

animation = SliceAnimation(input_bands, auxplot=target_band, metrics=metrics )
animation.invert_yaxis()
animation.show()


