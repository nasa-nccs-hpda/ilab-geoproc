import xarray as xa
from typing import List, Union, Tuple, Optional
import numpy as np
import os, pickle, time, math
from geoproc.aviris.manager import AvirisDataManager
from geoproc.aviris.perceptron import LinearPerceptron

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
n_input_bands = 106
n_samples_per_bin = 100

fit_params = dict(
    mse_thresh=0.2,
    sparsity=500.0,
    max_iter=500000,
)

input_file = os.path.join(DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9_img")
target_file = os.path.join(DATA_DIR, f"{aviris_tile}_Avg-Chl.tif")
mgr = AvirisDataManager(n_input_bands)

input_bands: xa.DataArray = mgr.read(input_file)
(norm_input_bands, scaling) = mgr.normalize(input_bands)

nodata_val = int(input_bands.attrs['data_ignore_value'])
target_bands: xa.DataArray = mgr.read(target_file, nodata_val)
(norm_target_bands, target_scaling) = mgr.normalize(target_bands)

x_data_train, y_data_train = mgr.restructure_for_training(norm_input_bands, norm_target_bands)
(x_binned_training, y_binned_training) = mgr.get_binned_sampling(x_data_train, y_data_train, n_samples_per_bin=n_samples_per_bin)
regress_components, mse0, full_estimator = mgr.regress(x_binned_training, y_binned_training)

p = LinearPerceptron(x_binned_training.values, y_binned_training.values)
(w, mse) = p.fit(**fit_params)

comps = np.vstack([regress_components.reshape([1, w.size]), w.reshape([1, w.size])])
mgr.plot_components( comps, ["R", f"S={fit_params['sparsity']:.2f}, MSE={mse:.2f}"], title="Sparse Perceptron Band Weights", highlight=[ 5, 61, 86 ] )

for i, wv in enumerate(w):
    print(f" -- {i}: {wv:.2f}")