from typing import Dict, Any, Optional
from dask.distributed import Client
from dask_jobqueue import SLURMCluster
from geoproc.cluster.base import ClusterManagerBase


class SlurmClusterManager(ClusterManagerBase):

  def __init__( self, serverConfiguration: Dict[str,Any] ):
      self.slurm_clusters = {}
      self.cores = serverConfiguration.get( 'scheduler.ncores', 8 )
      self.maxworkers = serverConfiguration.get("scheduler.maxworkers", 16 )
      self.queue = serverConfiguration.get( "scheduler.queue", "default" )
      ClusterManagerBase.__init__( self, serverConfiguration )
      self.submitters = []

  def getClient(self):
      return Client( self.getSlurmCluster(self.queue) )

  def getSlurmCluster( self, queue: str ):
      self.logger.info( f"Initializing Slurm cluster using queue {queue}" )
      cluster =  self.slurm_clusters.setdefault( queue, SLURMCluster(cores = self.cores) if queue == "default" else SLURMCluster( queue=queue, cores = self.cores ) )
      cluster.adapt( minimum=1, maximum=self.maxworkers, interval="2s", wait_count=500 )
      print( "CLUSTER JOB SCRIPT: " + cluster.job_script() )
      return cluster


class PersistentSlurmClusterManager(SlurmClusterManager):
  manager: "PersistentSlurmClusterManager" = None

  @classmethod
  def getManager( cls ) -> Optional["PersistentSlurmClusterManager"]:
      return cls.manager

  @classmethod
  def initManager( cls, serverConfiguration: Dict[str,str] ) -> "PersistentSlurmClusterManager":
      if cls.manager is None:
          cls.manager = PersistentSlurmClusterManager(serverConfiguration)
      return cls.manager

  def __init__( self, serverConfiguration: Dict[str,str] ):
      SlurmClusterManager.__init__( self, serverConfiguration )