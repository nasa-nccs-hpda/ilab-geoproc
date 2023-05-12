import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
from csv import reader as csv_reader
import numpy as np
import os, pickle, time
from geoproc.data.sampling import get_binned_sampling, add_bias_column

def get_ref_band_weights( file: str, col: int, nbands: int ) -> np.array:
    ref_band_weights_reader = csv_reader( open(file, "r") )
    ban_data = {int(row[0][1:]): float(row[col]) for row in ref_band_weights_reader}
    return np.array([ban_data.get(iW, 0.0) for iW in range(nbands)])

class LinearPerceptron:

    def __init__(self, **kwargs ):
        self.weights = None
        self.weights = kwargs.get( "weights", None )
        self.lrscale = 1e-2

    def fit(self, train_data: np.ndarray, target_data: np.ndarray, genx_data: np.ndarray, geny_data: np.ndarray, **kwargs ):
        self.x = train_data
        self.y = target_data
        max_error = kwargs.get( 'max_error', 1000 )
        if self.weights is None: self.weights = np.zeros([self.x.shape[1]])
        n_iter = kwargs['n_iter']
        alpha =  kwargs['learning_rate'] * self.lrscale
        beta = kwargs.get('sparsity') * self.lrscale
        mse, error = self.get_error( self.predict() )
        mse_train = []
        mse_gen = []
        for iL in range(n_iter):
            dW =  alpha * np.dot( error, self.x ) / self.x.shape[0]
            if beta > 0.0:
                w2 = 1 + self.weights * self.weights
                dws = beta * self.weights / w2
                m0, ms = dW.mean(), dws.mean()
                dW = dW - dws
            self.weights = self.weights + dW
            prediction = np.dot( self.weights, self.x.transpose())
            mse, error = self.get_error( prediction )
            if (iL % 20 == 0):
                train_prediction = self.predict(genx_data)
                gen_mse = mean_squared_error( geny_data, train_prediction)
                mse_train.append(mse)
                mse_gen.append( gen_mse )
                print(f" iter {iL}, train mse = {mse}, gen mse = {gen_mse}")
            if abs(mse) > max_error:
                raise Exception( "Diverged!")
        return np.array(mse_train), np.array(mse_gen)

    def optimize_learning_rate(self, alpha: float, dW: np.ndarray ) -> float:
        rmag = alpha * 0.2
        arange = np.linspace( alpha-rmag, alpha + rmag, 21 )
        errors = [ self.get_mse( np.dot(self.weights + a * dW, self.x.transpose()) ) for a in arange ]
        min_error_indices = np.where(errors == np.amin(errors))[0]
        return arange[ min_error_indices[0] ]

    def get_error( self, prediction: np.ndarray ) -> Tuple[float,np.ndarray]:
        diff = self.y - prediction
        return np.sqrt(np.mean(diff * diff, axis=0)), diff

    def get_mse( self, prediction: np.ndarray ) -> float:
        diff = self.y - prediction
        return np.sqrt(np.mean(diff * diff, axis=0))

    def predict( self, input_data: Optional[np.ndarray] = None ) -> np.ndarray:
        t0 = time.time()
        input = self.x.transpose() if input_data is None else input_data.transpose()
        result = np.dot(self.weights, input )
        print( f"Ran predict in {time.time()-t0} secs")
        return result

if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    version = "R2"
    init_weights = None
    modelType = "perceptron"
    verbose = False
    make_plots = False
    show_plots = False
    plot_image = True
    nbands = 106
    n_bins = 16
    n_samples_per_bin = 100
    n_iter = 1000
    learning_rate = 0.2
    sparsity = 0.1
    plot_weights = True

    init_weights_file = None

    parameters = dict( n_iter = n_iter, learning_rate = learning_rate,  sparsity = sparsity  )
    if init_weights_file is not None:
        init_weights = pickle.load( open( init_weights_file, "rb" ) )

    def get_indices(valid_mask: np.ndarray) -> np.ndarray:
        return np.extract(valid_mask, np.array(range(valid_mask.size)))

    def mean_squared_error(x: np.ndarray, y: np.ndarray):
        diff = x - y
        return np.sqrt(np.mean(diff * diff, axis=0))

    print("Reading Data")

    xTrainFile = os.path.join(outDir, f"{aviris_tile}_corr_v2p9_{version}_{nbands}.nc")
    x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)
    x_data_raw = x_dataset.band_data
    x_data_full = x_data_raw.stack(samples=('y', 'x')).transpose()
    valid_mask = np.isnan(x_data_full[:,0]) != True

    yTrainFile = os.path.join(outDir, f"{aviris_tile}_Avg-Chl_{version}.nc")
    y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)
    y_data_full = y_dataset.band_data.squeeze().stack(samples=('x', 'y'))
    valid_mask1 = np.isnan( y_data_full )!= True
#    valid_mask = valid_mask0 * valid_mask1

#    y_data_masked = y_data_full.where(valid_mask, drop=True)
#    samples_coord = np.array( range(y_data_masked.shape[0]) )
#    y_data = y_data_masked.assign_coords(samples=samples_coord)

#    x_data_masked = x_data_full.where(valid_mask, drop=True)
#    x_data = x_data_masked.assign_coords(samples=samples_coord)

    x_data_masked = x_data_full.isel(samples=get_indices(valid_mask))
    y_data_masked = y_data_full.isel(samples=get_indices(valid_mask))
    samples_coord = np.array(range(y_data_masked.shape[0]))
    x_data = x_data_masked.assign_coords(samples=samples_coord)
    y_data = y_data_masked.assign_coords(samples=samples_coord)

    x_binned_data, y_binned_data = get_binned_sampling( x_data, y_data, n_bins, n_samples_per_bin )
    x_train_data = x_binned_data.values
    y_train_data = y_binned_data.values

    ts_percent = (y_train_data.size*100.0)/y_data.size
    print(f"Using {y_train_data.size} samples out of {y_data.size}: {ts_percent:.3f}%")

    estimator: LinearPerceptron = LinearPerceptron( weights = init_weights )
    train_mse, gen_mse = estimator.fit( x_train_data, y_train_data , x_data.values, y_data.values, **parameters )

    save_weights_file = f"{outDir}/aviris.perceptron-{version}-{n_samples_per_bin}-{n_iter}.pkl"
    filehandler = open(save_weights_file,"wb")
    pickle.dump( estimator.weights, filehandler )
    print( f"Saved {modelType} Estimator to file {save_weights_file}" )

    if plot_image:
        x_valid_mask = valid_mask.values.reshape([valid_mask.shape[0], 1])
        image_xdata =  np.where( x_valid_mask, x_data_full.values, 0.0 )
        result_image = estimator.predict( image_xdata )
        image_prediction = np.where( x_valid_mask.squeeze(), result_image, np.nan )
        constructed_image: xa.DataArray = xa.DataArray( image_prediction.reshape(x_data_raw.shape[1:]), dims=['y', 'x'], coords=dict(x=x_data_raw.x, y=x_data_raw.y), name="constructed_image" )
        save_image_file = f"{outDir}/aviris-image.{modelType}-{version}-{n_samples_per_bin}.nc"
        print(f"Saving constructed_image to {save_image_file} ")
        constructed_image.to_netcdf( save_image_file )

    if plot_weights:
        wts = estimator.weights
        from geoproc.plot.bar import MultiBar
        band_names = {ib: f"b{ib}" for ib in range(0, nbands, 10)}
        barplots = MultiBar( "Band weights", band_names )
        ref_novn_weights = get_ref_band_weights( f"{DATA_DIR}/ref_band_weights_NoVN.csv", 8, nbands )
        barplots.addPlot( "Ref Weights NoVM", ref_novn_weights/np.abs(ref_novn_weights).mean() )
        barplots.addPlot(f"Perceptron with Sparsity", wts/np.abs(wts).mean() )
        barplots.show()

    if make_plots:
        fig, ax = plt.subplots(2)

        train_prediction = estimator.predict(x_data.values)
        final_mse = mean_squared_error(y_data.values, train_prediction)

        ax[0].set_title( f"{modelType}: {ts_percent:.3f}% samples, MSE={final_mse:.2f} ")
        xaxis0 = range(train_prediction.shape[0])
        ax[0].plot(xaxis0, y_data.values, color=(0,0,1,0.5), label="train data")
        ax[0].plot(xaxis0, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax[0].legend( loc = 'upper right' )

        ax[1].set_title( f"{modelType} Training Performance ")
        xaxis1 = range(train_mse.size)
        ax[1].plot(xaxis1, train_mse, color=(0,0,1,0.5), label="train mse")
        ax[1].plot(xaxis1, gen_mse, color=(0, 1, 0, 0.5), label="gen mse")
        ax[1].set_yscale("log")
        ax[1].legend( loc = 'upper right' )

        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

    if make_plots:
        fig, ax = plt.subplots(2)

        train_prediction = estimator.predict(x_data.values)
        final_mse = mean_squared_error(y_data.values, train_prediction)

        ax[0].set_title( f"{modelType}: {ts_percent:.3f}% samples, MSE={final_mse:.2f} ")
        xaxis0 = range(train_prediction.shape[0])
        ax[0].plot(xaxis0, y_data.values, color=(0,0,1,0.5), label="train data")
        ax[0].plot(xaxis0, train_prediction, color=(1,0,0,0.5), label="prediction")
        ax[0].legend( loc = 'upper right' )

        ax[1].set_title( f"{modelType} Training Performance ")
        xaxis1 = range(train_mse.size)
        ax[1].plot(xaxis1, train_mse, color=(0,0,1,0.5), label="train mse")
        ax[1].plot(xaxis1, gen_mse, color=(0, 1, 0, 0.5), label="gen mse")
        ax[1].set_yscale("log")
        ax[1].legend( loc = 'upper right' )

        plt.tight_layout()
        outFile =  os.path.join( outDir, f"aviris.plots.{modelType}.png" )
        print(f"Saving plots to {outFile} ")
        plt.savefig( outFile )
        if show_plots: plt.show()
        plt.close( fig )

