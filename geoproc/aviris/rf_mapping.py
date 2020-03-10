import xarray as xa
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Union
from geoproc.data.sampling import get_binned_sampling
from framework.estimator.base import EstimatorBase
import os, sys, pickle

parameters = dict(
    mlp=dict( max_iter=500, learning_rate="constant", solver="adam", learning_rate_init=0.05, early_stopping=False,
              validation_fraction = 0.2, activation='identity', hidden_layer_sizes=[], nesterovs_momentum=False ),    # activation='identity'
    rf=dict( n_estimators=100, max_depth=20 ),
    svr=dict(C=5.0, gamma=0.5, cache_size=2000 ),
    nnr=dict( n_neighbors=3, weights='distance', algorithm = 'kd_tree', leaf_size=30, metric="euclidean", n_jobs=8 ),
)

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
    modelType = "rf"
    init_weights = None
    verbose = False
    make_plots = False
    plot_image = True
    show_plots = False
    nbands = 106
    n_bins = 16
    n_samples_per_bin = 250

    save_weights_file = f"{outDir}/aviris.{modelType}-{version}-{n_samples_per_bin}.pkl"

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

    modParms = parameters[modelType]
    estimator: EstimatorBase = EstimatorBase.new( modelType )
    estimator.update_parameters( **modParms )
    print( f"Executing {modelType} estimator, parameters: { estimator.instance_parameters.items() } " )
    ts_percent = (y_data_train.size*100.0)/y_data.size
    print(f"Using {y_data_train.size} samples out of {y_data.size}: {ts_percent:.3f}%")
    estimator.fit( x_data_train, y_data_train )
    print( f"Performance {modelType}: ")

    train_prediction = estimator.predict( x_data.values )
    mse_train =  mean_squared_error( y_data.values, train_prediction )
    print(f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")

    if plot_image:
        x_valid_mask = valid_mask.values.reshape([valid_mask.shape[0], 1])
        image_xdata =  np.where( x_valid_mask, x_data_full.values, 0.0 )
        result_image = estimator.predict( image_xdata )
        image_prediction = np.where( x_valid_mask.squeeze(), result_image, np.nan )
        constructed_image: xa.DataArray = xa.DataArray( image_prediction.reshape(x_data_raw.shape[1:]), dims=['y', 'x'], coords=dict(x=x_data_raw.x, y=x_data_raw.y), name="constructed_image" )
        save_image_file = f"{outDir}/aviris-image.{modelType}-{version}-{n_samples_per_bin}.nc"
        print(f"Saving constructed_image to {save_image_file} ")
        constructed_image.to_netcdf( save_image_file )

    if make_plots:
        fig, ax = plt.subplots(1)
        ax.set_title( f"{modelType}: {ts_percent:.3f}% samples, MSE={mse_train:.2f} ")
        xaxis = range(train_prediction.shape[0])
        ax.plot(xaxis, y_data.values, color=(0,0,1,0.5), label="train data")
        ax.plot(xaxis, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax.legend( loc = 'upper right' )
        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}-{y_data_train.size}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

    filehandler = open(save_weights_file, "wb")
    pickle.dump(estimator.instance.feature_importances_, filehandler)
    print(f"Saved {modelType} Estimator to file {save_weights_file}")






