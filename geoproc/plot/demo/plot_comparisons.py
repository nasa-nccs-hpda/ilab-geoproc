import os
import xarray as xa
from typing import List, Union, Tuple, Dict
from geoproc.xext.xgeo import XGeo
from geoproc.plot.animation import PlotComparisons

wclimDataLocation = "/Users/tpmaxwel/.edas/cache/results/PyTest/world_clim/merra2-mth-WorldClim_1990-1999.nc"
dataset: xa.Dataset = xa.open_dataset( wclimDataLocation )
vars: Dict[int,str] = { idx: f"bio-{idx+1}[mul[subset[moist]]]" for idx in range(19) }
wclim_arrays: Dict[int,xa.DataArray] = { idx: dataset[vname] for idx,vname in vars.items() }

refDataLocation = "/Users/tpmaxwel/Dropbox/Tom/Data/WorldClim/MERRA/"
files: Dict[int,str] = { idx: f"MERRA_10m_mean_90s/10m_mean_90s_bio{idx+1}.tif" for idx in range(19) }                                # {(idx+1):02}
ref_arrays: Dict[int,xa.DataArray] = { idx: XGeo.loadRasterFile( os.path.join(refDataLocation,file) ) for idx,file in files.items() }

comparison_data: Dict[str,Dict[int,xa.DataArray]]  = { "Computed":wclim_arrays, "Reference":ref_arrays }
comparisons = PlotComparisons( comparison_data )
comparisons.show()

