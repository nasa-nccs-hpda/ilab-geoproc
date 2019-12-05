from typing import Dict, Any, Union, List, Callable, Optional
import traceback, time, logging, xml, socket, abc, dask, threading, requests, json
from dask.distributed import Client, Future, LocalCluster
from dask_jobqueue import SLURMCluster
from geoproc.util.logging import ILABLogger
import random, string, os, queue, datetime, atexit, multiprocessing, errno, uuid, abc
from threading import Thread
import xarray as xa

class ClusterManager:

    def __init__(self, serverConfiguration: Dict[str,Any]):
        self.type = serverConfiguration.get('type','local')
        self.logger = ILABLogger.getLogger()
        self.mgr = None
        if self.type == "slurm":
            self.mgr = SlurmClusterManager( serverConfiguration )
        self.logger.info( f"Using {self.type} Cluster Manager for Dask/xarray" )

    def __enter__(self):
        return self.mgr

    def __exit__(self):
        if self.mgr is not None:
            self.mgr.term()

class ClusterManagerBase:
    __metaclass__ = abc.ABCMeta

    def __init__(self, serverConfiguration: Dict[str, Any]):
        self.config = serverConfiguration
        self.logger = ILABLogger.getLogger()

    def __enter__(self):
        return self

    def __exit__(self):
        self.term()

    @abc.abstractmethod
    def term(self): pass

class SlurmClusterManager(ClusterManagerBase):

  def __init__( self, serverConfiguration: Dict[str,Any] ):
      ClusterManagerBase.__init__( self, serverConfiguration )
      self.num_wps_requests = 0
      self.maxworkers = serverConfiguration.get("scheduler.maxworkers", 16 )
      self.queue = serverConfiguration.get( "scheduler.queue", "default" )
      self.submitters = []
      self.slurm_clusters = {}
      self.active = True
      self.client = Client( self.getSlurmCluster(self.queue) )
      self.ncores = self.client.ncores()
      self.logger.info(f" ncores: {self.ncores}")
      self.scheduler_info = self.client.scheduler_info()
      self.workers: Dict = self.scheduler_info.pop("workers")
      self.logger.info(f" workers: {self.workers}")
      log_metrics = serverConfiguration.get("log.scheduler.metrics", False )
      if log_metrics:
        self.metricsThread =  Thread( target=self.trackMetrics )
        self.metricsThread.start()

  def getSlurmCluster( self, queue: str ):
      self.logger.info( f"Initializing Slurm cluster using queue {queue}" )
      cluster =  self.slurm_clusters.setdefault( queue, SLURMCluster() if queue == "default" else SLURMCluster( queue=queue ) )
      cluster.adapt( minimum=1, maximum=self.maxworkers, interval="2s", wait_count=500 )
      print( "CLUSTER JOB SCRIPT: " + cluster.job_script() )
      return cluster

  def getCWTMetrics(self) -> Dict:
      metrics_data = { key:{} for key in ['user_jobs_queued','user_jobs_running','wps_requests','cpu_ave','cpu_count','memory_usage','memory_available']}
      metrics = { "counts": self.getCounts(), "workers": self.getWorkerMetrics() }
      counts = metrics["counts"]
      workers = metrics["workers"]
      for key in ['tasks','processing','released','memory','saturated','waiting','waiting_data','unrunnable']: metrics_data['user_jobs_running'][key] = counts[key]
      for key in ['tasks', 'waiting', 'waiting_data', 'unrunnable']: metrics_data['user_jobs_queued'][key] = counts[key]
      for wId, wData in workers.items():
          worker_metrics = wData["metrics"]
          total_memory   = wData["memory_limit"]
          memory_usage = worker_metrics["memory"]
          metrics_data['memory_usage'][wId] = memory_usage
          metrics_data['memory_available'][wId] = total_memory - memory_usage
          metrics_data['cpu_count'][wId] = wData["ncores"]
          metrics_data['cpu_ave'][wId] = worker_metrics["cpu"]
      return metrics_data

  def trackMetrics(self, sleepTime=1.0 ):
      isIdle = False
      self.logger.info(f" ** TRACKING METRICS ** ")
      while self.active:
          metrics = { "counts": self.getCounts(), "workers": self.getWorkerMetrics() }
          counts = metrics["counts"]
          if counts['processing'] == 0:
              if not isIdle:
                self.logger.info(f" ** CLUSTER IS IDLE ** ")
                isIdle = True
          else:
              isIdle = False
              self.logger.info( f" METRICS: {metrics['counts']} " )
              workers = metrics["workers"]
              for key,value in workers.items():
                  self.logger.info( f" *** {key}: {value}" )
              self.logger.info(f" HEALTH: {self.getHealth()}")
              time.sleep( sleepTime )

  def getWorkerMetrics(self):
      metrics = {}
#      wkeys = [ 'ncores', 'memory_limit', 'last_seen', 'metrics' ]
      scheduler_info = self.client.scheduler_info()
      workers: Dict = scheduler_info.get( "workers", {} )
      for iW, worker in enumerate( workers.values() ):
          metrics[f"W{iW}"] = worker # { wkey: worker[wkey] for wkey in wkeys }
      return metrics

  def getDashboardAddress(self):
      return f"http://127.0.0.1:8787"

  def getCounts(self) -> Dict:
      profile_address = f"{self.getDashboardAddress()}/json/counts.json"
      return requests.get(profile_address).json()

  def getHealth(self, mtype: str = "" ) -> str:
      profile_address = f"{self.getDashboardAddress()}/health"
      return requests.get(profile_address).text

  def getMetrics(self, mtype: str = "" ) -> Optional[Dict]:
      counts = self.getCounts()
      if counts['processing'] == 0: return None
      mtypes = mtype.split(",")
      metrics = { "counts": counts }
      if "processing" in mtypes:  metrics["processing"] = self.client.processing()
      if "profile" in mtypes:     metrics["profile"]    = self.client.profile()
      return metrics

  def term(self):
      self.active = False
      time.sleep(0.1)
      self.client.close()


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