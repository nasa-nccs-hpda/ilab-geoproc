from geoproc.chaos.data import ProjectDataSource
import numpy as np
import xarray as xa
import matplotlib.pyplot as plt

npoints = 24
start = 0
series_name = "pdo_timeseries_mon"  #  "amo_timeseries_mon", "pdo_timeseries_mon", "indian_ocean_dipole", "nino34"
source = ProjectDataSource( "HadISST_1.cvdp_data.1980-2017" )
dset: xa.Dataset = source.getDataset( )
variable: xa.DataArray = dset[ series_name ]
if npoints <= 0:
    x = variable[:-1]
    y = variable[1:]
else:
    x = variable[start:npoints]
    y = variable[start+1:npoints+1]

plt.scatter( x, y, s=10 )
plt.plot(x, y, 'C3', lw=1)
plt.show()