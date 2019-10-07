import matplotlib.animation as animation
from matplotlib.figure import Figure
from geoproc.util.configuration import ConfigurableObject
import matplotlib.pyplot as plt
from typing import Dict, List
import os, time, sys
import xarray as xr

class ArrayAnimation(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def create_file_animation(self,  files: List[str], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        data_arrays: List[xr.DataArray] = [ xr.open_rasterio(file)[0] for file in files ]
        return self.create_animation( data_arrays, savePath, overwrite )

    def create_array_animation(self,  data_array: xr.DataArray, savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        data_arrays: List[xr.DataArray] = [  data_array[iT] for iT in range(data_array.shape[0]) ]
        return self.create_animation( data_arrays, savePath, overwrite )

    def create_animation( data_arrays: List[xr.DataArray], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        images = []
        t0 = time.time()
        print("\n Executing create_array_animation ")
        figure: Figure = plt.figure()

        for da in data_arrays:
            im = plt.imshow(da.values, animated=True)
            images.append([im])
        anim = animation.ArtistAnimation( figure, images, interval=50, blit=True, repeat_delay=1000)
        if savePath is not None and ( overwrite or not os.path.exists( savePath )):
            anim.save( savePath, fps=2 )
            print( f" Animation saved to {savePath}" )
        else:
            print( f" Animation file already exists at '{savePath}'', set 'overwrite = True'' if you wish to overwrite it." )
        print(f" Completed create_array_animation in {time.time()-t0:.3f} seconds" )
        plt.show()
        return anim