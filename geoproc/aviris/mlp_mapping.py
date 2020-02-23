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
n_components = 6
version = "T1"
center_threshold = 0.02
verbose = False
make_plots = True
show_plots = True
modelType =  "mlp" #[ "mlp", "rf", "svr", "nnr" ]
usePCA = False

parameters = dict(
    mlp=dict( max_iter=1000, learning_rate="constant", solver="sgd", learning_rate_init=0.05, early_stopping=False,
              validation_fraction = 0.2, activation='identity', hidden_layer_sizes=[] ),
    rf=dict(n_estimators=70, max_depth=20),
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

    target_file = os.path.join(DATA_DIR, "results", f"{aviris_tile}_Avg-Chl.nc")
    target_dataset: xa.DataArray = xa.open_dataset(target_file)
    y_data_full: np.ndarray = target_dataset.band_data.squeeze().stack( samples=('x', 'y') )
    valid_mask: np.ndarray = np.isnan(y_data_full) != True
    y_data_filtered = y_data_full.where( valid_mask, drop = True )

    if usePCA:
        pca_dataset_file = DATA_DIR + f"/pca-{n_components}.nc"
        pca_dataset: xa.Dataset = xa.open_dataset(pca_dataset_file)
        train_data_full: xa.DataArray = pca_dataset.reduced_data.stack( samples=('x', 'y') ).transpose()
        train_data_filtered = train_data_full.isel( samples=get_indices( valid_mask ) )
    else:
        input_file = os.path.join(DATA_DIR, "results", f"{aviris_tile}_rdn_v2p9.nc")
        aviris_dataset: xa.Dataset = xa.open_dataset(input_file)
        filtered_input_bands: xa.DataArray = aviris_dataset.band_data.where(aviris_dataset.center < center_threshold, drop=True)
        train_data_filtered = filtered_input_bands.stack( samples=('x', 'y') ).transpose().isel( samples=get_indices( valid_mask ) )

    n_training_samples = int( train_data_filtered.shape[0] / 5.0 )
    mseCols = ['mse_train', 'mse_trainC', 'mse_test', 'mse_testC']
    scoreCols = [ 'trainScore', 'testScore', 'ConstantModel' ]
    global_score_table = IterativeTable( cols=scoreCols )
    x_data_norm = train_data_filtered[:n_training_samples].values
    y_data = y_data_filtered[:n_training_samples].values
    y_data = y_data - y_data.mean()

    score_table = IterativeTable( cols=mseCols )
    modParms = parameters[modelType]
    estimator: EstimatorBase = EstimatorBase.new( modelType )
    estimator.update_parameters( **modParms )
    print( f"Executing {modelType} estimator, parameters: { estimator.instance_parameters.items() } " )
    estimator.fit( x_data_norm, y_data )
    model_mean  =  y_data.mean()
    const_model_train = np.full( y_data.shape, model_mean )
    print( f"Performance {modelType}: ")

    train_prediction = estimator.predict(x_data_norm)
    mse_train =  mean_squared_error( y_data, train_prediction )
    mse_trainC = mean_squared_error( y_data, const_model_train )
    print( f" ----> TRAIN SCORE: {mse_trainC/mse_train:.2f} [ MSE= {mse_train:.2f}: C={mse_trainC:.2f}  ]")

    if make_plots:
        fig, ax = plt.subplots(1)
        ax.set_title( f"{modelType} Train Data MSE = {mse_train:.2f}: C={mse_trainC:.2f} ")
        xaxis = range(train_prediction.shape[0])
        ax.plot(xaxis, y_data, "b--", label="train data")
        ax.plot(xaxis, train_prediction, "r--", label="prediction")
        ax.plot(xaxis, const_model_train, "r--", label="const_model")
        ax.legend()
        plt.tight_layout()
        outFile =  os.path.join( outDir, f"plots{version}-{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

    saved_model_path = os.path.join( outDir, f"model.{modelType}.{version}.pkl")
    filehandler = open(saved_model_path,"wb")
    pickle.dump( estimator, filehandler )
    print( f"Saved {modelType} Estimator to file {saved_model_path}" )






