import os, itertools, datetime
import numpy as np
import logging, abc, traceback
from typing import List, Union, Dict, Any
import xarray as xa

class DataSource(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name ):
         # type: (str) -> None
        self.name = name
        self.rootDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    def getDataFilePath(self, type, ext ):
        # type: (str,str) -> str
        return os.path.join(os.path.join(self.rootDir, "data", type), self.name + "." + ext )

class ProjectDataSource(DataSource):

    def __init__(self, name ):
        DataSource.__init__( self, name )
        self.dataFile = self.getDataFilePath("cvdp","nc")

    def getDataset( self, **kwargs ) -> xa.Dataset :
        dataset: xa.Dataset = xa.open_dataset( self.dataFile, decode_times=False )
        return dataset

