import xarray as xa
from geoproc.plot.animation import SliceAnimation
import os

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
aviris_tile = "ang20170714t213741"
target_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_Avg-Chl.nc")
n_components = 6
components_file = DATA_DIR + f"/pca-{n_components}.nc"
cmap_range = [-2,2]

pca_dataset: xa.Dataset = xa.open_dataset( components_file )
component_data: xa.DataArray = pca_dataset.component_data
reduced_data: xa.DataArray = pca_dataset.reduced_data
scale: xa.DataArray = pca_dataset.scale
explained_variance: xa.DataArray = pca_dataset.explained_variance
reduced_data.attrs['cmap'] = dict( range=cmap_range )
metrics = dict( blue = explained_variance )

target_dataset: xa.DataArray = xa.open_dataset( target_file )
target_band: xa.DataArray = target_dataset.band_data
target_band.attrs['cmap'] = dict(range=[0,5])

animation = SliceAnimation( reduced_data, auxplot=target_band, metrics=metrics )
animation.invert_yaxis()
animation.show()


