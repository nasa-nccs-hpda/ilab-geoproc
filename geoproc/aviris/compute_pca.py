import xarray as xa
import numpy as np
from sklearn.decomposition import PCA
import os

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
aviris_tile = "ang20170714t213741"
target_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_Avg-Chl.nc")
input_file = os.path.join( DATA_DIR, "results", f"{aviris_tile}_corr_v2p9.nc" )
n_components = 6

aviris_dataset: xa.Dataset = xa.open_dataset( input_file )
input_bands = aviris_dataset.band_data
scale = aviris_dataset.scale
components_axis = np.array( range(n_components) )
scale_threshold = 10.0

filtered_input_bands: xa.DataArray = input_bands.where( scale < scale_threshold, drop = True ) if scale_threshold else  input_bands
ny, nx = filtered_input_bands.shape[1], filtered_input_bands.shape[2]
band_axis = filtered_input_bands.band
pca = PCA( n_components=n_components )
pca_input = filtered_input_bands.fillna(0.0).values.reshape( filtered_input_bands.shape[0], nx * ny  ).transpose()
np_reduced_data = pca.fit_transform( pca_input )

component_data = xa.DataArray( pca.components_, coords=dict( component=components_axis, band=band_axis ), dims=['component', 'band'] )
component_data.name = "component_data"

reduced_data = xa.DataArray( np_reduced_data.transpose().reshape(n_components,ny,nx), coords=dict( component= components_axis, y=input_bands.y, x=input_bands.x ), dims=['component', 'y', 'x']  )
scale = np.abs(reduced_data).mean( dim=["x","y"] )
reduced_data_scaled = reduced_data/scale
explained_variance = xa.DataArray( pca.explained_variance_ratio_, coords=dict( component = components_axis ), dims=[ 'component' ] )
explained_variance.name = "explained_variance"

pca_dataset = xa.Dataset( dict(component_data=component_data, reduced_data = reduced_data_scaled, scale=scale, explained_variance=explained_variance ) )
result_file = DATA_DIR + f"/pca-rfl-{n_components}.nc"
print( f"Writing output to {result_file}")
pca_dataset.to_netcdf(result_file)



