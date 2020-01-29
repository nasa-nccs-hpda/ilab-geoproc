import xarray as xa
import os
from geoproc.cluster.manager import ClusterManager

DATA_DIR = "/att/nobackup/jli30/workspace/landslide/perf_test"
image_file = os.path.join( DATA_DIR, "4551910_2016-01-02_RE4_3A_Analytic.tif" )

if __name__ == '__main__':

    cluster_parameters = {'type': 'slurm'}
    with ClusterManager( cluster_parameters ) as clusterMgr:

        data_array = xa.open_rasterio(image_file)
        print( data_array.dims )
#        var_array = data_array.coarsen(time=7, x=2).mean()









