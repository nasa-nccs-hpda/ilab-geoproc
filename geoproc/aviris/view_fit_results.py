import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
import numpy as np
import os, pickle
from csv import reader as csv_reader
from geoproc.data.sampling import get_binned_sampling, add_bias_column

def get_ref_band_weights( file: str, col: int, nbands: int ) -> np.array:
    ref_band_weights_reader = csv_reader( open(file, "r") )
    ban_data = {int(row[0][1:]): float(row[col]) for row in ref_band_weights_reader}
    return np.array([ban_data.get(iW, 0.0) for iW in range(nbands)])

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
    type = "Weights"
    vrange = [ -1., 3. ]
    modelType = "perceptron"
    nbands = 106
    show_weights = False
    show_images = False
    view_result_image = True
    n_bins = 16
    n_samples_per_bin = 500
    n_iter = 200000

    if view_result_image:
        view_ml_algo = "perceptron"
        fig, ax = plt.subplots()
        rf_save_image_file = f"{outDir}/aviris-image.{view_ml_algo}-R2-{n_samples_per_bin}.nc"
        rf_dataset: xa.Dataset = xa.open_dataset( rf_save_image_file )
        rf_dataset.constructed_image.plot.imshow(ax=ax, yincrease=False, cmap="jet", vmin=vrange[0], vmax=vrange[1])
        ax.set_title(f" RF Constructed Image ")
        plt.tight_layout()
        plt.show()


    if show_weights:
        from geoproc.plot.bar import MultiBar
        band_names = {ib: f"b{ib}" for ib in range(0, nbands, 10)}
        barplots = MultiBar( "Band weights", band_names )

        ref_novn_weights = get_ref_band_weights( f"{DATA_DIR}/ref_band_weights_NoVN.csv", 8, nbands )
        barplots.addPlot( "Ref Weights NoVM", ref_novn_weights/np.abs(ref_novn_weights).mean() )

        for i_batch in range(5):
            init_weights_file = f"{outDir}/aviris.{modelType}-{version}-{n_samples_per_bin}-{n_iter_per_batch}-{i_batch}.pkl"
            init_weights = pickle.load(open(init_weights_file, "rb"))
            barplots.addPlot(f"ML_{type}-{modelType}-{(i_batch+1)*n_iter_per_batch}", init_weights/np.abs(init_weights).mean() )
        barplots.show()

    if show_images:
        from geoproc.aviris.perceptron import LinearPerceptron
        print("Reading Data")
        i_batch = 0
        init_weights_file = f"{outDir}/aviris.perceptron-{version}-{n_samples_per_bin}-{n_iter}.pkl"
        init_weights = pickle.load(open(init_weights_file, "rb"))

        yTrainFile = os.path.join(outDir, f"{aviris_tile}_Avg-Chl_{version}.nc")
        y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)

        y_data_full: xa.DataArray = y_dataset.band_data.squeeze().stack(samples=('x', 'y'))
        valid_mask = np.isnan(y_data_full) != True
        y_data_masked = y_data_full.where(valid_mask, drop=True)
        samples_coord = np.array(range(y_data_masked.shape[0]))
        y_data = y_data_masked.assign_coords(samples=samples_coord)

        xTrainFile = os.path.join(outDir, f"{aviris_tile}_corr_v2p9_{version}_{nbands}.nc")
        x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)
        x_data_full = x_dataset.band_data.stack(samples=('x', 'y')).transpose()
        x_data = x_data_full.isel(samples=get_indices(valid_mask)).assign_coords(samples=samples_coord)

        x_binned_data, y_binned_data = get_binned_sampling(x_data, y_data, n_bins, n_samples_per_bin)
        x_data_train = x_binned_data.values
        y_train_data = y_binned_data.values

        print("Constructing Image")
        estimator: LinearPerceptron = LinearPerceptron( weights = init_weights )
        train_prediction = estimator.predict( x_data_full )
        constructed_image: xa.DataArray = xa.DataArray( train_prediction.reshape( x_dataset.band_data.shape[1:] ), dims=['x','y'], coords=dict(x=x_dataset.band_data.x,y=x_dataset.band_data.y) )
        target_image: xa.DataArray = y_data_full.unstack("samples")

        print("Plotting")
        fig, ax = plt.subplots()

        constructed_image.transpose().plot.imshow( ax=ax, yincrease=False, cmap="jet", vmin=vrange[0], vmax=vrange[1] )
        ax.set_title(f" Linear Perceptron Constructed Image ")

        plt.tight_layout()
        plt.show()

