import xarray as xa
import numpy as np
from typing import List, Tuple, Union
import os, sys, pickle

def get_binned_sampling( x_data_full: xa.DataArray, y_data_full: xa.DataArray, n_bins: int, n_samples_per_bin: int = 1000 ) -> Tuple[xa.DataArray,xa.DataArray]:
    training_indices = []
    for sbin in y_data_full[ y_data_full.dims[0] ].groupby_bins( y_data_full, n_bins ):
        binned_indices: xa.DataArray = sbin[1]
        ns = binned_indices.size
        if ns <= n_samples_per_bin:
            training_indices.append(  binned_indices.values )
        else:
            selection_indices = np.linspace( 0, ns-1, n_samples_per_bin ).astype( np.int )
            sample_indices = binned_indices.isel( samples=selection_indices )
            training_indices.append( sample_indices.values )
        print( f"  *  Bin range = {sbin[0]}; NSamples total = {ns}, actual = {training_indices[-1].size} ")

    np_training_indices = np.concatenate( training_indices )
    x_data_train = x_data_full.isel( samples=np_training_indices, drop=True )
    y_data_train = y_data_full.isel( samples=np_training_indices, drop=True )
    return x_data_train, y_data_train

def add_bias_column( x_data: xa.DataArray )-> xa.DataArray:
    return xa.concat([ x_data, xa.ones_like(x_data[:,0]) ], x_data.dims[1] )
