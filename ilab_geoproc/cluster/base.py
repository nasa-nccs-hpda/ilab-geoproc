from typing import Dict, Any, Optional
import traceback, time, requests
from geoproc.util.scrap.logging import ILABLogger
import abc

from threading import Thread


class ClusterManagerBase:
      __metaclass__ = abc.ABCMeta

      def __init__(self, serverConfiguration: Dict[str, Any]):
          self.config = serverConfiguration
          self.logger = ILABLogger.getLogger()
          self.client = self.getClient()
          self.ncores = self.client.ncores()
          self.logger.info(f" ncores: {self.ncores}")
          self.scheduler_info = self.client.scheduler_info()
          self.workers: Dict = self.scheduler_info.pop("workers")
          self.logger.info(f" workers: {self.workers}")
          self.active = True
          log_metrics = serverConfiguration.get("log.scheduler.metrics", False )
          if log_metrics:
            self.metricsThread =  Thread( target=self.trackMetrics )
            self.metricsThread.start()

      def __enter__(self):
         return self

      def __exit__(self, exc_type, exc_value, tb):
         if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
         self.term()

      @abc.abstractmethod
      def getClient(self): pass

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

