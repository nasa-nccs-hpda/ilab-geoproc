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
        colors = self.getParameter( "colors", [(0, 0, 0), (0.5, 1, 0.25), (1, 1, 0), (0, 0, 1)] )
        self.setColormap( colors )

    def setColormap(self, colors: List[Tuple[float,float,float]] ):
        self.norm = Normalize( 0,len(colors) )
        self.cm = LinearSegmentedColormap.from_list( "geoProc-TilePlotter", colors, N=len(colors) )

    def plot(self, axes, data_arrays: Union[xr.DataArray,List[xr.DataArray]], timeIndex = -1 ):
        print("Plotting tile")
        axes.set_yticklabels([]); axes.set_xticklabels([])
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

    def __init__( self, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )

    def create_file_animation( self,  files: List[str], savePath: str = None, **kwargs ) -> animation.TimedAnimation:
        from geoproc.xext.xgeo import XGeo
        bbox: Region = self.getParameter("bbox")
        data_arrays: List[xr.DataArray] = XGeo.loadRasterFiles(files, region=bbox)
        return self.create_animation( data_arrays, savePath, **kwargs )

    def create_array_animation(self,  data_array: xr.DataArray, savePath: str = None, **kwargs ) -> animation.TimedAnimation:
        data_arrays: List[xr.DataArray] = [  data_array[iT] for iT in range(data_array.shape[0]) ]
        return self.create_animation( data_arrays, savePath, **kwargs )

    def create_animation( self, data_arrays: List[xr.DataArray], savePath: str = None, **kwargs ) -> animation.TimedAnimation:
        images = []
        overwrite = kwargs.get('overwrite', False )
        display = kwargs.get('display', True)
        t0 = time.time()
        color_map = kwargs.get( 'cmap' )
        if color_map is None:
            colors = [ (0.0, 0.0, 0.1), (0.05, 0.7, 0.2), (0, 0, 1), (1, 1, 0) ]  # (0.15, 0.3, 0.5)
            norm = Normalize(0, len(colors))
            color_map = LinearSegmentedColormap.from_list( "lake-map", colors, N=4 )
        else:
            range = kwargs.get( 'range' )
            norm = Normalize(*range) if range else None
        fps = self.getParameter( "fps", 1 )
        roi: Region = self.getParameter("roi")
        print("\n Executing create_array_animation ")
        figure, axes = plt.subplots() if roi is None else plt.subplots(1,2)
        overlays = kwargs.get('overlays', {})

        if roi is  None:
            axes.set_yticklabels([]); axes.set_xticklabels([])
            for iF, da in enumerate(data_arrays):
                im: Image = axes.imshow( da.values, animated=True, cmap=color_map, norm=norm )
                for color, overlay in overlays.items():
                    overlay.plot(ax=axes, color=color, linewidth=2)
                t = axes.annotate( f"{da.name}[{iF}]", (0,0) )
                images.append([im,t])
        else:
            for axis in axes:
                axis.set_yticklabels([]); axis.set_xticklabels([])
            for iF, da in enumerate(data_arrays):
                im0: Image = axes[0].imshow( da.values, animated=True, cmap=color_map, norm=norm  )
                im1: Image = axes[1].imshow( da[ roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1] ], animated=True, cmap=color_map, norm=norm )

                for color, overlay in overlays.items():
                    overlay.plot(ax=axes[0], color=color, linewidth=2)
                t = axes.annotate( f"{da.name}[{iF}]", ( 0,0) )
                images.append( [im0,im1,t] )

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
        if display: plt.show()
        return anim

    def getDataSubset( self, data_arrays: List[xr.DataArray], frameIndex: int, bin_size: 8, roi: Region ):
        results = []
        for iFrame in range(frameIndex,frameIndex+bin_size):
            da = data_arrays[ min( iFrame, len(data_arrays)-1 ) ]
            results.append( da[ roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1] ] )
        return results

    def create_watermap_diag_animation(self, title: str, data_arrays: List[xr.DataArray], savePath: str = None,
                                       overwrite=False) -> animation.TimedAnimation:
        from geoproc.surfaceMapping.lakes import WaterMapGenerator
        images = []
        t0 = time.time()
        colors = [(0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1)]
        norm = Normalize(0, 4)
        cm = LinearSegmentedColormap.from_list("lake-map", colors, N=4)
        fps = self.getParameter("fps", 0.5)
        roi: Region = self.getParameter("roi")
        print("\n Executing create_array_animation ")
        figure, axes = plt.subplots(2, 2)
        waterMapGenerator = WaterMapGenerator()
        water_maps = [{}, {}, {}]
        figure.suptitle(title, fontsize=16)

        anim_running = True

        def onClick(event):
            nonlocal anim_running
            if anim_running:
                anim.event_source.stop()
                anim_running = False
            else:
                anim.event_source.start()
                anim_running = True

        for frameIndex in range(len(data_arrays)):
            waterMaskIndex = frameIndex // 8
            da0 = data_arrays[frameIndex]
            waterMask11 = water_maps[0].setdefault(waterMaskIndex,
                                                   waterMapGenerator.get_water_mask(self.getDataSubset(data_arrays, frameIndex, 8, roi), 0.5, 1))
            waterMask12 = water_maps[1].setdefault(waterMaskIndex,
                                                   waterMapGenerator.get_water_mask(self.getDataSubset(data_arrays, frameIndex, 8, roi), 0.5, 2))
            waterMask13 = water_maps[2].setdefault(waterMaskIndex,
                                                   waterMapGenerator.get_water_mask(self.getDataSubset(data_arrays, frameIndex, 8, roi), 0.5, 3))
            #            im0: Image = axes[0].imshow(da.values, animated=True, cmap=cm, norm=norm  )
            axes[0, 0].title.set_text('raw data');
            axes[0, 0].set_yticklabels([]);
            axes[0, 0].set_xticklabels([])
            im0: Image = axes[0, 0].imshow(da0[roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1]], animated=True, cmap=cm, norm=norm)
            axes[0, 1].title.set_text('minw: 1');
            axes[0, 1].set_yticklabels([]);
            axes[0, 1].set_xticklabels([])
            im1: Image = axes[0, 1].imshow(waterMask11, animated=True, cmap=cm, norm=norm)
            axes[1, 0].title.set_text('minw: 2');
            axes[1, 0].set_yticklabels([]);
            axes[1, 0].set_xticklabels([])
            im2: Image = axes[1, 0].imshow(waterMask12, animated=True, cmap=cm, norm=norm)
            axes[1, 1].title.set_text('minw: 3');
            axes[1, 1].set_yticklabels([]);
            axes[1, 1].set_xticklabels([])
            im3: Image = axes[1, 1].imshow(waterMask13, animated=True, cmap=cm, norm=norm)
            images.append([im0, im1, im2, im3])

        #        rect = patches.Rectangle( roi.origin, roi.size, roi.size, linewidth=1, edgecolor='r', facecolor='none')
        #        axes[0].add_patch(rect)
        figure.canvas.mpl_connect('button_press_event', onClick)
        anim = animation.ArtistAnimation(figure, images, interval=1000.0 / fps, repeat_delay=1000)

        if savePath is not None:
            if (overwrite or not os.path.exists(savePath)):
                anim.save(savePath, fps=fps)
                print(f" Animation saved to {savePath}")
            else:
                print(f" Animation file already exists at '{savePath}'', set 'overwrite = True'' if you wish to overwrite it.")
        print(f" Completed create_array_animation in {time.time() - t0:.3f} seconds")
        plt.tight_layout()
        plt.show()
        return anim


    def create_multi_array_animation(self, title: str, data_arrays: List[xr.DataArray], savePath: str = None, overwrite=False, colors = None, count_values = None ) -> animation.TimedAnimation:
        anim_frames = []
        t0 = time.time()
        cm_colors = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)] if colors is None else colors
        norm = Normalize(0, len(cm_colors))
        cm = LinearSegmentedColormap.from_list( "tmp-colormap", cm_colors, N=len(cm_colors))
        fps = self.getParameter("fps", 1.0)
        roi: Region = self.getParameter("roi")
        print("\n Executing create_array_animation ")
        figure, axes = plt.subplots(1, len(data_arrays) if count_values is None else len(data_arrays) + 1 )
        figure.suptitle(title, fontsize=16)

        anim_running = True

        def onClick(event):
            nonlocal anim_running
            if anim_running:
                anim.event_source.stop()
                anim_running = False
            else:
                anim.event_source.start()
                anim_running = True


        counts = None if count_values is None else data_arrays[-1].xgeo.countInstances(count_values)

        for frameIndex in range(data_arrays[0].shape[0]):
            images = []
            for iImage, data_array in enumerate(data_arrays):
                axis = axes[ iImage ]
                axis.title.set_text( data_array.name )
                axis.set_yticklabels([]); axis.set_xticklabels([])
                image_data = data_array[frameIndex] if roi is None else data_array[frameIndex, roi.origin[0]:roi.bounds[0], roi.origin[1]:roi.bounds[1]]
                image: Image = axis.imshow( image_data, animated=True, cmap=cm, norm=norm )
                images.append( image )

            if count_values is not None:
                bar_heights = counts[frameIndex]
                axis: plt.Axes =  axes[ len(data_arrays) ]
                axis.set_yticklabels([]); axis.set_xticklabels([])
                plot = axis.barh( [0,1], bar_heights.values, animated=True )
                images.append( plot )

            anim_frames.append( images )

        figure.canvas.mpl_connect('button_press_event', onClick)
        anim = animation.ArtistAnimation(figure, anim_frames, interval=1000.0 / fps, repeat_delay=1000)

        if savePath is not None:
            if (overwrite or not os.path.exists(savePath)):
                anim.save(savePath, fps=fps)
                print(f" Animation saved to {savePath}")
            else:
                print(f" Animation file already exists at '{savePath}'', set 'overwrite = True'' if you wish to overwrite it.")
        print(f" Completed create_array_animation in {time.time() - t0:.3f} seconds")
#        plt.tight_layout()
        plt.show()
        return anim

    def animateGifs(self, gifList: List[str] ):
        images = [ Image.open(gifFile).convert('RGB') for gifFile in gifList ]
        nImages = len( images )
        nRows = nImages // 3
        nCols = nImages // nRows
        figure, axes = plt.subplots( nRows, nCols )




if __name__ == '__main__':
    from geoproc.data.mwp import MWPDataManager

    t0 = time.time()
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "2D2OT" , "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = locations[0]
    product = products[0]
    year = 2019
    download = False
    roi = None
    bbox = Region( [3000,3500], 750 )
    savePath = DATA_DIR + "/watermap_diagnostic_animation.gif"
    fps = 1.0
    time_index_range = [ 192, 195 ]

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults( product=product, download=download, year=2019, start_day=time_index_range[0], end_day=time_index_range[1], bbox=bbox )
    data_arrays = dataMgr.get_tile_data(location)

    animator = ArrayAnimation( roi=roi, fps=fps )
    anim = animator.create_animation( data_arrays )
#    anim = animator.create_watermap_diag_animation( f"{product} @ {location}", data_arrays, savePath, True )
