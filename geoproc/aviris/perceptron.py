import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
import numpy as np
import os, pickle
from geoproc.data.sampling import get_binned_sampling, add_bias_column

class LinearPerceptron:

    def __init__(self, **kwargs ):
        self.weights = None
        self.weights = kwargs.get( "weights", None )
        self.lrscale = 1e-2

    def fit(self, train_data: np.ndarray, target_data: np.ndarray, **kwargs ):
        self.x = train_data
        self.y = target_data
        max_error = kwargs.get( 'max_error', 1000 )
        if self.weights is None: self.weights = np.zeros([self.x.shape[1]])
        n_iter = kwargs['n_iter']
        alpha =  kwargs['learning_rate'] * self.lrscale
        emax, mse, error = self.get_error( self.predict() )
        max_error_data = []
        mse_data = []
        for iL in range(n_iter):
            dW = np.dot( error, self.x ) / self.x.shape[0]
            self.weights = self.weights + alpha * dW
            prediction = np.dot( self.weights, self.x.transpose())
            emax, mse, error = self.get_error( prediction )
            max_error_data.append( emax )
            mse_data.append( mse )
            if (iL < 10) or (iL % 20 == 0):
                print(f" iter {iL}, max error = {emax}, mse = {mse}, alpha = {alpha}")
            if abs(mse) > max_error:
                raise Exception( "Diverged!")
        return np.array(mse_data), np.array(max_error_data)

    def optimize_learning_rate(self, alpha: float, dW: np.ndarray ) -> float:
        rmag = alpha * 0.2
        arange = np.linspace( alpha-rmag, alpha + rmag, 21 )
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
    version = "R1"
    init_weights = None
    modelType = "perceptron"
    verbose = False
    make_plots = True
    show_plots = True
    nbands = 106
    n_bins = 16
    n_samples_per_bin = 500
    n_iter = int(1e6)
    learning_rate = 0.5

    save_weights_file = f"{outDir}/aviris.perceptron-{version}.pkl"
    init_weights_file = None

    parameters = dict( n_iter = n_iter, learning_rate = learning_rate )
    if init_weights_file is not None:
        init_weights = pickle.load( open( init_weights_file, "rb" ) )

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
    x_train_data = x_binned_data.values
    y_train_data = y_binned_data.values

    estimator: LinearPerceptron = LinearPerceptron( weights = init_weights )
    mse, max_error = estimator.fit( x_train_data, y_train_data , **parameters )

    train_prediction = estimator.predict( x_data.values )
    mse_train =  mean_squared_error( y_data.values, train_prediction )
    print( f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")

    if save_weights_file:
        filehandler = open(save_weights_file,"wb")
        pickle.dump( estimator.weights, filehandler )
        print( f"Saved {modelType} Estimator to file {save_weights_file}" )

    if make_plots:
        fig, ax = plt.subplots(2)

        ax[0].set_title( f"{modelType} Train Result MSE = {mse_train:.2f} ")
        xaxis0 = range(train_prediction.shape[0])
        ax[0].plot(xaxis0, y_data.values, color=(0,0,1,0.5), label="train data")
        ax[0].plot(xaxis0, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax[0].legend( loc = 'upper right' )

        ax[1].set_title( f"{modelType} Training Performance ")
        xaxis1 = range(mse.size)
        ax[1].plot(xaxis1, mse, color=(0,0,1,0.5), label="mse")
        ax[1].plot(xaxis1, max_error*0.1, color=(1,0,0,0.5), label="max_error")
        ax[1].set_yscale("log")
        ax[1].legend( loc = 'upper right' )

        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

