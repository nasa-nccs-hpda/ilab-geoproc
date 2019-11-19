import matplotlib.widgets
import matplotlib.patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.axes import SubplotBase
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.collections import QuadMesh
import matplotlib.pyplot as plt
from threading import  Thread
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
import xarray as xa
import numpy as np
from typing import List, Union, Dict, Callable, Tuple
import time, math, atexit
from enum import Enum

class ADirection(Enum):
    BACKWARD = -1
    STOP = 0
    FORWARD = 1

class EventSource(Thread):

    def __init__( self, action: Callable, **kwargs ):
        Thread.__init__(self)
        self.event = None
        self.action = action
        self.interval = kwargs.get( "delay",0.5 )
        self.active = False
        self.running = True
        self.daemon = True
        atexit.register( self.exit )

    def run(self):
        while self.running:
            time.sleep( self.interval )
            if self.active:
                plt.pause( 0.01 )
                self.action( self.event )

    def activate(self, delay = None ):
        if delay is not None: self.interval = delay
        self.active = True

    def deactivate(self):
        self.active = False

    def exit(self):
        self.running = False

class PageSlider(matplotlib.widgets.Slider):

    def __init__(self, ax: SubplotBase, numpages = 10, valinit=0, valfmt='%1d', **kwargs ):
        self.facecolor=kwargs.get('facecolor',"yellow")
        self.activecolor = kwargs.pop('activecolor',"blue" )
        self.stepcolor = kwargs.pop('stepcolor', "#ff6f6f" )
        self.animcolor = kwargs.pop('animcolor', "#6fff6f" )
        self.on_animcolor = kwargs.pop('on-animcolor', "#006622")
        self.fontsize = kwargs.pop('fontsize', 10)
        self.maxIndexedPages = 24
        self.numpages = numpages
        self.init_anim_delay: float = 0.5   # time between timer events in seconds
        self.anim_delay: float = self.init_anim_delay
        self.anim_delay_multiplier = 1.5
        self.anim_state = ADirection.STOP
        self.axes = ax
        self.event_source = EventSource( self.step, delay = self.init_anim_delay )

        super(PageSlider, self).__init__(ax, "", 0, numpages, valinit=valinit, valfmt=valfmt, **kwargs)

        self.poly.set_visible(False)
        self.vline.set_visible(False)
        self.pageRects = []
        indexMod = math.ceil( self.numpages / self.maxIndexedPages )
        for i in range(numpages):
            facecolor = self.activecolor if i==valinit else self.facecolor
            r  = matplotlib.patches.Rectangle((float(i)/numpages, 0), 1./numpages, 1, transform=ax.transAxes, facecolor=facecolor)
            ax.add_artist(r)
            self.pageRects.append(r)
            if i % indexMod == 0:
                ax.text(float(i)/numpages+0.5/numpages, 0.5, str(i+1), ha="center", va="center", transform=ax.transAxes, fontsize=self.fontsize)
        self.valtext.set_visible(False)

        divider = make_axes_locatable(ax)
        bax = divider.append_axes("right", size="5%", pad=0.05)
        fax = divider.append_axes("right", size="5%", pad=0.05)
        self.button_back = matplotlib.widgets.Button(bax, label='$\u25C1$', color=self.stepcolor, hovercolor=self.activecolor)
        self.button_forward = matplotlib.widgets.Button(fax, label='$\u25B7$', color=self.stepcolor, hovercolor=self.activecolor)
        self.button_back.label.set_fontsize(self.fontsize)
        self.button_forward.label.set_fontsize(self.fontsize)
        self.button_back.on_clicked(self.step_backward)
        self.button_forward.on_clicked(self.step_forward)

        afax = divider.append_axes("left", size="5%", pad=0.05)
        asax = divider.append_axes("left", size="5%", pad=0.05)
        abax = divider.append_axes("left", size="5%", pad=0.05)
        self.button_aback    = matplotlib.widgets.Button( abax, label='$\u25C0$', color=self.animcolor, hovercolor=self.activecolor)
        self.button_astop = matplotlib.widgets.Button( asax, label='$\u25FE$', color=self.animcolor, hovercolor=self.activecolor)
        self.button_aforward = matplotlib.widgets.Button( afax, label='$\u25B6$', color=self.animcolor, hovercolor=self.activecolor)

        self.button_aback.label.set_fontsize(self.fontsize)
        self.button_astop.label.set_fontsize(self.fontsize)
        self.button_aforward.label.set_fontsize(self.fontsize)
        self.button_aback.on_clicked(self.anim_backward)
        self.button_astop.on_clicked(self.anim_stop)
        self.button_aforward.on_clicked(self.anim_forward)

    def reset_buttons(self):
        for button in [ self.button_aback, self.button_astop, self.button_aforward ]:
            button.color = self.animcolor
        self.refesh()


    def refesh(self):
        self.axes.figure.canvas.draw()

    def start(self):
        self.event_source.start()

    def _update(self, event):
        super(PageSlider, self)._update(event)
        i = int(self.val)
        if i >=self.valmax: return
        self._colorize(i)

    def _colorize(self, i):
        for j in range(self.numpages):
            self.pageRects[j].set_facecolor(self.facecolor)
        self.pageRects[i].set_facecolor(self.activecolor)

    def step( self, event=None ):
        if   self.anim_state == ADirection.FORWARD:  self.forward(event)
        elif self.anim_state == ADirection.BACKWARD: self.backward(event)

    def forward(self, event=None):
        current_i = int(self.val)
        i = current_i+1
        if i >= self.valmax: i = self.valmin
        self.set_val(i)
        self._colorize(i)

    def backward(self, event=None):
        current_i = int(self.val)
        i = current_i-1
        if i < self.valmin: i = self.valmax -1
        self.set_val(i)
        self._colorize(i)

    def step_forward(self, event=None):
        self.anim_stop()
        self.forward(event)

    def step_backward(self, event=None):
        self.anim_stop()
        self.backward(event)

    def anim_forward(self, event=None):
        if self.anim_state == ADirection.FORWARD:
            self.anim_delay = self.anim_delay / self.anim_delay_multiplier
            self.event_source.interval = self.anim_delay
        elif self.anim_state == ADirection.BACKWARD:
            self.anim_delay = self.anim_delay * self.anim_delay_multiplier
            self.event_source.interval = self.anim_delay
        else:
            self.anim_delay = self.init_anim_delay
            self.anim_state = ADirection.FORWARD
            self.event_source.activate( self.anim_delay )
            self.button_aforward.color = self.on_animcolor
            self.refesh()

    def anim_backward(self, event=None):
        if self.anim_state == ADirection.FORWARD:
            self.anim_delay = self.anim_delay * self.anim_delay_multiplier
            self.event_source.interval = self.anim_delay
        elif self.anim_state == ADirection.BACKWARD:
            self.anim_delay = self.anim_delay / self.anim_delay_multiplier
            self.event_source.interval = self.anim_delay
        else:
            self.anim_delay = self.init_anim_delay
            self.anim_state = ADirection.BACKWARD
            self.event_source.activate( self.anim_delay )
            self.button_aback.color = self.on_animcolor
            self.refesh()

    def anim_stop(self, event=None):
        if self.anim_state != ADirection.STOP:
            self.anim_delay = self.init_anim_delay
            self.anim_state = ADirection.STOP
            self.event_source.deactivate()
            self.reset_buttons()

class SliceAnimation:

    def __init__(self, data_arrays: Union[xa.DataArray,List[xa.DataArray]], **kwargs ):
        self.data: List[xa.DataArray] = data_arrays if isinstance(data_arrays, list) else [ data_arrays ]
        assert self.data[0].ndim == 3, f"This plotter only works with 3 dimensional [t,y,x] data arrays.  Found {self.data[0].dims}"
        self.plot_axes = None
        self.figure: Figure = None
        self.images: Dict[int,AxesImage] = {}
        self.nPlots = len(self.data)
        self.plot_grid_shape: List[int] = self.getSubplotShape( )  # [ rows, cols ]
        self.figure, self.plot_axes = plt.subplots( *self.plot_grid_shape )
        self.figure.suptitle( kwargs.get("title",""), fontsize=14 )
        self.figure.subplots_adjust(bottom=0.18)
        self.slider_axes: SubplotBase = self.figure.add_axes([0.1, 0.05, 0.8, 0.04])  # [left, bottom, width, height]
        self.z_axis = kwargs.get('z', 0)
        self.z_axis_name = self.data[0].dims[ self.z_axis ]
        self.x_axis = kwargs.get( 'x', 2 )
        self.x_axis_name = self.data[0].dims[ self.x_axis ]
        self.y_axis = kwargs.get( 'y', 1 )
        self.y_axis_name = self.data[0].dims[ self.y_axis ]

        self.nFrames = self.data[0].shape[0]
        self.create_cmap( **kwargs )
        self.add_plots( **kwargs )
        self.add_slider( **kwargs )
        self._update(0)

    def get_xy_coords(self, iPlot: int ) -> Tuple[ np.ndarray, np.ndarray ]:
        return self.get_coord( iPlot, self.x_axis ), self.get_coord( iPlot, self.y_axis )

    def get_anim_coord(self, iPlot: int ) -> np.ndarray:
        return self.get_coord( iPlot, 0 )

    def get_coord(self, iPlot: int, iCoord: int ) -> np.ndarray:
        data = self.data[iPlot]
        return data.coords[ data.dims[iCoord] ].values

    def getSubplotShape(self ) -> List[int]:
        ncols = math.floor( math.sqrt( self.nPlots ) )
        nrows = math.ceil( self.nPlots / ncols )
        return [ nrows, ncols ]

    def getSubplot( self, iPlot: int  ) -> SubplotBase:
        if self.plot_grid_shape == [1, 1]: return self.plot_axes
        if self.plot_grid_shape[0] == 1: return self.plot_axes[iPlot]
        plot_coords = [ iPlot//self.plot_grid_shape[1], iPlot % self.plot_grid_shape[1]  ]
        return self.plot_axes[ plot_coords[0], plot_coords[1] ]

    def create_cmap( self, **kwargs ):
        self.cmap = kwargs.get("cmap")
        self.cnorm = None
        if self.cmap is None:
            colors = kwargs.get("colors")
            if colors is None:
                self.cmap = "jet"
            else:
                self.cnorm = Normalize(0, len(colors))
                self.cmap = LinearSegmentedColormap.from_list("custom colors", colors, N=4)

    def create_image1(self, iPlot: int ) -> QuadMesh:
        data = self.data[iPlot]
        subplot: SubplotBase = self.getSubplot( iPlot )
        image: QuadMesh = data.isel(**{self.z_axis_name:0}).plot(ax=subplot)
        return image

    def create_image2(self, iPlot: int ) -> QuadMesh:
        data = self.data[iPlot]
        subplot: SubplotBase = self.getSubplot( iPlot )
        image: QuadMesh =  subplot.pcolormesh(data.isel(**{self.z_axis_name:0}))
        return image

    def create_image(self, iPlot: int ) -> AxesImage:
        from geoproc.plot.plot import imshow
        data = self.data[iPlot]
        subplot: SubplotBase = self.getSubplot( iPlot )
#        x, y = self.get_xy_coords( iPlot )
        z =  data[ 0, :, : ]   # .transpose()
        image: AxesImage = imshow( z, ax=subplot, cmap=self.cmap, norm=self.cnorm )
        subplot.title.set_text( data.name )
        # x_coord, y_coord = self.get_xy_coords( iPlot )
        # dx2, dy2 = x_coord[1] - x_coord[0], y_coord[0] - y_coord[1]
        # image.set_extent( [ x_coord[0] - dx2,  x_coord[-1] + dx2,  y_coord[-1] - dy2,  y_coord[0] + dy2 ] )
        return image

    def update_plots(self, iFrame: int ):
        for iPlot in range(self.nPlots):
            subplot: SubplotBase = self.getSubplot(iPlot)
            data = self.data[iPlot]
            self.images[iPlot].set_data( data[iFrame,:,:] )
#            self.images[iPlot].set_array( data[iFrame,:,:].values.ravel() )
            acoord = self.get_anim_coord( iPlot )
            subplot.title.set_text( f"{data.name}: {acoord[iFrame]}" )

    def add_plots(self, **kwargs ):
        for iPlot in range(self.nPlots):
            self.images[iPlot] = self.create_image( iPlot )
#        divider = make_axes_locatable(self.plot_axes)
#        cax = divider.append_axes('right', size='5%', pad=0.05)
#        self.figure.colorbar( self.images[self.nPlots-1], cax=cax, orientation='vertical')

    def add_slider(self,  **kwargs ):
        self.slider = PageSlider( self.slider_axes, self.nFrames )
        self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        i = int( self.slider.val )
        self.update_plots(i)

#        self.plot_axes.title.set_text( f"Frame {i+1}: {self.anim_coord[i]}" )

    def show(self):
        self.slider.start()
        plt.show()


class ArrayListAnimation:

    def __init__(self, dataset: Union[xa.Dataset,List[xa.DataArray]], **kwargs ):
        self.data: List[xa.DataArray] = dataset if isinstance(dataset, list) else ( list(dataset.data_vars.values()) if isinstance(dataset, xa.Dataset) else None )
        assert self.data is not None, " Input must be either xa.Dataset or List[xa.DataArray]"
        for dvar in self.data:
            assert dvar.ndim == 2, f"This plotter only works with 2 dimensional [y,x] data arrays.  Found {dvar.dims}"
        self.plot_axes = None
        self.figure: Figure = None
        self.image: AxesImage = None
        self.figure, self.plot_axes = plt.subplots()
        self.figure.suptitle( kwargs.get("title",""), fontsize=14 )
        self.figure.subplots_adjust(bottom=0.18)
        self.slider_axes: SubplotBase = self.figure.add_axes([0.1, 0.05, 0.8, 0.04])  # [left, bottom, width, height]
        self.x_axis = kwargs.get( 'x', 1 )
        self.x_axis_name = self.data[0].dims[ self.x_axis ]
        self.y_axis = kwargs.get( 'y', 0 )
        self.y_axis_name = self.data[0].dims[ self.y_axis ]

        self.nFrames = len(self.data)
        self.create_cmap( **kwargs )
        self.add_plot(**kwargs)
        self.add_slider( **kwargs )
        self._update(0)

    def get_xy_coords(self) -> Tuple[ np.ndarray, np.ndarray ]:
        return self.get_coord( self.x_axis ), self.get_coord( self.y_axis )

    def get_anim_coord(self ) -> np.ndarray:
        return self.get_coord( 0 )

    def get_coord(self, iCoord: int ) -> np.ndarray:
        return self.data[0].coords[ self.data[0].dims[iCoord] ].values

    def create_cmap( self, **kwargs ):
        self.cmap = kwargs.get("cmap")
        self.cnorm = None
        if self.cmap is None:
            colors = kwargs.get("colors")
            if colors is None:
                self.cmap = "jet"
            else:
                self.cnorm = Normalize(0, len(colors))
                self.cmap = LinearSegmentedColormap.from_list("custom colors", colors, N=4)

    def create_image(self ) -> AxesImage:
        from geoproc.plot.plot import imshow
        z =  self.data[ 0 ]   # .transpose()
        image: AxesImage = imshow( z, ax=self.plot_axes, cmap=self.cmap, norm=self.cnorm )
        self.plot_axes.title.set_text( z.name )
        return image

    def update_plot(self, iFrame: int):
        data = self.data[iFrame]
        self.image.set_data( data[:,:] )
        acoord = self.get_anim_coord()
        self.plot_axes.title.set_text( f"{data.name}: {acoord[iFrame]}" )

    def add_plot(self, **kwargs):
        self.image = self.create_image( )

    def add_slider(self,  **kwargs ):
        self.slider = PageSlider( self.slider_axes, self.nFrames )
        self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        i = int( self.slider.val )
        self.update_plot(i)

    def show(self):
        self.slider.start()
        plt.show()


if __name__ == "__main__":
    from geoproc.util.configuration import Region
    from geoproc.data.mwp import MWPDataManager

    colors = [ (0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0) ]
    locations = [ "120W050N", "100W040N" ]
    products = [ "1D1OS", "2D2OT" , "3D3OT" ]
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location: str = locations[0]
    product = products[0]
    year = 2019
    download = False
    roi = None
    bbox = Region( [3000,3500], 750 )
    time_index_range = [ 0, 365 ]

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults( product=product, download=download, year=2019, start_day=time_index_range[0], end_day=time_index_range[1] ) # , bbox=bbox )
    tile_data = dataMgr.get_tile_data( location, True )

    animation = SliceAnimation( tile_data, title='MPW Time Slice Animation', colors=colors )
    animation.show()
