from geoproc.data.dataserver import CIP
from geoproc.xext.xplot import XGeoDS
import xarray as xr

tas_data_address = CIP("merra2", "tas")

dataset = xr.open_dataset(tas_data_address)

dataset.xplot.animate( )
