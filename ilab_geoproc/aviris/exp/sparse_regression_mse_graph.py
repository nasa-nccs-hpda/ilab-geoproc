import xarray as xa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from typing import List, Union, Tuple, Optional
import os, math, random
from geoproc.aviris.manager import AvirisDataManager

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
n_input_bands = 106
plot_components = False
plot_images = True
n_bins = 16
n_samples_per_bin = 20
n_randomized_tests = 20
selected_bands = [ 104, 87,68, 60, 54, 37, 20 ]

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

sparse_bands = [ (ib,full_comps[0,ib]) for ib in selected_bands ]
sparse_bands.sort( reverse=True, key = lambda x: abs(x[1]) )
mse_plot = []
nbands_plot = []
for nbands in range(1,len(sparse_bands)+1):
    selected_bands_subset = [ sb[0] for sb in sparse_bands[0:nbands] ]
    x_sparse_training = x_binned_training.isel( band=selected_bands_subset )
    sparse_regress_components, mse1, sparse_estimator = mgr.regress( x_sparse_training, y_binned_training )
    print( f"{nbands}: {mse1}  -> {sparse_bands[0:nbands]}")
    nbands_plot.append( nbands )
    mse_plot.append( mse1 )

randomized_tests = []
for iT in range( n_randomized_tests ):
    randomized_sparse_bands = [ *selected_bands ]
    random.shuffle( randomized_sparse_bands )
    mse_rplot = []
    nbands_rplot = []
    for nbands in range(1, len(randomized_sparse_bands) + 1):
        selected_bands_subset = randomized_sparse_bands[0:nbands]
        x_sparse_training = x_binned_training.isel(band=selected_bands_subset)
        sparse_regress_components, mse1, sparse_estimator = mgr.regress(x_sparse_training, y_binned_training)
        print(f"R[{iT}]: {nbands}: {mse1}  -> {selected_bands_subset}")
        nbands_rplot.append(nbands)
        mse_rplot.append(mse1)
    randomized_tests.append( (nbands_rplot, mse_rplot) )

fig, ax = plt.subplots()
ax.set_title('MSE for band subsets', fontsize=16)
ax.set_xlabel('Number of Bands')
ax.set_ylabel('MSE')
ax.plot( nbands_plot, mse_plot, color='blue', lw=2.0 )
for randomized_test in randomized_tests:
    ax.plot( randomized_test[0], randomized_test[1], color=(0.2, 0.2, 0.2, 0.2) )
plt.show()




