import xarray as xa
import numpy as np
from typing import List, Union, Tuple, Optional
import os, math
from geoproc.aviris.manager import AvirisDataManager

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
n_input_bands = 106
plot_components = False
plot_images = True
n_bins = 16
n_samples_per_bin = 20
selected_bands = [ 104, 87,68, 60, 54, 37, 20 ]

input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9_img" )
target_file = os.path.join(DATA_DIR, f"{aviris_tile}_Avg-Chl.tif")
mgr = AvirisDataManager( n_input_bands )

input_bands =  mgr.read( input_file )
(norm_input_bands, scaling) = mgr.normalize( input_bands )

nodata_val = int( input_bands.attrs['data_ignore_value'] )
target_bands = mgr.read(target_file, nodata_val )
(norm_target_bands, target_scaling) = mgr.normalize( target_bands )

x_data_train, y_data_train = mgr.restructure_for_training( norm_input_bands, norm_target_bands )
( x_binned_training, y_binned_training ) = mgr.get_binned_sampling( x_data_train, y_data_train, n_bins, n_samples_per_bin )

regress_components, mse0, full_estimator = mgr.regress(x_binned_training, y_binned_training )
regress_title = f"Ref, MSE={mse0:.2f}"


full_comps = regress_components.reshape(1,regress_components.size)

x_sparse_training = x_binned_training.isel( band=selected_bands )
sparse_regress_components, mse1, sparse_estimator = mgr.regress( x_sparse_training, y_binned_training )

sparse_comps = np.zeros( shape=(1,regress_components.size) )
for iSel in range( len(selected_bands) ):
    sparse_comps[ 0, selected_bands[iSel] ] = sparse_regress_components[iSel]

if plot_components:
    mgr.plot_components( np.vstack([full_comps,sparse_comps]), [ regress_title, f"Sparse Regression, MSE={mse1:.2f}" ], highlight=selected_bands  )

if plot_images:
    dims = norm_target_bands.dims[1:]
    image_xdata = norm_target_bands.stack(samples=dims).transpose()

    sparse_result = sparse_estimator.predict( image_xdata )
    full_result = full_estimator.predict( image_xdata )

    sparse_image: xa.DataArray = xa.DataArray( sparse_result.reshape(image_xdata.shape[1:]), dims=dims, coords=dict(x=image_xdata.x, y=image_xdata.y), name="sparse_regression_image" )
    full_image: xa.DataArray = xa.DataArray( full_result.reshape(image_xdata.shape[1:]), dims=dims, coords=dict(x=image_xdata.x, y=image_xdata.y), name="full_regression_image" )

    print(".")



