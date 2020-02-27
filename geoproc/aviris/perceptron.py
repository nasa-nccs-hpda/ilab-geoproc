import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
import numpy as np
import os, pickle
from geoproc.data.sampling import get_binned_sampling, add_bias_column

class LinearPerceptron:

    def __init__(self, train_data: np.ndarray, target_data: np.ndarray ):
        self.weights = None
        self.x = train_data
        self.y = target_data
        self.weights = np.zeros([self.x.shape[1]])
        self.lrscale = 1e-2

    def fit(self, **kwargs ):
        n_iter = kwargs['n_iter']
        alpha =  kwargs['learning_rate'] * self.lrscale
        emax, mse, error = self.get_error( self.predict() )
        max_error_data = []
        mse_data = []
        for iL in range(n_iter):
            dW = np.dot( error, self.x ) / self.x.shape[0]
            new_weights = self.weights + alpha * dW
            prediction = np.dot( new_weights, self.x.transpose())
            emax, new_mse, error = self.get_error( prediction )
            decreasing = new_mse < mse
            if decreasing:
                self.weights = new_weights
                mse = new_mse
                max_error_data.append( emax )
                mse_data.append( mse )
#            if not decreasing or ( (iL % 100 == 0) and (iL >= 200) ):
            if not decreasing or ((iL % 10 == 0) and (iL >= 2)):
                alpha = self.optimize_learning_rate( alpha, dW )
            if (iL < 10) or (iL % 20 == 0):
                print(f" iter {iL}, max error = {emax}, mse = {mse}, alpha = {alpha}, decreasing = {decreasing}")
        return np.array(mse_data), np.array(max_error_data)

    def optimize_learning_rate(self, alpha: float, dW: np.ndarray ) -> float:
        rmag = alpha * 0.1
        arange = np.linspace( alpha-rmag, alpha + rmag, 11 )
        errors = [ self.get_mse( np.dot(self.weights + a * dW, self.x.transpose()) ) for a in arange ]
        min_error_indices = np.where(errors == np.amin(errors))[0]
        return arange[ min_error_indices[0] ]

    def get_error( self, prediction: np.ndarray ) -> Tuple[float,float,np.ndarray]:
        diff = self.y - prediction
        return diff.max(axis=0), np.sqrt(np.mean(diff * diff, axis=0)), diff

    def get_mse( self, prediction: np.ndarray ) -> float:
        diff = self.y - prediction
        return np.sqrt(np.mean(diff * diff, axis=0))

    def predict( self, input_data: Optional[np.ndarray] = None ) -> np.ndarray:
        input = self.x.transpose() if input_data is None else input_data.transpose()
        return np.dot(self.weights, input )

if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    version = "T1"
    modelType = "perceptron"
    verbose = False
    make_plots = True
    show_plots = True
    n_bins = 16
    n_samples_per_bin = 10000
    n_iter = 100000
    n_samples = 1000
    use_binned_sampling = True
    use_bias = False

    parameters = dict( n_iter = n_iter, learning_rate = 1.2 )

    def get_indices(valid_mask: np.ndarray) -> np.ndarray:
        return np.extract(valid_mask, np.array(range(valid_mask.size)))

    def mean_squared_error(x: np.ndarray, y: np.ndarray):
        diff = x - y
        return np.sqrt(np.mean(diff * diff, axis=0))

    print("Reading Data")
    xTrainFile = os.path.join(outDir, f"{aviris_tile}_xtrain_full.nc")
    yTrainFile = os.path.join(outDir, f"{aviris_tile}_ytrain_full.nc")
    y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)
    x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)
    x_data_raw, y_data_raw = add_bias_column( x_dataset.xdata ) if use_bias else x_dataset.xdata, y_dataset.ydata
    y_data = y_data_raw - y_data_raw.mean()
    x_data_full = x_data_raw.values
    y_data_full = y_data.values

    if use_binned_sampling:
        x_binned_data, y_binned_data = get_binned_sampling( x_data_raw, y_data, n_bins, n_samples_per_bin)
        x_train_data = x_binned_data.values
        y_train_data = y_binned_data.values
    else:
        x_train_data = x_data_raw.values[0:n_samples]
        y_train_data = y_data.values[0:n_samples]

    estimator: LinearPerceptron = LinearPerceptron( x_train_data, y_train_data )
    mse, max_error = estimator.fit( **parameters )

    train_prediction = estimator.predict( x_data_full )
    mse_train =  mean_squared_error( y_data_full, train_prediction )
    print( f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")

    if make_plots:
        fig, ax = plt.subplots(2)

        ax[0].set_title( f"{modelType} Train Result MSE = {mse_train:.2f} ")
        xaxis0 = range(train_prediction.shape[0])
        ax[0].plot(xaxis0, y_data_full, color=(0,0,1,0.5), label="train data")
        ax[0].plot(xaxis0, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax[0].legend( loc = 'upper right' )

        ax[1].set_title( f"{modelType} Training Performance ")
        xaxis1 = range(mse.size)
        ax[1].plot(xaxis1, mse, color=(0,0,1,0.5), label="mse")
        ax[1].plot(xaxis1, max_error*0.25, color=(1,0,0,0.5), label="max_error")
        ax[1].set_yscale("log")
        ax[1].legend( loc = 'upper right' )

        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

    saved_model_path = os.path.join( outDir, f"aviris.{modelType}-{n_iter}-{n_bins}-{n_samples_per_bin}.pkl")
    filehandler = open(saved_model_path,"wb")
    pickle.dump( estimator.weights, filehandler )
    print( f"Saved {modelType} Estimator to file {saved_model_path}" )