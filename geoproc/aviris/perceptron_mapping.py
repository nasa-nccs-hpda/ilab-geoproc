import xarray as xa
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Union
from geoproc.data.sampling import get_binned_sampling
from framework.estimator.base import EstimatorBase
from geoproc.aviris.perceptron import LinearPerceptron
import os, sys, pickle

def get_indices(valid_mask: np.ndarray) -> np.ndarray:
    return np.extract(valid_mask, np.array(range(valid_mask.size)))

def mean_squared_error(x: np.ndarray, y: np.ndarray):
    diff = x - y
    return np.sqrt(np.mean(diff * diff, axis=0))

if __name__ == '__main__':

    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    version = "R2"
    modelType = "perceptron"

    n_iter = 100000
    nbands = 106
    n_bins = 16
    n_samples_per_bin = 10

    print("Reading Data")
    yTrainFile = os.path.join(outDir, f"{aviris_tile}_Avg-Chl_{version}.nc")
    y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)

    y_data_full = y_dataset.band_data.squeeze().stack(samples=('y', 'x'))
    valid_mask = np.isnan( y_data_full )!= True
    y_data_masked = y_data_full.where(valid_mask, drop=True)
    samples_coord = np.array( range(y_data_masked.shape[0]) )
    y_data = y_data_masked.assign_coords(samples=samples_coord)

    xTrainFile = os.path.join(outDir, f"{aviris_tile}_corr_v2p9_{version}_{nbands}.nc")
    x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)
    x_data_raw = x_dataset.band_data
    x_data_full = x_data_raw.stack(samples=('y', 'x')).transpose()
    x_data = x_data_full.isel(samples=get_indices(valid_mask)).assign_coords( samples=samples_coord )

    x_binned_data, y_binned_data = get_binned_sampling( x_data, y_data, n_bins, n_samples_per_bin )
    x_data_train = x_binned_data.values
    y_data_train = y_binned_data.values

    save_weights_file = f"{outDir}/aviris.perceptron-{version}-{n_samples_per_bin}-{n_iter}-0.pkl"
    init_weights = pickle.load( open(save_weights_file,"rb") )
    estimator: LinearPerceptron = LinearPerceptron(weights=init_weights)

    x_valid_mask = valid_mask.values.reshape([valid_mask.shape[0], 1])
    image_xdata =  np.where( x_valid_mask, x_data_full.values, 0.0 )
    result_image = estimator.predict( image_xdata )
    image_prediction = np.where( x_valid_mask.squeeze(), result_image, np.nan )
    constructed_image: xa.DataArray = xa.DataArray( image_prediction.reshape(x_data_raw.shape[1:]), dims=['y', 'x'], coords=dict(x=x_data_raw.x, y=x_data_raw.y), name="constructed_image" )
    save_image_file = f"{outDir}/aviris-image.{modelType}-{version}-{n_samples_per_bin}.nc"
    print(f"Saving constructed_image to {save_image_file} ")
    constructed_image.to_netcdf( save_image_file )








