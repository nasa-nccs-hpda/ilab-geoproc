import os, math, numpy as np
from geoproc.plot.bar import MultiBar

scratchDir = os.environ.get( "ILSCRATCH", os.path.expanduser("~/ILAB/scratch") )
outDir = os.path.join( scratchDir, "results", "Bathymetry" )
whiten = False

band_names = [ 'b1_LC8_075', 'b2_LC8_075', 'b3_LC8_075', 'b4_LC8_075', 'b5_LC8_075', 'b6_LC8_075', 'b7_LC8_075', 'b8_LC8_075', 'b9_LC8_075', 'b10_LC8_07',
               'b11_LC8_07', 'b12_LC8_07', 'b13_LC8_07', 'b14_LC8_07', 'b15_LC8_07', 'b16_LC8_07', 'b17_LC8_07', 'b18_LC8_07', 'b19_LC8_07', 'b20_LC8_07',
               'b21_LC8_07', 'b22_LC8_07', 'b23_LC8_07', 'b24_LC8_07', 'b25_LC8_07', 'b26_LC8_07', 'b27_LC8_07', 'b28_LC8_07', 'b29_LC8_07', 'b30_LC8_07',
               'b31_LC8_07', 'b32_LC8_07', 'b33_LC8_07', 'b34_LC8_07', 'b35_LC8_07' ]

datafile = os.path.join(outDir, 'bpvals.mlp.csv' )
# usecols = [1] + list(range(3,len(band_names)+3))
dataArray: np.ndarray = np.loadtxt( datafile, delimiter="," )

barplots = MultiBar("MLP bpvals", band_names )

for iC in range(dataArray.shape[0]):
    bpvals = dataArray[iC]
    barplots.addPlot(f"bpvals", bpvals )

barplots.show()
