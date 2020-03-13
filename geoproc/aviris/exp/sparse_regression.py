import xarray as xa
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
import os, math
from geoproc.aviris.manager import AvirisDataManager

def post_process( image, iattrs ):
    centered_image = image - image.mean()
    result = centered_image / centered_image.std()
    result.attrs.update( iattrs )
    return result

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
n_input_bands = 106
plot_components = True
plot_images = True
n_bins = 16
n_samples_per_bin = 20
full_selected_bands = [ 104, 87,68, 60, 54, 37, 20 ]
selected_bands = [ 68, 104, 87 ]
selected_band_stats = [ (68, -1.1257342), (104, -0.9761612), (87, 0.5391385), (54, -0.14595145), (37, 0.14316636), (20, -0.04348179), (60, 0.079601854) ]

input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9_img" )
target_file = os.path.join(DATA_DIR, f"{aviris_tile}_Avg-Chl.tif")
mgr = AvirisDataManager( n_input_bands )

input_bands: xa.DataArray =  mgr.read( input_file )
(norm_input_bands, scaling) = mgr.normalize( input_bands )

nodata_val = int( input_bands.attrs['data_ignore_value'] )
target_bands: xa.DataArray = mgr.read(target_file, nodata_val )
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
    idims = norm_target_bands.dims[1:]
    icoords = { idims[i]: norm_input_bands.coords[idims[i]] for i in [0,1] }
    ishape = norm_input_bands.shape[1:]
    iattrs = dict( transform = input_bands.transform, crs = input_bands.crs )

    image_xdata = norm_input_bands.stack(samples=idims).transpose()
    predict_input = image_xdata.fillna(0.0)

    sparse_result = sparse_estimator.predict( predict_input.isel( band=selected_bands ).values )
    full_result = full_estimator.predict( predict_input.values )

    sparse_image: xa.DataArray = post_process( xa.DataArray( sparse_result.reshape(ishape), dims=idims, coords=icoords, name="sparse_regression_image" ), iattrs )
    full_image: xa.DataArray = post_process( xa.DataArray( full_result.reshape(ishape), dims=idims, coords=icoords, name="full_regression_image" ), iattrs )

    fig, ax = plt.subplots(2)
    sparse_image.plot.imshow( ax=ax[1], yincrease=False, cmap="jet", vmin=-3, vmax=3 )
    full_image.plot.imshow( ax=ax[0], yincrease=False, cmap="jet", vmin=-3, vmax=3 )
    plt.show()



