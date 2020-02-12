import os, math, pickle, numpy as np
from geoproc.plot.bar import MultiBar

scratchDir = os.environ.get( "ILSCRATCH", os.path.expanduser("~/ILAB/scratch") )
outDir = os.path.join( scratchDir, "results", "Bathymetry" )

band_names = [ 'b1_LC8_075', 'b2_LC8_075', 'b3_LC8_075', 'b4_LC8_075', 'b5_LC8_075', 'b6_LC8_075', 'b7_LC8_075', 'b8_LC8_075', 'b9_LC8_075', 'b10_LC8_07',
               'b11_LC8_07', 'b12_LC8_07', 'b13_LC8_07', 'b14_LC8_07', 'b15_LC8_07', 'b16_LC8_07', 'b17_LC8_07', 'b18_LC8_07', 'b19_LC8_07', 'b20_LC8_07',
               'b21_LC8_07', 'b22_LC8_07', 'b23_LC8_07', 'b24_LC8_07', 'b25_LC8_07', 'b26_LC8_07', 'b27_LC8_07', 'b28_LC8_07', 'b29_LC8_07', 'b30_LC8_07',
               'b31_LC8_07', 'b32_LC8_07', 'b33_LC8_07', 'b34_LC8_07', 'b35_LC8_07' ]

barplots = MultiBar("MLP Feature Importance", band_names )
nRuns = 1
weight_by_bpvals = True

if weight_by_bpvals:
    bpvals_datafile = os.path.join(outDir, 'bpvals.mlp.csv')
    bpvals_dataArray: np.ndarray = np.loadtxt(bpvals_datafile, delimiter=",")
else: bpvals_dataArray = None

for model_index in range(nRuns):
    saved_model_path = os.path.join(outDir, f"mlp_weights_{model_index}")
    filehandler = open(saved_model_path, "rb")
    weights = pickle.load( filehandler )
    w0: np.ndarray = weights[0]
    w1: np.ndarray = weights[2]
    feature_importance = np.fabs( np.matmul( w0, w1 ).squeeze() )

    if weight_by_bpvals:
        bpvals = np.fabs( bpvals_dataArray[ model_index ] )
        feature_importance = np.dot( feature_importance, bpvals )
    barplots.addPlot(f"M{model_index}", feature_importance.squeeze() )

barplots.show()
