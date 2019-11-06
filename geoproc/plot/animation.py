import matplotlib.widgets
import matplotlib.patches
import mpl_toolkits.axes_grid1
from matplotlib.backend_bases import TimerBase
import matplotlib.pyplot as plt
from threading import  Thread
from matplotlib.figure import Figure
import xarray as xa
from typing import List, Union, Dict, Callable
import time, math, atexit
from enum import Enum

class ADirection(Enum):
    BACKWARD = -1
    STOP = 0
    FORWARD = 1

class EventSource(Thread):

    def __init__( self, action: Callable, delay = 0.1 ):
        Thread.__init__(self)
        self.event = None
        self.action = action
        self.interval = delay
        self.active = False
        self.running = True
        atexit.register( self.exit )

    def run(self):
        while self.running:
            time.sleep( self.interval )
            if self.active: self.action( self.event )

    def activate(self, delay = None ):
        if delay is not None: self.interval = delay
        self.active = True

    def deactivate(self):
        self.active = False

    def exit(self):
        print( "Exiting EventSource" )
        self.running = False

class PageSlider(matplotlib.widgets.Slider):


    def __init__(self, ax, numpages = 10, valinit=0, valfmt='%1d', **kwargs ):
        self.facecolor=kwargs.get('facecolor',"yellow")
        self.activecolor = kwargs.pop('activecolor',"blue" )
        self.stepcolor = kwargs.pop('stepcolor', "#ff6f6f" )
        self.animcolor = kwargs.pop('animcolor', "#6fff6f" )
        self.fontsize = kwargs.pop('fontsize', 10)
        self.figure = fig
        self.maxIndexedPages = 24
        self.numpages = numpages
        self.init_anim_delay: float = 0.5   # time between timer events in seconds
        self.anim_delay: float = self.init_anim_delay
        self.anim_delay_multiplier = 1.5
        self.anim_state = ADirection.STOP
        self.event_source = EventSource( self.step )
        self.event_source.start()

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

        divider = mpl_toolkits.axes_grid1.make_axes_locatable(ax)
        bax = divider.append_axes("right", size="5%", pad=0.05)
        fax = divider.append_axes("right", size="5%", pad=0.05)
        self.button_back = matplotlib.widgets.Button(bax, label='$\u25C1$', color=self.stepcolor, hovercolor=self.activecolor)
        self.button_forward = matplotlib.widgets.Button(fax, label='$\u25B7$', color=self.stepcolor, hovercolor=self.activecolor)
        self.button_back.label.set_fontsize(self.fontsize)
        self.button_forward.label.set_fontsize(self.fontsize)
        self.button_back.on_clicked(self.backward)
        self.button_forward.on_clicked(self.forward)

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
        print( f"Stepping, self.anim_state = {self.anim_state} ")
        if   self.anim_state == ADirection.FORWARD:  self.forward(event)
        elif self.anim_state == ADirection.BACKWARD: self.backward(event)

    def forward(self, event=None):
        self.anim_stop()
        current_i = int(self.val)
        i = current_i+1
        if i >= self.valmax: i = self.valmin
        self.set_val(i)
        self._colorize(i)

    def backward(self, event=None):
        self.anim_stop()
        current_i = int(self.val)
        i = current_i-1
        if i < self.valmin: i = self.valmax -1
        self.set_val(i)
        self._colorize(i)

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

    def anim_backward(self, event=None):
        if self.anim_state == ADirection.BACKWARD:
            self.anim_delay = self.anim_delay / self.anim_delay_multiplier
            self.event_source.interval = self.anim_delay
        elif self.anim_state == ADirection.BACKWARD:
            self.anim_delay = self.anim_delay * self.anim_delay_multiplier
            self.event_source.interval = self.anim_delay
        else:
            self.anim_delay = self.init_anim_delay
            self.anim_state = ADirection.BACKWARD
            self.event_source.activate( self.anim_delay )

    def anim_stop(self, event=None):
        if self.anim_state != ADirection.STOP:
            self.anim_delay = self.init_anim_delay
            self.anim_state = ADirection.STOP
            self.event_source.deactivate()

class SliceAnimation:

    def __init__(self, fig: Figure, data_array: xa.DataArray, axes: Dict, **kwargs ):
        self.data = data_array
        assert data_array.ndim == 3, f"This plotter only works with 3 dimensional [t,y,x] data arrays.  Found {data_array.dims}"
        self.anim_coord = data_array.coords[ data_array.dims[0] ].values
        self.y_coord = data_array.coords[data_array.dims[1]].values
        self.x_coord = data_array.coords[data_array.dims[2]].values
        self.anim_coord_name: str = data_array.coords[ data_array.dims[0] ].name
        self.figure = fig
        self.nFrames = data_array.shape[0]
        self.create_cmap( **kwargs )
        self.add_plot( axes, **kwargs )
        self.add_slider( axes, **kwargs )
        self._update(0)

    def create_cmap( self, **kwargs ):
        self.cmap = kwargs.get("cmap")
        self.cnorm = None
        if self.cmap is None:
            colors = kwargs.get("colors")
            if colors is not None:
                self.cnorm = Normalize(0, len(colors))
                self.cmap = LinearSegmentedColormap.from_list("custom colors", colors, N=4)

    def add_plot(self, axes: Dict, **kwargs ):
        self.ax_plot = axes.get("plot")
        self.image = self.ax_plot.imshow( self.data[0, :, :], cmap=self.cmap, norm=self.cnorm, interpolation='nearest')
        dx2, dy2 = self.x_coord[1] - self.x_coord[0], self.y_coord[0] - self.y_coord[1]
        self.image.set_extent( [self.x_coord[0]-dx2, self.x_coord[-1]+dx2, self.y_coord[-1]-dy2, self.y_coord[0]]+dy2 )

    def add_slider(self, axes: Dict, **kwargs ):
        self.slider = kwargs.get("slider")
        self.slider_cid = None
        self.ax_slider = axes.get("slider")
        if self.slider is not None:
            self.slider_cid = self.slider.on_changed(self._update)
        elif self.ax_slider is not None:
            self.slider = PageSlider( self.ax_slider, self.nFrames )
            self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        i = int( self.slider.val )
        self.image.set_data( data_array[i,:,:] )
        self.ax_plot.title.set_text( f"Frame {i+1}: {self.anim_coord[i]}" )

if __name__ == "__main__":
    from geoproc.util.configuration import Region
    from matplotlib import pyplot as plt
    from geoproc.data.mwp import MWPDataManager
    from matplotlib.colors import LinearSegmentedColormap, Normalize

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
    time_index_range = [ 190, 350 ]

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults( product=product, download=download, year=2019, start_day=time_index_range[0], end_day=time_index_range[1], bbox=bbox )
    data_array = dataMgr.get_tile_data( location, True )

    fig, ax = plt.subplots()
    fig.suptitle('MPW Time Slice Animation', fontsize=16)
    fig.subplots_adjust(bottom=0.18)
    ax_slider = fig.add_axes([0.1, 0.05, 0.8, 0.04])    # [left, bottom, width, height]
    axes = dict( plot=ax, slider=ax_slider )

    animation = SliceAnimation( fig, data_array, axes, colors=colors )

    plt.show()