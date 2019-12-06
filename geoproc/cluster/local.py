from typing import Dict, Any, Union, List, Callable, Optional
import traceback, time, logging, xml, socket, abc, dask, threading, requests, json
from dask.distributed import Client, Future, LocalCluster
from dask_jobqueue import SLURMCluster
from geoproc.util.logging import ILABLogger
import random, string, os, queue, datetime, atexit, multiprocessing, errno, uuid, abc
from geoproc.cluster.base import ClusterManagerBase
from threading import Thread
import xarray as xa

class LocalClusterManager(ClusterManagerBase):

    def __init__( self, serverConfiguration: Dict[str,Any] ):
      self.nWorkers = serverConfiguration.get("scheduler.nworkers", 4 )
      ClusterManagerBase.__init__( self, serverConfiguration )
      self.scheduler_address = self.client.scheduler.address
      self.logger.info(f"Initializing Local Dask cluster with {self.nWorkers} workers,  scheduler address = {self.scheduler_address}")

    def getClient(self):
      return Client( LocalCluster(n_workers=self.nWorkers) )

class PersistentLocalClusterManager(LocalClusterManager):
  manager: "PersistentLocalClusterManager" = None

  @classmethod
  def getManager( cls ) -> Optional["PersistentLocalClusterManager"]:
      return cls.manager

  @classmethod
  def initManager( cls, serverConfiguration: Dict[str,str] ) -> "PersistentLocalClusterManager":
      if cls.manager is None:
          cls.manager = PersistentLocalClusterManager(serverConfiguration)
      return cls.manager

  def __init__( self, serverConfiguration: Dict[str,str] ):
      LocalClusterManager.__init__( self, serverConfiguration )




