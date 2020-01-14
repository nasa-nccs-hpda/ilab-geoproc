import xarray as xr, regionmask, utm
from typing import List, Union, Tuple
from geoproc.xext.xextension import XExtension
from geoproc.plot.animation import SliceAnimation

@xr.register_dataarray_accessor('xplot')
class XPlot(XExtension):
    """  This is an extension for xarray DataArrays to provide an interface to matplotlib capabilities """

    def __init__(self, xarray_obj: xr.DataArray):
        XExtension.__init__( self, xarray_obj )

    def animate(self, **kwargs ):
        animation = SliceAnimation( self._obj, **kwargs )
        animation.show()

@xr.register_dataset_accessor('xplot')
class XPlotDS:
    """  This is an extension for xarray Datasets to provide an interface to matplotlib capabilities """

    def __init__( self, dset: xr.Dataset ):
        self._dset = dset

    def animate(self, **kwargs ):
        vars = kwargs.get( "vars", self.get_data_vars() )
        data_arrays = [ self._dset[vname] for vname in vars ]
        animation = SliceAnimation( data_arrays, **kwargs )
        animation.show()

    def get_data_vars(self) -> List[str]:
        data_vars = []
        for (key,dval) in self._dset.data_vars.items():
            if not( key.endswith("_bnds") or "bnds" in dval.coords.keys() ):
                data_vars.append( key )
        return data_vars


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
    time_index_range = [ 0, 365 ]

    dataMgr = MWPDataManager(DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products")
    dataMgr.setDefaults( product=product, download=download, year=2019, start_day=time_index_range[0], end_day=time_index_range[1] ) # , bbox=bbox )
    data_array: xr.DataArray = dataMgr.get_tile_data( location, True )

    data_array.xplot.animate( title='MPW Time Slice Animation', colors=colors )



