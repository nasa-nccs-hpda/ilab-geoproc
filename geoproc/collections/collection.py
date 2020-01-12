import os
from geoproc.util.configuration import ILABEnv
from geoproc.util.logging import ILABLogger
from datetime import datetime, timezone
from netCDF4 import MFDataset, Variable
from typing import List, Dict, Any, Sequence, BinaryIO, TextIO, ValuesView, Optional, Tuple
from edas.process.source import VID
from geoproc.collections.aggregation import Aggregation, File

class Collection:

    collDir = os.path.expanduser( ILABEnv.COLLECTIONS )

    @classmethod
    def getCollectionsList(cls):
        collList = []
        for f in os.listdir(cls.collDir):
            if( os.path.isfile(os.path.join(cls.collDir, f)) and f.endswith(".csv")):
                collection_name = f[0:-4]
                collection = Collection.new( collection_name )
                aggSpecs = [ '<variable name="{}" agg="{}"/>'.format( vName, aggName ) for vName,aggName in collection.aggs.items( )]
                collList.append( '<collection name="{}"> {} </collection>'.format( collection_name, " ".join( aggSpecs ) ) )
        return collList

    @classmethod
    def new(cls, name: str ):
        spec_file = os.path.join(cls.collDir, name + ".csv")
        return Collection(name, spec_file)

    def __init__(self, _name, _spec_file ):
        self.logger = ILABLogger.getLogger()
        self.name = _name
        self.spec = os.path.expanduser( _spec_file )
        self.aggs = {}
        self.parms = {}
        self._parseSpecFile()

    def _parseSpecFile(self):
        self.logger.info( f"Retreiving spec for collection {self.name} from spec file {self.spec}")
        assert os.path.isfile(self.spec), "Unknown Collection: " + self.spec + ", Collections dir = " + self.collDir
        with open( self.spec, "r" ) as file:
            for line in file.readlines():
                if not line: break
                if( line[0] == '#' ):
                    toks = line[1:].split(",")
                    self.parms[toks[0].strip()] = ",".join(toks[1:]).strip()
                else:
                    toks = line.split(",")
                    self.aggs[toks[0].strip()] = ",".join(toks[1:]).strip()

    def getAggId( self, varName: str ) -> str:
        return self.aggs.get( varName )

    def getAggregation( self, aggId: str ) -> "Aggregation":
        agg_file = os.path.join(Collection.collDir, aggId + ".ag1")
        return Aggregation( self.name, agg_file )

    def getVariableSpec( self, varName: str ):
        agg =  self.getAggregation( self.getAggId( varName ) )
        return agg.toXml(varName)

    def getVariable( self, varName ) -> Variable:
        agg =  self.getAggregation( self.getAggId( varName ) )
        return agg.getVariable(varName)

    def fileList(self, aggId: str ) -> List[File]:
        agg = self.getAggregation( aggId )
        return list(agg.fileList())

    def sortVarsByAgg(self, vids: List[VID] ) -> Dict[str,List[str]]:
        bins = {}
        for vid in vids:
            agg_id = self.aggs.get(vid.name)
            assert agg_id is not None, "Can't find aggregation for variable " + vid.name
            bin = bins.setdefault( agg_id, [] )
            bin.append( vid.name )
        return bins

    def pathList(self, aggId: str ) -> List[str]:
        agg = self.getAggregation( aggId )
        return agg.pathList()

    def periodPathList(self, aggId: str, start:datetime, end:datetime ) -> List[str]:
        agg = self.getAggregation( aggId )
        return agg.periodPathList( start, end )
