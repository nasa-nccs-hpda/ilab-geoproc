import xarray as xa
import os, time
import matplotlib.pyplot as plt

DATA_DIR = "/att/nobackup/jli30/workspace/landslide/perf_test"
image_file = os.path.join( DATA_DIR, "4551910_2016-01-02_RE4_3A_Analytic.tif" )
result_file =  "/tmp/4551910_2016-01-02_RE4_3A_var.nc"

block = dict(x=5, y=5)
band_index = 3

t0 = time.time()

data_array: xa.DataArray = xa.open_rasterio( image_file )
band_data: xa.DataArray  = data_array.sel( band=band_index, drop=True )
var_array: xa.DataArray = band_data.coarsen( **block, boundary='pad' ).var()
var_array.name = "band_3_var_5x5"
var_array.to_netcdf( result_file )

print(f" \n Completed operation in {time.time()-t0} seconds, wrote output to {result_file}, data range = [ {band_data.min().values[0]}, {band_data.max().values[0]} ] ")

fig, ax = plt.subplots()
im = ax.imshow( var_array.values, cmap="jet", vmin=var_array.min().values[0], vmax=var_array.max().values[0] )
plt.show()




