import matplotlib.widgets
import matplotlib.patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap, Normalize, ListedColormap
import matplotlib.pyplot as plt
from threading import  Thread
from geoproc.util.configuration import sanitize, ConfigurableObject as BaseOp
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
import matplotlib as mpl
import xarray as xa
import numpy as np
from typing import List, Union, Dict, Callable, Tuple
import time, math, atexit, json
from enum import Enum

def get_color_bounds( color_values: List[float] ) -> List[float]:
    color_bounds = []
    for iC, cval in enumerate( color_values ):
        if iC == 0: color_bounds.append( cval - 0.5 )
        else: color_bounds.append( (cval + color_values[iC-1])/2.0 )
    color_bounds.append( color_values[-1] + 0.5 )
    return color_bounds


class ADirection(Enum):
    BACKWARD = -1
    STOP = 0
    FORWARD = 1

class EventSource(Thread):

    def __init__( self, action: Callable, **kwargs ):
        Thread.__init__(self)
        self.event = None
        self.action = action
        self.interval = kwargs.get( "delay",0.01 )
        self.active = False
        self.running = True
        self.daemon = True
        atexit.register( self.exit )

    def run(self):
        while self.running:
            time.sleep( self.interval )
            if self.active:
                plt.pause( 0.05 )
                self.action( self.event )

    def activate(self, delay = None ):
        if delay is not None: self.interval = delay
        self.active = True

    def deactivate(self):
        self.active = False

    def exit(self):
        self.running = False

class PageSlider(matplotlib.widgets.Slider):

    def __init__(self, ax: Axes, numpages = 10, valinit=0, valfmt='%1d', **kwargs ):
        self.facecolor=kwargs.get('facecolor',"yellow")
        self.activecolor = kwargs.pop('activecolor',"blue" )
        self.stepcolor = kwargs.pop('stepcolor', "#ff6f6f" )
        self.animcolor = kwargs.pop('animcolor', "#6fff6f" )
        self.on_animcolor = kwargs.pop('on-animcolor', "#006622")
        self.fontsize = kwargs.pop('fontsize', 10)
        self.animation_controls = kwargs.pop('dynamic', True )
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

        if self.animation_controls:
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
        if self.animation_controls:
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
        self.frames: np.ndarray = None
        self.metrics_scale =  kwargs.get( 'metrics_scale', None )
        self.data: List[xa.DataArray] = self.preprocess_inputs(data_arrays)
        self.plot_axes = None
        self.auxplot = kwargs.get( "auxplot", None )
        self.metrics_alpha = kwargs.get( "metrics_alpha", 0.7 )
        self.figure: Figure = None
        self.images: Dict[int,AxesImage] = {}
        self.nPlots = len(self.data)
        self.metrics: Dict = kwargs.get("metrics", {})
        self.frame_marker: Line2D = None
        self.setup_plots(**kwargs)
        self.z_axis = kwargs.pop('z', 0)
        self.z_axis_name = self.data[0].dims[ self.z_axis ]
        self.x_axis = kwargs.pop( 'x', 2 )
        self.x_axis_name = self.data[0].dims[ self.x_axis ]
        self.y_axis = kwargs.pop( 'y', 1 )
        self.y_axis_name = self.data[0].dims[ self.y_axis ]

        self.add_plots( **kwargs )
        self.add_slider( **kwargs )
        self._update(0)

    def preprocess_inputs(self, data_arrays: Union[xa.DataArray,List[xa.DataArray]]  ) -> List[xa.DataArray]:
        inputs_list = data_arrays if isinstance(data_arrays, list) else [data_arrays]
        preprocessed_inputs: List[xa.DataArray] = [ self.preprocess_input(input) for input in inputs_list ]
        axis0_lens = [ processed_input.shape[0] for processed_input in preprocessed_inputs ]
        self.nFrames = max(axis0_lens)
        target_input = preprocessed_inputs[ axis0_lens.index( self.nFrames ) ]
        self.frames = target_input.coords[ target_input.dims[0] ].values
        return preprocessed_inputs

    @classmethod
    def preprocess_input(cls, dataArray: xa.DataArray ) -> xa.DataArray:
        if dataArray.ndim == 3: return dataArray
        if 'time' not in dataArray.dims:
            return BaseOp.time_merge([dataArray])
        else:
            raise Exception( f"This plotter only works with 3 dimensional [t,y,x] data arrays.  Found {dataArray.dims}" )

    def setup_plots( self, **kwargs ):
        self.plot_grid_shape: List[int] = self.getSubplotShape( len(self.metrics)>0 )  # [ rows, cols ]
        if self.nPlots == 1 and len( self.metrics ) > 0:
            self.plot_axes = np.arange(2)
            self.figure = plt.figure()
            gs = self.figure.add_gridspec(2, 3)
            if self.auxplot is None:
                self.plot_axes = np.array( [ self.figure.add_subplot( gs[:, :-1] ), self.figure.add_subplot( gs[:,  -1] ) ] )
            else:
                self.plot_axes = np.array([self.figure.add_subplot(gs[:, :-1]), self.figure.add_subplot(gs[0, -1]), self.figure.add_subplot(gs[1, -1]) ])

        else:
            self.figure, self.plot_axes = plt.subplots( *self.plot_grid_shape )

        self.figure.subplots_adjust(bottom=0.12) # 0.18)
        self.figure.suptitle( kwargs.get("title",""), fontsize=14 )
        self.slider_axes: Axes = self.figure.add_axes([0.1, 0.05, 0.8, 0.04])  # [left, bottom, width, height]

    def invert_yaxis(self):
        from matplotlib.artist import Artist
        if isinstance( self.plot_axes, Artist ):
            self.plot_axes.invert_yaxis()
        else:
            self.plot_axes[0].invert_yaxis()

    def get_xy_coords(self, iPlot: int ) -> Tuple[ np.ndarray, np.ndarray ]:
        return self.get_coord( iPlot, self.x_axis ), self.get_coord( iPlot, self.y_axis )

    def get_anim_coord(self, iPlot: int ) -> np.ndarray:
        return self.get_coord( iPlot, 0 )

    def get_coord(self, iPlot: int, iCoord: int ) -> np.ndarray:
        data = self.data[iPlot]
        return data.coords[ data.dims[iCoord] ].values

    def getSubplotShape(self, has_diagnostics: bool  ) -> List[int]:
        nCells = self.nPlots+1 if has_diagnostics else self.nPlots
        nrows = math.floor( math.sqrt( nCells ) )
        ncols = math.ceil( nCells / nrows )
        return [ nrows, ncols ]

    def getSubplot( self, iPlot: int  ) -> Axes:
        if self.plot_grid_shape == [1, 1]: return self.plot_axes
        if len(self.plot_axes.shape) == 1: return self.plot_axes[iPlot]
        plot_coords = [ iPlot//self.plot_grid_shape[1], iPlot % self.plot_grid_shape[1]  ]
        return self.plot_axes[ plot_coords[0], plot_coords[1] ]

    def create_cmap( self, cmap_spec: Union[str,Dict] ):
        if isinstance(cmap_spec,str):
            cmap_spec =  json.loads(cmap_spec)
        range = cmap_spec.pop("range",None)
        colors = cmap_spec.pop("colors",None)
        if colors is None:
            cmap = cmap_spec.pop("cmap","jet")
            norm = Normalize(*range) if range else None
            return dict( cmap=cmap, norm=norm, cbar_kwargs=dict(cmap=cmap, norm=norm, orientation='horizontal'), tick_labels=None )
        else:
            if isinstance( colors, np.ndarray ):
                return dict( cmap=LinearSegmentedColormap.from_list('my_colormap', colors) )
            rgbs = [ cval[2] for cval in colors ]
            cmap: ListedColormap = ListedColormap( rgbs )
            tick_labels = [ cval[1] for cval in colors ]
            color_values = [ float(cval[0]) for cval in colors]
            color_bounds = get_color_bounds(color_values)
            norm = mpl.colors.BoundaryNorm( color_bounds, len( colors )  )
            cbar_args = dict( cmap=cmap, norm=norm, boundaries=color_bounds, ticks=color_values, spacing='proportional',  orientation='horizontal')
            return dict( cmap=cmap, norm=norm, cbar_kwargs=cbar_args, tick_labels=tick_labels )

    def update_metrics( self, iFrame: int ):
        if len( self.metrics ):
            axis: Axes = self.plot_axes[1]
            x = [iFrame, iFrame]
            y = [ axis.dataLim.y0, axis.dataLim.y1 ]
            if self.frame_marker == None:
                self.frame_marker, = axis.plot( x, y, color="yellow", lw=3, alpha=0.5 )
            else:
                self.frame_marker.set_data( x, y )

    def update_aux_plot( self, iFrame: int ):
        if (self.auxplot is not None) and (self.auxplot.shape[0] == self.nFrames):
            self.images[self.nPlots].set_data( self.auxplot[iFrame] )

    def create_image(self, iPlot: int, **kwargs ) -> AxesImage:
        data: xa.DataArray = self.data[iPlot]
        subplot: Axes = self.getSubplot( iPlot )
        cm = self.create_cmap( data.attrs.get("cmap",{}) )
        z: xa.DataArray =  data[ 0, :, : ]   # .transpose()
        color_tick_labels = cm.pop( 'tick_labels', None )
        image: AxesImage = z.plot.imshow( ax=subplot, **cm )
        if color_tick_labels is not None: image.colorbar.ax.set_xticklabels( color_tick_labels )
        subplot.title.set_text( data.name )
        overlays = kwargs.get( "overlays", {} )
        for color, overlay in overlays.items():
            overlay.plot( ax=subplot, color=color, linewidth=2 )
        return image

    def create_metrics_plot(self):
        if len( self.metrics ):
            axis = self.plot_axes[1]
            axis.title.set_text("Metrics")
            if self.metrics_scale is not None: axis.set_yscale( self.metrics_scale )
            markers = self.metrics.pop('markers',{})
            for color, values in self.metrics.items():
                x = range( len(values) )
                line, = axis.plot( x, values, color=color, alpha=self.metrics_alpha )
                line.set_label(values.name)
            for color, value in markers.items():
                x = [value, value]
                y = [axis.dataLim.y0, axis.dataLim.y1]
                line, = axis.plot(x, y, color=color)
            axis.legend()

    def create_aux_plot(self):
        if self.auxplot is not None:
            axis = self.plot_axes[2]
            axis.title.set_text("AuxPlot")
            cm = self.create_cmap( self.auxplot.attrs.get("cmap", {}) )
            color_tick_labels = cm.pop('tick_labels', None)
            z: xa.DataArray = self.auxplot[0]
            self.images[self.nPlots]  = z.plot.imshow( ax=axis, **cm )
            if color_tick_labels is not None: self.images[self.nPlots].colorbar.ax.set_yticklabels(color_tick_labels)
            axis.legend()

    def update_plots(self, iFrame: int ):
        tval = self.frames[ iFrame ]
        for iPlot in range(self.nPlots):
            subplot: Axes = self.getSubplot(iPlot)
            data = self.data[iPlot]
            frame_image = data.sel( **{ data.dims[0]: tval }, method='nearest' )
            try:                tval1 = frame_image.time.values
            except Exception:   tval1 = tval
            self.images[iPlot].set_data( frame_image )
            stval = str(tval1).split("T")[0]
            subplot.title.set_text( f"F-{iFrame} [{stval}]" )
        self.update_metrics( iFrame )
        self.update_aux_plot(iFrame)

    def onMetricsClick(self, event):
        if event.xdata != None and event.ydata != None:
            if len(self.metrics):
                axis: Axes = self.plot_axes[1]
                if event.inaxes == axis:
                    print( f"onMetricsClick: {event.xdata}" )
                    self.slider.set_val( round(event.xdata) )

    def add_plots(self, **kwargs ):
        for iPlot in range(self.nPlots):
            self.images[iPlot] = self.create_image( iPlot, **kwargs )
        self.create_metrics_plot()
        self.create_aux_plot()
        self._cid = self.figure.canvas.mpl_connect( 'button_press_event', self.onMetricsClick)

    def add_slider(self,  **kwargs ):
        self.slider = PageSlider( self.slider_axes, self.nFrames )
        self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        i = int( self.slider.val )
        self.update_plots(i)

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
        self.slider_axes: Axes = self.figure.add_axes([0.1, 0.05, 0.8, 0.04])  # [left, bottom, width, height]
        self.x_axis = kwargs.get( 'x', 1 )
        self.x_axis_name = self.data[0].dims[ self.x_axis ]
        self.y_axis = kwargs.get( 'y', 0 )
        self.y_axis_name = self.data[0].dims[ self.y_axis ]
        self.ranges = [ ( data.min(), data.max() ) for data in self.data ]

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
        self.norm = None
        if self.cmap is None:
            colors = kwargs.get("colors")
            if colors is None:
                self.cmap = "jet"
            else:
                self.norm = Normalize(0, len(colors))
                self.cmap = LinearSegmentedColormap.from_list("custom colors", colors, N=4)

    def create_image(self ) -> AxesImage:
        z =  self.data[ 0 ]   # .transpose()
        image: AxesImage = self.plot_axes.imshow( z, cmap=self.cmap, norm=self.norm )
        self.plot_axes.title.set_text( z.name )
        plt.colorbar(image, ax=self.plot_axes, cmap=self.cmap, norm=self.norm)
        return image

    def update_plot(self, iFrame: int):
        data: xa.DataArray = self.data[iFrame]
        self.plot_axes.title.set_text( f"{data.name}" )
        self.image.set_clim( *self.ranges[iFrame] )
        self.image.set_data( data[:,:] )

    def add_plot(self, **kwargs):
        self.image = self.create_image( )

    def add_slider(self,  **kwargs ):
        self.slider = PageSlider( self.slider_axes, self.nFrames, dynamic = False )
        self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        i = int( self.slider.val )
        self.update_plot(i)

    def show(self):
        self.slider.start()
        plt.show()

class PlotComparisons:

    def __init__(self, comparison_data: Dict[str,Dict[int,xa.DataArray]], **kwargs ):
        self.data: Dict[str,Dict[int,xa.DataArray]] = comparison_data
        assert self.data is not None, " Input must be either xa.Dataset or List[xa.DataArray]"
        for data_series in self.data.values():
            for dvar in data_series.values():
                assert dvar.ndim == 2, f"This plotter only works with 2 dimensional [y,x] data arrays.  Found {dvar.dims}"
        self.plot_axes = None
        self.figure: Figure = None
        self.images: Dict[str,AxesImage] = {}
        self.nPlots = len( self.data )
        self.nFrames = max([max(dSeries.keys()) for dSeries in self.data.values()])
        self.plot_grid_shape: List[int] = self.getSubplotShape( )  # [ rows, cols ]
        self.figure, self.plot_axes = plt.subplots( *self.plot_grid_shape )
        self.figure.suptitle( kwargs.get("title",""), fontsize=14 )
        self.figure.subplots_adjust(bottom=0.18)
        self.slider_axes: Axes = self.figure.add_axes([0.1, 0.05, 0.8, 0.04])  # [left, bottom, width, height]
        self.x_axis = kwargs.get( 'x', 1 )
        self.y_axis = kwargs.get( 'y', 0 )
        self.ranges: Dict[str,Dict[int,Tuple[float,float]]] = { seriesId: { frameId: (data.min(), data.max()) for frameId, data in seriesData.items() } for seriesId, seriesData in self.data.items() }
        self.frames = list(self.data.keys())
        self.create_cmap( **kwargs )
        for iPlot in range(self.nPlots):
            self.add_plot( iPlot, **kwargs )
        self.add_slider( **kwargs )
        self._update(0)

    def get_xy_coords(self, seriesId: str ) -> Tuple[ np.ndarray, np.ndarray ]:
        return self.get_coord( seriesId, self.x_axis ), self.get_coord( seriesId, self.y_axis )

    def get_anim_coord(self, seriesId: str ) -> np.ndarray:
        return self.get_coord( seriesId, 0 )

    def get_coord(self, seriesId: str, iCoord: int ) -> np.ndarray:
        dataArray = self.data[ seriesId ][0]
        return dataArray.coords[ dataArray.dims[iCoord] ].values

    def create_cmap( self, **kwargs ):
        self.cmap = kwargs.get("cmap")
        self.norm = None
        if self.cmap is None:
            colors = kwargs.get("colors")
            if colors is None:
                self.cmap = "jet"
            else:
                self.norm = Normalize(0, len(colors))
                self.cmap = LinearSegmentedColormap.from_list("custom colors", colors, N=4)

    def getPlotArgs(self, ax, seriesId: str ):
        x,y = self.get_xy_coords( seriesId )
        try: xstep = (x[1] - x[0]) / 2.0
        except IndexError: xstep = 0.1
        try:  ystep = (y[1] - y[0]) / 2.0
        except IndexError: ystep = 0.1
        left, right = x[0] - xstep, x[-1] + xstep
        bottom, top = y[-1] + ystep, y[0] - ystep
        defaults = { "interpolation": "nearest" }
        defaults["origin"] = "upper" if ystep < 0.0 else "lower"
        if not hasattr( ax, "projection" ): defaults["aspect"] = "auto"
        if defaults["origin"] == "upper":   defaults["extent"] = [left, right, bottom, top]
        else:                               defaults["extent"] = [left, right, top, bottom]
        return defaults

    def create_image(self, seriesId: str, iPlot: int ) -> AxesImage:
        dataSeries: Dict[int,xa.DataArray] = self.data[seriesId]
        range = self.ranges[seriesId].get(0)
        subplot: Axes = self.getSubplot(iPlot)
        z: xa.DataArray = dataSeries[0]
        plotArgs = self.getPlotArgs( subplot, seriesId )
        image: AxesImage = subplot.imshow( z, cmap=self.cmap, norm=self.norm, **plotArgs )
        if range is not None: image.set_clim( *range )
        image.axes.title.set_text(z.name)
        plt.colorbar(image, ax=subplot, cmap=self.cmap, norm=self.norm)
        return image

    def getSubplot( self, iPlot: int  ) -> Axes:
        if self.plot_grid_shape == [1, 1]: return self.plot_axes
        if self.plot_grid_shape[0] == 1 or self.plot_grid_shape[1] == 1:
            return self.plot_axes[iPlot]
        plot_coords = [ iPlot//self.plot_grid_shape[1], iPlot % self.plot_grid_shape[1]  ]
        return self.plot_axes[ plot_coords[0], plot_coords[1] ]

    def update_plot(self, seriesId: str, iFrame: int ):
        data: xa.DataArray = self.data[seriesId][iFrame]
        image = self.images[seriesId]
        range = self.ranges[seriesId].get(iFrame)
        if range is not None: image.set_clim( *range )
        image.axes.title.set_text( f"{data.name}" )
        image.set_data( data.values )

    def add_plot(self, iPlot: int, **kwargs):
        seriesId = self.frames[iPlot]
        self.images[seriesId] = self.create_image( seriesId, iPlot )

    def add_slider(self,  **kwargs ):
        self.slider = PageSlider( self.slider_axes, self.nFrames, dynamic = False )
        self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        iFrame = int( self.slider.val )
        for seriesId in self.data.keys():
            self.update_plot( seriesId, iFrame )

    def show(self):
        self.slider.start()
        plt.show()

    def getSubplotShape(self ) -> List[int]:
        n1 = math.floor( math.sqrt( self.nPlots ) )
        n0 = math.ceil( self.nPlots / n1 )
        return [ n0, n1 ]

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
