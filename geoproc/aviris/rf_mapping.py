import xarray as xa
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Union
from geoproc.data.sampling import get_binned_sampling
from framework.estimator.base import EstimatorBase
import os, sys, pickle

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
n_bins = 50
n_samples_per_bin = 500
verbose = False
make_plots = True
show_plots = True
modelType =  "rf" #[ "mlp", "rf", "svr", "nnr" ]

parameters = dict(
    mlp=dict( max_iter=500, learning_rate="constant", solver="adam", learning_rate_init=0.05, early_stopping=False,
              validation_fraction = 0.2, activation='identity', hidden_layer_sizes=[], nesterovs_momentum=False ),    # activation='identity'
    rf=dict(n_estimators=50, max_depth=20),
    svr=dict(C=5.0, gamma=0.5, cache_size=2000 ),
    nnr=dict( n_neighbors=3, weights='distance', algorithm = 'kd_tree', leaf_size=30, metric="euclidean", n_jobs=8 ),
)

def get_indices( valid_mask: np.ndarray ) -> np.ndarray:
    return np.extract( valid_mask, np.array( range( valid_mask.size ) )  )

def mean_squared_error( x: np.ndarray, y: np.ndarray ):
    diff =  x-y
    return np.sqrt( np.mean( diff*diff, axis=0 ) )

if __name__ == '__main__':
    print("Reading Data")

    xTrainFile = os.path.join(outDir, f"{aviris_tile}_xtrain_full.nc")
    yTrainFile = os.path.join(outDir, f"{aviris_tile}_ytrain_full.nc")
    y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)
    x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)

    x_data_train, y_data_train = get_binned_sampling( x_dataset.xdata,  y_dataset.ydata, n_bins, n_samples_per_bin )
    modParms = parameters[modelType]
    estimator: EstimatorBase = EstimatorBase.new( modelType )
    estimator.update_parameters( **modParms )
    print( f"Executing {modelType} estimator, parameters: { estimator.instance_parameters.items() } " )
    print(f"Using {y_data_train.size} samples out of {y_dataset.ydata.size} ")
    estimator.fit( x_data_train.values, y_data_train.values )
    print( f"Performance {modelType}: ")

    train_prediction = estimator.predict( x_dataset.xdata.values )
    mse_train =  mean_squared_error( y_dataset.ydata.values, train_prediction )
    print( f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")

    if make_plots:
        fig, ax = plt.subplots(1)
        ax.set_title( f"{modelType} Train Data MSE = {mse_train:.2f} ")
        xaxis = range(train_prediction.shape[0])
        ax.plot(xaxis, y_dataset.ydata.values, color=(0,0,1,0.5), label="train data")
        ax.plot(xaxis, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax.legend( loc = 'upper right' )
        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

    saved_model_path = os.path.join( outDir, f"aviris.model.{modelType}.pkl")
    filehandler = open(saved_model_path,"wb")
    pickle.dump( estimator, filehandler )
    print( f"Saved {modelType} Estimator to file {saved_model_path}" )






