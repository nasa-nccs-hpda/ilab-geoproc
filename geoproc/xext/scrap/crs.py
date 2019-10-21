import math, rasterio, subprocess, os
import xarray as xa
from typing import Dict, List, Tuple
import numpy as np
from geoproc.util.configuration import ConfigurableObject

class CRS(ConfigurableObject):

    @classmethod
    def get_utm_crs( cls, longitude: float, south: bool = False ) -> str:
        if longitude > 180: longitude = longitude - 360
        zone = cls.get_utm_zone( longitude )
        result =  f"+proj=utm +zone={zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        if south: result = result + " +south"
        return result

    @classmethod
    def get_utm_zone( cls, longitude: float ):
        return math.floor((longitude + 180) / 6) + 1

        return out_dir, out_file

    @classmethod
    def reproject(cls, input_file: str, output_file: str, dst_crs: str, **kwargs ):
        try:
            command = ['rio', 'warp', input_file, output_file, '--dst-crs', f"'{dst_crs}'" ]
            resolution = kwargs.get("resolution")
            if resolution is not None: command = command + [ '--res', float(resolution) ]
            print( f"Executing command: >> {' '.join(command)}" )
            completedProcess: subprocess.CompletedProcess = subprocess.run( command, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            print( f"Reprojection process completed with returncode {completedProcess.returncode}, output = {output_file}" )
        except Exception as err:
            print(f"Error running reprojection operation: {err}")

# from multiprocessing import Pool
# def download_tiles(self, nProcesses: int = 8):
#     locations = dataMgr.get_global_locations()
#     with Pool(nProcesses) as p:
#         p.map(dataMgr.get_tile, locations, nProcesses)