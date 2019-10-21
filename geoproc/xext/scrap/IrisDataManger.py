from geoproc.util.configuration import ConfigurableObject, Region
from geoproc.data.mwp import MWPDataManager
import iris, xarray as xa



class IrisDataManager(ConfigurableObject):

    def __init__(self, data_dir: str, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        self.data_dir = data_dir

    def get_cube_data(self, files: Union[str,List[str]] ):
        if not isinstance(files, list): files = [files]
        assert len( files ) > 0, "Attempt to open empty list of files"
        try:
            return iris.load( files )
        except Exception:
            bbox: Region = self.getParameter("bbox")
            data_arrays: List[xa.DataArray]
            if files[0].endswith( "tif" ):
                if bbox is None:    data_arrays = [xa.open_rasterio(file)[0] for file in files]
                else:               data_arrays = [xa.open_rasterio(file)[0, bbox.origin[0]:bbox.bounds[0], bbox.origin[1]:bbox.bounds[1]] for file in files]
            else:
                dset = xa.open_mfdataset(files) if len(files) > 1 else xa.open_dataset(files[0])
                data_arrays = dset.data_vars.values()
            return [ array.to_iris() for array in data_arrays ]


if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
    location = "120W050N"
    dataMgr = MWPDataManager( DATA_DIR, "https://floodmap.modaps.eosdis.nasa.gov/Products" )
    dataMgr.setDefaults( product = "1D1OS", download = True, year = 2019, start_day = 1, end_day = 365 )
    files = dataMgr.get_tile(location, download = False)

    irisDataMgr = IrisDataManager( DATA_DIR )
    cubes = irisDataMgr.get_cube_data( files )
    print( cubes )


