import math, rasterio, subprocess, os
import xarray as xa
from typing import Dict, List, Tuple
import numpy as np
from .configuration import ConfigurableObject

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

    @classmethod
    def to_geotiff(cls, array: xa.DataArray, output_dir: str = None) -> Tuple[str,str]:
        array = array.load()

        if len(array.shape) == 2:
            count = 1
            height = array.shape[0]
            width = array.shape[1]
            band_indicies = 1
        else:
            count = array.shape[0]
            height = array.shape[1]
            width = array.shape[2]
            band_indicies = np.arange(count) + 1

        processed_attrs = {}
        try:
            from rasterio import Affine
            val = array.attrs.get( 'transform' )
            if val is None: val = array.attrs['affine']
            processed_attrs['transform'] = Affine.from_gdal(*val)
        except Exception as ex:
            print( f"Error processing transform: {ex}")

        try:
            from rasterio import crs
            val = array.attrs['crs']
            processed_attrs['crs'] = crs.CRS.from_string(val)
        except Exception as ex:
            print( f"Error processing crs: {ex}")

        out_dir = output_dir if output_dir else f"/tmp/{cls.randomId(6)}"
        if not os.path.isdir( out_dir ): os.mkdir(out_dir)
        out_file = f"{array.name if array.name else cls.randomId(4)}.tif"
        with rasterio.open( f"{out_dir}/{out_file}", 'w', driver='GTiff',  height=height, width=width,  dtype=str(array.dtype), count=count,  **processed_attrs) as dst:
            dst.write(array.values, band_indicies)

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