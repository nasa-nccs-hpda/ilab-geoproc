from matplotlib.axes import SubplotBase
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple, Dict, Any
import csv
import numpy as np


class MultiBar:

    def __init__(self, title: str, bar_labels: List[str], **kwargs ):
        self.fig = plt.figure()
        self.fig.suptitle( title, fontsize=12 )
        self.bar_labels = bar_labels
        self.nBars = len(self.bar_labels)
        self.ycoord = np.arange( self.nBars )
        self.scale = kwargs.get( 'scale', 1.0 )
        self.axes = []
        self.plots = []

    def addPlot(self, title: str, data: np.ndarray):
        self.plots.append( (title,data) )

    def addMeanPlot( self, title: str, **kwargs ):
        aggPlots: np.ndarray = np.stack( [ tup[1] for tup in self.plots ], axis=1 )
        plot_data: np.ndarray =  aggPlots.mean( axis=1)
        self.addPlot( title, plot_data )
        outfile_path: str = kwargs.get( 'write_to_file', None )
        if outfile_path is not None:
            self.write_plot_data( outfile_path, [ plot_data ] )


    def write_plot_data(self, outfile_path: str, plot_data: List[np.ndarray] ):
        with open( outfile_path, "w") as outfile:
            print( f"Write data to file {outfile_path}" )
            csv_writer = csv.writer(outfile)
            for row in plot_data:
                csv_writer.writerow( row )

    def _addPlots( self ):
        nPlots = len( self.plots )
        if nPlots > 0:
            awidth = 0.88 / nPlots
            for plot_index in range( nPlots ):
                title, data = self.plots[plot_index]
                x0 = 0.1 + plot_index * awidth
                if plot_index == 0:
                    ax: SubplotBase = self.fig.add_axes( [ x0, 0.1, awidth, 0.8 ], yticks=self.ycoord, yticklabels=self.bar_labels  )
                    ax.invert_yaxis()
                else:
                    ax = self.fig.add_axes( [ x0, 0.1, awidth, 0.8 ], sharey = self.axes[0], sharex = self.axes[0] )
                    plt.setp( ax.get_yticklabels(), visible=False )

                plt.setp( ax.get_xticklabels(), visible=False )
                ax.set_title(title)
                ax.barh( self.ycoord, data * self.scale, align='center')
                self.axes.append( ax )
            self.plots = []

    def save(self, fname, **kwargs ):
        self._addPlots()
        print( f"Saving plot to: {fname}")
        self.fig.savefig( fname, **kwargs )

    def show( self, **kwargs ):
        self._addPlots()
        plt.show()
