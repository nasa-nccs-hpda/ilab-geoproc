import matplotlib.widgets
import matplotlib.patches
import mpl_toolkits.axes_grid1
import xarray as xa
from typing import List, Union, Dict
import time, math

class PageSlider(matplotlib.widgets.Slider):

    def __init__(self, ax, label, numpages = 10, valinit=0, valfmt='%1d', **kwargs ):
        self.facecolor=kwargs.get('facecolor',"yellow")
        self.activecolor = kwargs.pop('activecolor',"blue")
        self.fontsize = kwargs.pop('fontsize', 10)
        self.maxIndexedPages = 24
        self.numpages = numpages

        super(PageSlider, self).__init__(ax, label, 0, numpages, valinit=valinit, valfmt=valfmt, **kwargs)

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
        self.button_back = matplotlib.widgets.Button(bax, label='$\u25C0$', color=self.facecolor, hovercolor=self.activecolor)
        self.button_forward = matplotlib.widgets.Button(fax, label='$\u25B6$', color=self.facecolor, hovercolor=self.activecolor)
        self.button_back.label.set_fontsize(self.fontsize)
        self.button_forward.label.set_fontsize(self.fontsize)
        self.button_back.on_clicked(self.backward)
        self.button_forward.on_clicked(self.forward)

    def _update(self, event):
        super(PageSlider, self)._update(event)
        i = int(self.val)
        if i >=self.valmax:
            return
        self._colorize(i)

    def _colorize(self, i):
        for j in range(self.numpages):
            self.pageRects[j].set_facecolor(self.facecolor)
        self.pageRects[i].set_facecolor(self.activecolor)

    def forward(self, event):
        current_i = int(self.val)
        i = current_i+1
        if (i < self.valmin) or (i >= self.valmax):
            return
        self.set_val(i)
        self._colorize(i)

    def backward(self, event):
        current_i = int(self.val)
        i = current_i-1
        if (i < self.valmin) or (i >= self.valmax):
            return
        self.set_val(i)
        self._colorize(i)

class SliceAnimation:

    def __init__(self, data_array: xa.DataArray, axes: Dict, **kwargs ):
        self.data = data_array
        assert data_array.ndim == 3, f"This plotter only works with 3 dimensional [t,y,x] data arrays.  Found {data_array.dims}"
        self.anim_coord = data_array.coords[ data_array.dims[0] ]
        self.y_coord = data_array.coords[data_array.dims[1]].values
        self.x_coord = data_array.coords[data_array.dims[2]].values
        self.frame_names = data_array.attrs.get("names")
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
            self.slider = PageSlider( self.ax_slider, 'Frame', self.nFrames )
            self.slider_cid = self.slider.on_changed(self._update)

    def _update( self, val ):
        i = int( self.slider.val )
        self.image.set_data( data_array[i,:,:] )
        frame_title = self.frame_names[i] if self.frame_names is not None else str( self.anim_coord[i] )
        self.ax_plot.title.set_text( f"Frame {i+1}: {frame_title}" )


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
    fig.subplots_adjust(bottom=0.18)
    ax_slider = fig.add_axes([0.1, 0.05, 0.8, 0.04])    # [left, bottom, width, height]
    axes = dict( plot=ax, slider=ax_slider )

    animation = SliceAnimation( data_array, axes, colors=colors )

    plt.show()