import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
import numpy as np
import os, pickle
from geoproc.data.sampling import get_binned_sampling
from sklearn.linear_model import LinearRegression


if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    version = "R2"
    init_weights = None
    modelType = "regression"
    verbose = False
    make_plots = False
    show_plots = False
    nbands = 106
    n_bins = 16
    n_samples_per_bin = 10

    save_weights_file = f"{outDir}/aviris.{modelType}-{version}.pkl"
    parameters = dict(  )

    def get_indices(valid_mask: np.ndarray) -> np.ndarray:
        return np.extract(valid_mask, np.array(range(valid_mask.size)))

    def mean_squared_error(x: np.ndarray, y: np.ndarray):
        diff = x - y
        return np.sqrt(np.mean(diff * diff, axis=0))

    print("Reading Data")
    yTrainFile = os.path.join(outDir, f"{aviris_tile}_Avg-Chl_{version}.nc")
    y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)

    y_data_full = y_dataset.band_data.squeeze().stack(samples=('x', 'y'))
    valid_mask = np.isnan( y_data_full )!= True
    y_data_masked = y_data_full.where(valid_mask, drop=True)
    samples_coord = np.array( range(y_data_masked.shape[0]) )
    y_data = y_data_masked.assign_coords(samples=samples_coord)

    xTrainFile = os.path.join(outDir, f"{aviris_tile}_corr_v2p9_{version}_{nbands}.nc")
    x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)
    x_data_full = x_dataset.band_data.stack(samples=('x', 'y')).transpose()
    x_data = x_data_full.isel(samples=get_indices(valid_mask)).assign_coords( samples=samples_coord )

    x_binned_data, y_binned_data = get_binned_sampling( x_data, y_data, n_bins, n_samples_per_bin )
    x_train_data = x_binned_data.values  # [0:nbands]
    y_train_data = y_binned_data.values  # [0:nbands]

    print(f"Using {y_train_data.size} samples out of {y_data.size}: {(y_train_data.size * 100.0) / y_data.size:.2f}%")

    estimator: LinearRegression = LinearRegression()
    reg = estimator.fit( x_train_data, y_train_data , **parameters )

    train_prediction = estimator.predict( x_data.values )
    mse_train =  mean_squared_error( y_data.values, train_prediction )
    print( f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")

    if save_weights_file:
        filehandler = open(save_weights_file,"wb")
        pickle.dump( estimator.coef_, filehandler )
        print( f"Saved {modelType} Estimator to file {save_weights_file}" )

    if make_plots:
        fig, ax = plt.subplots(2)

        ax[0].set_title( f"{modelType} Train Result MSE = {mse_train:.2f} ")
        xaxis0 = range(train_prediction.shape[0])
        ax[0].plot(xaxis0, y_data.values, color=(0,0,1,0.5), label="train data")
        ax[0].plot(xaxis0, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax[0].legend( loc = 'upper right' )

        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

