from geoproc.util.scrap.logging import ILABLogger
import traceback
from typing import Dict, Any


class ClusterManager:

    def __init__(self, serverConfiguration: Dict[str,Any]):
        self.logger = ILABLogger.getLogger()
        self.type = serverConfiguration.get('type','local')
        if self.type == "slurm":
            from geoproc.cluster.slurm import SlurmClusterManager
            self.mgr = SlurmClusterManager( serverConfiguration )
        else:
            from geoproc.cluster.local import LocalClusterManager
            self.mgr = LocalClusterManager( serverConfiguration )
        self.logger.info( f"Using {self.type} Cluster Manager for Dask/xarray, Dashboard: '{self.mgr.getDashboardAddress()}'" )

    def __enter__(self):
         return self.mgr

    def __exit__(self, exc_type, exc_value, tb):
         if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
         if self.mgr is not None:
             self.mgr.term()


if __name__ == '__main__':

    cluster_parameters = {'type': 'local'}
    with ClusterManager( cluster_parameters ) as clusterMgr:
        print("TEST1")