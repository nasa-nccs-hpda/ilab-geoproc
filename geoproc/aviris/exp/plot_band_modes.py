import xarray as xa
import numpy as np
from typing import List, Union, Tuple, Optional
import os, math
from geoproc.aviris.manager import AvirisDataManager

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris/processed/"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170701t182520"
n_input_bands = 106
plot_pca = False
plot_ica = True
plot_regression = True
n_components = 6
n_bins = 16
n_samples_per_bin = 10

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

regress_components, mse = mgr.regress(x_binned_training, y_binned_training )
regress_title = f"Ref, MSE={mse:.2f}"

if plot_ica:
    (np_reduced_data, ica_components, ica_mixing) = mgr.ica( x_binned_training, n_components )
    ica_titles = [ f"C-{iC}" for iC in range( n_components )]

if plot_pca:
    (np_reduced_data, pca_components, explained_variance) = mgr.pca( x_binned_training, n_components )
    pca_titles = [ f"C-{iC}: {evr * 100:.2f}" for (iC,evr) in enumerate(explained_variance.tolist())]

comps = np.vstack( [regress_components.reshape(1,regress_components.size), ica_components ] )
mgr.plot_components( comps, [ regress_title ] + ica_titles )


