import xarray as xa
import matplotlib.pyplot as plt
from typing import List, Union, Tuple, Optional
from csv import reader as csv_reader
from numpy import linalg as LA
import numpy as np
import os, pickle, time, math
from geoproc.aviris.manager import AvirisDataManager

class LinearPerceptron:

    def __init__(self, x: np.ndarray, y: np.ndarray ):
        self.X = x.transpose()
        self.Y = y
        self.XXt = np.matmul( self.X, x )
        self.E = self.maxeig()
        self.XY = np.matmul( self.X, self.Y )

    def maxeig(self) -> float:
        w, v = LA.eig(self.XXt)
        return w.max()

    def h( self, Z: np.ndarray, threshold: float ) -> np.ndarray:
        if threshold == 0.0: return Z
        return np.select( [Z < -threshold, Z < threshold], [Z + threshold, 0], Z - threshold  )

    def fit(self, **params ):
        W = params.get( 'weights', np.zeros( [ self.X.shape[0] ] ) )
        intertia = params.get( 'inertia', 0.01 )
        L =  self.E * ( 1 + intertia )
        sparsity = params.get('sparsity', 0.1)
        threshold = sparsity / L
        max_iter = params.get( 'max_iter', 1000000 )
        mse_thresh = params.get( 'mse_thresh', 0.5 )
        mse = 0.0

        for iL in range(max_iter):
            DW = np.matmul( self.XXt, W ) - self.XY
            Z = W - DW/L
            W = self.h( Z, threshold )

            if iL % 5000 == 0:
                mse = self.get_error( W )
                print( f" ** Iteration {iL}, mse = {mse:.4f}" )
                if mse < mse_thresh:
                    print( "Converged.")
                    break
        return W, mse

    def get_error(self, W: np.ndarray ):
        P = np.matmul( W, self.X )
        return self.mean_squared_error( P, self.Y )

    def mean_squared_error(self, x: np.ndarray, y: np.ndarray) -> float:
        diff = x - y
        return math.sqrt( np.mean( diff * diff ) )
