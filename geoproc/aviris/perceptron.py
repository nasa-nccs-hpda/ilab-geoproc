import xarray as xa
import matplotlib.pyplot as plt
import numpy as np
import os, pickle

class LinearPerceptron:

    def __init__(self):
        self.weights = None

    def fit(self, x_data: np.ndarray, y_data: np.ndarray, **kwargs ):
        n_iter = kwargs['n_iter']
        alpha =  kwargs['learning_rate'] * 1e-5
        if self.weights is None:
            self.weights = np.zeros( [ x_data.shape[1] ] )
        for iL in range(n_iter):
            err = y_data - self.predict( x_data )
            if iL% 100 == 0: print( f" iter {iL}, max error = {err.max()}")
            self.weights = self.weights + alpha * np.dot( err, x_data )

    def predict(self, x_data: np.ndarray ) -> np.ndarray:
        return np.dot(self.weights, x_data.transpose())

if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    version = "T1"
    scale_threshold = 10.0
    n_training_samples = 1000
    verbose = False
    make_plots = True
    show_plots = True
    usePCA = False

    parameters = dict(n_iter = 100000, learning_rate = 1.0 )

    def get_indices(valid_mask: np.ndarray) -> np.ndarray:
        return np.extract(valid_mask, np.array(range(valid_mask.size)))

    def mean_squared_error(x: np.ndarray, y: np.ndarray):
        diff = x - y
        return np.sqrt(np.mean(diff * diff, axis=0))

    print("Reading Data")

    xTrainFile = os.path.join(outDir, f"{aviris_tile}_xtrain_{n_training_samples}.nc")
    yTrainFile = os.path.join(outDir, f"{aviris_tile}_ytrain_{n_training_samples}.nc")
    y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)
    x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)

    x_data = x_dataset.xdata.values
    y_data = y_dataset.ydata.values

    estimator: LinearPerceptron = LinearPerceptron()
    estimator.fit( x_data, y_data, **parameters )

    train_prediction = estimator.predict( x_data )
    mse_train =  mean_squared_error( y_data, train_prediction )
    print( f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")