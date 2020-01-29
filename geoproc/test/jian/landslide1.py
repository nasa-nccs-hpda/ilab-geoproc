import xarray as xa
import os, time
from geoproc.cluster.manager import ClusterManager

DATA_DIR = "/att/nobackup/jli30/workspace/landslide/perf_test"
image_file = os.path.join( DATA_DIR, "4551910_2016-01-02_RE4_3A_Analytic.tif" )
result_file = os.path.join( DATA_DIR, "4551910_2016-01-02_RE4_3A_var.nc" )
block = dict(x=5, y=5)
band_index = 3

if __name__ == '__main__':

    t0 = time.time()
    cluster_parameters = {'type': 'slurm'}
    with ClusterManager( cluster_parameters ) as clusterMgr:

        data_array: xa.DataArray = xa.open_rasterio(image_file)
        band_data: xa.DataArray  = data_array.sel( band=band_index, drop=True )

        print( " * Band Data: " )
        print( band_data.dims )
        print( band_data.shape )

        var_array: xa.DataArray = band_data.coarsen( **block, boundary='pad' ).var()

        print(" \n *Var Data: ")
        print( var_array.dims )
        print( var_array.shape )

        var_array.to_netcdf( result_file )

        print(f" \n Completed operation in {time.time()-t0} seconds, wrote output to {result_file} ")









