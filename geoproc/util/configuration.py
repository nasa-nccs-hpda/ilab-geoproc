from shapely.geometry import Point
import xarray as xr
import string, random
import pandas as pd
from os.path import dirname, abspath, join
import logging, os
from typing import Sequence, List, Dict, Mapping, Optional
from geoproc.util.logging import ILABLogger

def argfilter( args: Dict, **kwargs ) -> Dict:
    return { key: args.get(key,value) for key,value in kwargs.items() }


class ConfigurableObject:

    def __init__(self, **kwargs):
        self.parms = { **kwargs }

    def getParameter(self, name: str, default=None, **kwargs ):
        return kwargs.get( name, self.parms.get(name,default) )

    def setDefaults( self, **kwargs ):
        self.parms.update( kwargs )

    @classmethod
    def randomId( cls, length: int ) -> str:
        sample = string.ascii_lowercase+string.digits+string.ascii_uppercase
        return ''.join(random.choice(sample) for i in range(length))

    @classmethod
    def transferMetadata( cls, ref_array: xr.DataArray, new_array: xr.DataArray ):
        for key, value in ref_array.attrs.items():
            if key not in new_array.attrs: new_array.attrs[key] = value

    @classmethod
    def parseLocation( cls, location: str ) -> Point:
        lonVal, latStr, latVal = None, None, None
        try:
            if "E" in location:
                coords = location.split("E")
                lonVal = int(coords[0])
                latStr = coords[1]
            elif "W" in location:
                coords = location.split("W")
                lonVal = -int(coords[0])
                latStr = coords[1]
            if "N" in latStr:
                latVal = int(latStr[:-1])
            elif "S" in latStr:
                latVal = -int(latStr[:-1])
            assert lonVal and latVal, "Missing NSEW"
        except Exception as err:
            raise Exception( f"Format error parsing location {location}: {err}")

        return Point( lonVal, latVal )

    def frames_merge( self, data_arrays: List[xr.DataArray] ) -> xr.DataArray:
        frame_names = [ da.name for da in data_arrays ]
        merge_coord = pd.Index( frame_names, name="frames" )
        return xr.concat( objs=data_arrays, dim=merge_coord )

    def time_merge( self, data_arrays: List[xr.DataArray] ) -> xr.DataArray:
        frame_indices = range( len(data_arrays) )
        frame_names = [da.name for da in data_arrays]
        merge_coord = pd.Index( frame_indices, name="time" )
        result =  xr.concat( objs=data_arrays, dim=merge_coord )
        return result # .assign_coords( {'frames': frame_names } )

class Region:

    def __init__(self, origin: List[int], size: int ):
        self.origin: List[int] = origin
        self.size: int = size
        self.bounds: List[int] = [ origin[0] + size, origin[1] + size ]

class ILABParameterManager:

    def __init__(self):
        self._parms = {}
        self.logger =  ILABLogger.getLogger()
        self.HOME = os.environ.get('ILAB_HOME' )
        self.TRANSIENTS =  os.environ.get('ILSCRATCH', os.path.join( self.HOME, "scratch" ) )
        self.COLLECTIONS = os.environ.get('ILCOL', os.path.join( self.HOME, "data", "collections" ) )
        for cpath in [self.TRANSIENTS, self.COLLECTIONS]:
            if not os.path.exists(cpath): os.makedirs(cpath)

    def update(self, parms: Dict[str,str] = None, **kwargs ):
        self._parms.update( parms if parms else {}, **kwargs )
        self.logger.info( f"@PM-> Update parms: {self._parms}")

    @property
    def parms(self)-> Dict[str,str]: return self._parms

    def __getitem__( self, key: str ) -> str: return self._parms.get( key )
    def get( self, key: str, default=None ) -> str: return self._parms.get( key, default )
    def getBool( self, key: str, default: bool ) -> bool:
        rv = self._parms.get( key, None )
        if rv is None: return default
        return rv.lower().startswith("t")

ILABEnv = ILABParameterManager()





