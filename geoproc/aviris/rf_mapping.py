import xarray as xa
import matplotlib.pyplot as plt
import numpy.ma as ma
import numpy as np
from bathyml.common.data import IterativeTable
from geoproc.plot.animation import SliceAnimation
from framework.estimator.base import EstimatorBase
import os, pickle

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
n_training_samples = 50000
verbose = False
make_plots = True
show_plots = True
modelType =  "rf" #[ "mlp", "rf", "svr", "nnr" ]

parameters = dict(
    mlp=dict( max_iter=500, learning_rate="constant", solver="adam", learning_rate_init=0.05, early_stopping=False,
              validation_fraction = 0.2, activation='identity', hidden_layer_sizes=[], nesterovs_momentum=False ),    # activation='identity'
    rf=dict(n_estimators=50, max_depth=15),
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

    x_data_full = x_dataset.xdata
    y_data_full = y_dataset.ydata

    grouped_data = y_dataset.groupby_bins( 'ydata', 10 )
    for gd in grouped_data:
        print( f"{gd[0]} : {gd[1].ydata.shape}" )
    random_samples = np.random.randint( 0, x_data_full.shape[0], (n_training_samples,) )
    x_data_train = x_data_full.isel( samples=random_samples, drop=True ).values
    y_data_train = y_data_full.isel( samples=random_samples, drop=True ).values
    np_y_data_full = y_data_full.values
    np_x_data_full = x_data_full.values

    modParms = parameters[modelType]
    estimator: EstimatorBase = EstimatorBase.new( modelType )
    estimator.update_parameters( **modParms )
    print( f"Executing {modelType} estimator, parameters: { estimator.instance_parameters.items() } " )
    estimator.fit( x_data_train, y_data_train )
    print( f"Performance {modelType}: ")

    train_prediction = estimator.predict( np_x_data_full )
    mse_train =  mean_squared_error( np_y_data_full, train_prediction )
    print( f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")

    if make_plots:
        fig, ax = plt.subplots(1)
        ax.set_title( f"{modelType} Train Data MSE = {mse_train:.2f} ")
        xaxis = range(train_prediction.shape[0])
        ax.plot(xaxis, np_y_data_full, "b--", label="train data")
        ax.plot(xaxis, train_prediction, "r--", label="prediction")
        ax.legend()
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






