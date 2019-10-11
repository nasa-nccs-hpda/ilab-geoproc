import matplotlib.animation as animation
from matplotlib.figure import Figure
from geoproc.util.configuration import ConfigurableObject, Region
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from typing import Dict, List, Tuple, Union
import os, time, sys
import xarray as xr

class TilePlotter(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        colors = self.getParameter( "colors", [(0, 0, 0), (0.5, 1, 0.25), (0, 0, 1), (1, 1, 0)] )
        self.setColormap( colors )

    def setColormap(self, colors: List[Tuple[float,float,float]] ):
        self.norm = Normalize( 0,len(colors) )
        self.cm = LinearSegmentedColormap.from_list( "geoProc-TilePlotter", colors, N=len(colors) )

    def plot(self, axes, data_arrays: Union[xr.DataArray,List[xr.DataArray]], timeIndex = -1 ):
        print("Plotting tile")
        if not isinstance(data_arrays, list): data_arrays = [data_arrays]
        if timeIndex >= 0:
            axes.imshow( data_arrays[timeIndex].values, cmap=self.cm, norm=self.norm )
        else:
            if len( data_arrays ) == 1:
                axes.imshow( data_arrays[0].values, cmap=self.cm, norm=self.norm )
            else:
                da: xr.DataArray = self.time_merge( data_arrays )
                result = da[0].copy()
                result = result.where( result == 0, 0 )
                land = ( da == 1 ).sum( axis=0 )
                perm_water = ( da == 2 ).sum( axis=0 )
                print( "Computed masks" )
                result = result.where( land == 0, 1 )
                result = result.where( perm_water == 0, 2 )
                axes.imshow( result.values, cmap=self.cm, norm=self.norm )

class ArrayAnimation(ConfigurableObject):

    def __init__(self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def create_file_animation(self,  files: List[str], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        bbox: Region = self.getParameter("bbox")
        if bbox is None:
            data_arrays: List[xr.DataArray] = [ xr.open_rasterio(file)[0] for file in files ]
        else:
            data_arrays: List[xr.DataArray] = [ xr.open_rasterio(file)[ 0, bbox.origin[0]:bbox.bounds[0], bbox.origin[1]:bbox.bounds[1] ] for file in files ]
        return self.create_animation( data_arrays, savePath, overwrite )

    def create_array_animation(self,  data_array: xr.DataArray, savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        data_arrays: List[xr.DataArray] = [  data_array[iT] for iT in range(data_array.shape[0]) ]
        return self.create_animation( data_arrays, savePath, overwrite )

    def create_animation( self, data_arrays: List[xr.DataArray], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        images = []
        t0 = time.time()
        colors = [(0, 0, 0), (0.15, 0.3, 0.5), (0, 0, 1), (1, 1, 0)]
        norm = Normalize(0,4)
        cm = LinearSegmentedColormap.from_list( "lake-map", colors, N=4 )
        fps = self.getParameter( "fps", 2 )
        roi: Region = self.getParameter("roi")
        print("\n Executing create_array_animation ")
        figure, axes = plt.subplots() if roi is None else plt.subplots(1,2)

        if roi is  None:
            for da in data_arrays:
                im: Image = axes.imshow( da.values, animated=True, cmap=cm, norm=norm )
                images.append([im])
        else:
            for da in data_arrays:
                im0: Image = axes[0].imshow( da.values, animated=True, cmap=cm, norm=norm  )
                im1: Image = axes[1].imshow( da[ roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1] ], animated=True, cmap=cm, norm=norm )
                images.append( [im0,im1] )

            rect = patches.Rectangle( roi.origin, roi.size, roi.size, linewidth=1, edgecolor='r', facecolor='none')
            axes[0].add_patch(rect)

        anim = animation.ArtistAnimation( figure, images, interval=1000.0/fps )

        if savePath is not None:
            if ( overwrite or not os.path.exists( savePath )):
                anim.save( savePath, fps=fps )
                print( f" Animation saved to {savePath}" )
            else:
                print( f" Animation file already exists at '{savePath}'', set 'overwrite = True'' if you wish to overwrite it." )
        print(f" Completed create_array_animation in {time.time()-t0:.3f} seconds" )
        plt.show()
        return anim

    def getDataSubset( self, data_arrays: List[xr.DataArray], frameIndex: int, bin_size: 8, roi: Region ):
        results = []
        for iFrame in range(frameIndex,frameIndex+bin_size):
            da = data_arrays[ min( iFrame, len(data_arrays)-1 ) ]
            results.append( da[ roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1] ] )
        return results

    def create_watermap_diag_animation( self, data_arrays: List[xr.DataArray], savePath: str = None, overwrite = False ) -> animation.TimedAnimation:
        from geoproc.surfaceMapping.lakes import WaterMapGenerator
        images = []
        t0 = time.time()
        colors = [(0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1)]
        norm = Normalize(0,4)
        cm = LinearSegmentedColormap.from_list( "lake-map", colors, N=4 )
        fps = self.getParameter( "fps", 2 )
        roi: Region = self.getParameter("roi")
        print("\n Executing create_array_animation ")
        figure, axes = plt.subplots(1,3)
        waterMapGenerator = WaterMapGenerator()
        water_maps = {}

        anim_running = True
        def onClick(event):
            nonlocal anim_running
            if anim_running:
                anim.event_source.stop()
                anim_running = False
            else:
                anim.event_source.start()
                anim_running = True

        for frameIndex in range( len(data_arrays) ):
            waterMaskIndex = frameIndex // 8
            da = data_arrays[frameIndex]
            waterMask = water_maps.setdefault( waterMaskIndex, waterMapGenerator.get_water_mask( self.getDataSubset(data_arrays, frameIndex, 8, roi ) ) )
            im0: Image = axes[0].imshow(da.values, animated=True, cmap=cm, norm=norm  )
            im1: Image = axes[1].imshow( da[ roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1] ], animated=True, cmap=cm, norm=norm )
            im2: Image = axes[2].imshow( waterMask, animated=True, cmap=cm, norm=norm )
            images.append( [im0,im1,im2] )

#        image_extent = images[0][0].get_extent()
#        image_size: Image = [ image_extent[1]-image_extent[0], image_extent[2]-image_extent[3] ]
#        array_size = data_arrays[0].shape
#        resolution: List[float] = [ image_size[i]/array_size[i] for i in [0,1] ]
#        origin = tuple( [ roi.origin[i]*resolution[i] for i in [0,1] ] )
#        size = [roi.size * resolution[i] for i in [0, 1]]
#        rect = patches.Rectangle( origin, size[0], size[1], linewidth=1, edgecolor='r', facecolor='none')
        rect = patches.Rectangle( roi.origin, roi.size, roi.size, linewidth=1, edgecolor='r', facecolor='none')
        axes[0].add_patch(rect)
        figure.canvas.mpl_connect('button_press_event', onClick)
        anim = animation.ArtistAnimation( figure, images, interval=1000.0/fps, repeat_delay=1000)

        if savePath is not None:
            if ( overwrite or not os.path.exists( savePath )):
                anim.save( savePath, fps=fps )
                print( f" Animation saved to {savePath}" )
            else:
                print( f" Animation file already exists at '{savePath}'', set 'overwrite = True'' if you wish to overwrite it." )
        print(f" Completed create_array_animation in {time.time()-t0:.3f} seconds" )
        plt.show()
        return anim



if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager

    t0 = time.time()
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = locations[0]
    product: str = products[0]
    year = 2019
    download = False
    roi = Region( [250,250], 20 )
    bbox = Region([1750, 1750], 500 )
    fps = 0.5

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults( product=product, download=download, year=2019, start_day=1, end_day=365, bbox=bbox )
    data_arrays = dataMgr.download_tile_data( location )

    animator = ArrayAnimation( roi=roi, fps=fps )
#    animationFile = os.path.join(DATA_DIR, f'MWP_{year}_{location}_{product}_subset.gif')
    animator.create_watermap_diag_animation( data_arrays )
