import os, math, pickle, numpy as np
from geoproc.plot.bar import MultiBar
from typing import List, Union, Tuple

def norm( x: np.ndarray ): return x/x.mean()

scratchDir = os.environ.get( "ILSCRATCH", os.path.expanduser("~/ILAB/scratch") )
outDir = os.path.join( scratchDir, "results", "Bathymetry" )

band_names = [ 'b1_LC8_075', 'b2_LC8_075', 'b3_LC8_075', 'b4_LC8_075', 'b5_LC8_075', 'b6_LC8_075', 'b7_LC8_075', 'b8_LC8_075', 'b9_LC8_075', 'b10_LC8_07',
               'b11_LC8_07', 'b12_LC8_07', 'b13_LC8_07', 'b14_LC8_07', 'b15_LC8_07', 'b16_LC8_07', 'b17_LC8_07', 'b18_LC8_07', 'b19_LC8_07', 'b20_LC8_07',
               'b21_LC8_07', 'b22_LC8_07', 'b23_LC8_07', 'b24_LC8_07', 'b25_LC8_07', 'b26_LC8_07', 'b27_LC8_07', 'b28_LC8_07', 'b29_LC8_07', 'b30_LC8_07',
               'b31_LC8_07', 'b32_LC8_07', 'b33_LC8_07', 'b34_LC8_07', 'b35_LC8_07' ]

barplots = MultiBar("MLP Feature Importance", band_names )
nRuns = 8
weight_by_bpvals = False
bpvals_dataArray = None

def get_weights(model_index ) -> List[np.ndarray]:
    saved_model_path = os.path.join( outDir, f"mlp_weights_{model_index}" )
    filehandler = open(saved_model_path, "rb")
    weights = pickle.load( filehandler )
    return weights

def ann_feature_importance( model_index ) -> np.ndarray:
    weights = get_weights( model_index )
    w0: np.ndarray = weights[0]
    w1: np.ndarray = weights[2]
    feature_importance = np.fabs( np.matmul( w0, w1 ) )
    return norm(feature_importance)

def rf_feature_importance( model_index: int ) -> np.ndarray:
    saved_model_path = os.path.join(outDir, f"model.rf.T{model_index}.pkl")
    filehandler = open(saved_model_path, "rb")
    estimator = pickle.load(filehandler)
    from sklearn.ensemble import RandomForestRegressor
    instance: RandomForestRegressor = estimator.instance
    feature_importance: np.ndarray =  norm( instance.feature_importances_ )
    return feature_importance.reshape( [ feature_importance.shape[0], 1 ])

ann_fi = [ ann_feature_importance( model_index ) for model_index in range(nRuns) ]
ann_ave = np.stack( ann_fi, axis=1 ).mean( axis = 1 ).squeeze()
barplots.addPlot(f"ANN Feature Importance", ann_ave )

rf_fi = [ rf_feature_importance( model_index ) for model_index in range(nRuns) ]
rf_ave = np.stack( rf_fi, axis=1 ).mean( axis = 1 ).squeeze()
barplots.addPlot( f"RF Feature Importance", rf_ave )

barplots.show()
