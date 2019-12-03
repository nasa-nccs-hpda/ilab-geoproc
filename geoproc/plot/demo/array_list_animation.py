from geoproc.plot.animation import ArrayListAnimation
import xarray as xa

# DATA_FILE = "/att/pubrepo/ILAB/scratch/results/PyTest/world_clim/merra2_mth-WorldClim.nc"
DATA_FILE = "/Users/tpmaxwel/Dropbox/Tom/Data/WorldClim/MERRA/merra2-mth-WorldClim-2000.nc"
dataset: xa.Dataset = xa.open_dataset( DATA_FILE )
print( f"Animating data vars: {dataset.data_vars.keys()}")

animator = ArrayListAnimation( dataset )
animator.show()