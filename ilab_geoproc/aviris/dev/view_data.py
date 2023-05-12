import xarray as xa
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from geoproc.plot.animation import SliceAnimation
import os

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
version = "R2"
nbands = 106
target_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_Avg-Chl.nc")
input_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_corr_v2p9.nc" )
xTrainFile = os.path.join(outDir, f"{aviris_tile}_corr_v2p9_{version}_{nbands}.nc")

aviris_dataset: xa.DataArray = xa.open_dataset( xTrainFile )
input_bands = aviris_dataset.band_data
input_bands.attrs['cmap'] = dict(range=[-0.1,2])
scale = aviris_dataset.scale
metrics = dict( blue=scale )

target_dataset: xa.DataArray = xa.open_dataset( target_file )
target_band: xa.DataArray = target_dataset.band_data
target_band.attrs['cmap'] = dict(range=[0,5])

animation = SliceAnimation(input_bands ) # , auxplot=target_band, metrics=metrics, metrics_scale="log" )
animation.invert_yaxis()
animation.show()


