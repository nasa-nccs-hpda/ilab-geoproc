import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
import numpy as np
import os, pickle
from csv import reader as csv_reader

if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    version = "T2"
    vrange = [ -1., 3. ]
    modelType = "perceptron"
    init_weights_file = f"{outDir}/aviris.perceptron-{version}.pkl"
    init_weights = pickle.load( open( init_weights_file, "rb" ) )
    ref_band_weights_reader = csv_reader(  open( f"{DATA_DIR}/band_weights.csv", "r") )
    show_weights = True
    show_images = False

    if show_weights:
        from geoproc.plot.bar import MultiBar
        ban_data = { int(row[0][1:]): float(row[2]) for row in ref_band_weights_reader }
        ref_weights = np.array( [ ban_data.get(iW,0.0) for iW in range( init_weights.size )] )
        band_names = { ib: f"b{ib}" for ib in range( 0, init_weights.size, 10 ) }
        barplots = MultiBar( "Band weights", band_names )
        barplots.addPlot(f"ML_weights", init_weights/np.abs(init_weights).mean() )
        barplots.addPlot(f"ref_weights", ref_weights/np.abs(ref_weights).mean() )
        barplots.show()

    if show_images:
        from geoproc.aviris.perceptron import LinearPerceptron
        print("Reading Data")
        xTrainFile = os.path.join(outDir, f"{aviris_tile}_xtrain_full.nc")
        yTrainFile = os.path.join(outDir, f"{aviris_tile}_ytrain_full.nc")
        y_dataset: xa.Dataset = xa.open_dataset(yTrainFile)
        x_dataset: xa.Dataset = xa.open_dataset(xTrainFile)
        x_data_raw, y_data_raw = x_dataset.xdata, y_dataset.ydata - y_dataset.ydata.mean()
        x_data_train = x_data_raw.stack(samples=('x', 'y')).transpose().values
        y_data_train = y_data_raw.stack(samples=('x', 'y')).values

        print("Constructing Image")
        estimator: LinearPerceptron = LinearPerceptron( weights = init_weights )
        train_prediction = estimator.predict( x_data_train )
        constructed_image: xa.DataArray = xa.DataArray( train_prediction.reshape( y_data_raw.shape ), coords=dict(x=y_data_raw.x,y=y_data_raw.y), dims=['x','y'] )

        print("Plotting")
        fig, ax = plt.subplots( nrows=2, sharex=True,  sharey=True )

        y_data_raw.transpose().plot.imshow( ax=ax[0], yincrease=False, cmap="jet", vmin=vrange[0], vmax=vrange[1] )
        ax[0].set_title(f" Target Image ")

        constructed_image.transpose().plot.imshow( ax=ax[1], yincrease=False, cmap="jet", vmin=vrange[0], vmax=vrange[1] )
        ax[1].set_title(f" Linear Perceptron Constructed Image ")

        plt.tight_layout()
        plt.show()

