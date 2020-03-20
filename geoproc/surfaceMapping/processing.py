from typing import List, Union, Tuple, Dict, Optional
from geoproc.xext.xrio import XRio
import xarray as xr
import numpy as np
import os, time, collections

class LakeMaskProcessor:

    def __init__( self, opspecs: Dict, **kwargs ):
        self._opspecs = { key.lower(): value for key,value in opspecs.items() }
        self._defaults = self._opspecs.get( "defaults", None )

    def process_lakes(self) -> Dict[ int, xr.DataArray ]:
        year_range = self._defaults['year_range']
        lakeMaskSpecs = self._defaults.get( "lake_masks", None )
        data_dir = lakeMaskSpecs["basedir"]
        lake_index_range = lakeMaskSpecs["lake_index_range"]
        directorys_spec = lakeMaskSpecs["subdir"]
        files_spec = lakeMaskSpecs["file"]
        lake_masks = {}
        lake_indices = []
        for year in range( int(year_range[0]), int(year_range[1]) + 1 ):
            year_dir = os.path.join( data_dir, directorys_spec.format( year=year ) )
            _lake_indices = lake_indices if year > year_range[0] else range(lake_index_range[0], lake_index_range[1] + 1)
            for lake_index in _lake_indices:
                file_path = os.path.join(year_dir, files_spec.format( year=year, lake_index=lake_index ) )
                if year == year_range[0]:
                    if os.path.isfile( file_path ):
                        lake_masks[lake_index] = collections.OrderedDict( )
                        lake_masks[lake_index][year] = file_path
                        lake_indices.append( lake_index )
                else:
                    lake_masks[lake_index][year]= file_path

        results = {}
        for lake_index, sorted_file_paths in lake_masks.items():
            time_values = np.array( [ self.get_date_from_year(year) for year in sorted_file_paths.keys()], dtype='datetime64[ns]' )
            yearly_lake_masks: xr.DataArray = XRio.load(list(sorted_file_paths.values()),  band=0, index=time_values)
            lake_results = self.process_lake_masks( lake_index, yearly_lake_masks )
            if lake_results is not None: results[lake_index] = lake_results
            else: print( f"Skipping lake {lake_index} due to errors ")

        return results

    def process_lake_masks(self, lake_index: int, mask_files: xr.DataArray ) -> Optional[xr.DataArray]:
        from geoproc.surfaceMapping.lakeExtentMapping import WaterMapGenerator
        waterMapGenerator = WaterMapGenerator( { 'lake_index': lake_index, **self._defaults } )
        return waterMapGenerator.process_yearly_lake_masks( lake_index, mask_files )

    def fuzzy_where( cond: xr.DataArray, x, y, join="left" ) -> xr.DataArray:
        from xarray.core import duck_array_ops
        return xr.apply_ufunc( duck_array_ops.where, cond, x, y, join=join, dataset_join=join, dask="allowed" )

    def get_date_from_year( self, year: int ):
        from datetime import datetime
        result = datetime( year, 1, 1 )
        return np.datetime64(result)

    def set_spatial_precision( self, array: xr.DataArray, precision: int ) -> xr.DataArray:
        if precision is None: return array
        sdims = [ array.dims[-2], array.dims[-1] ]
        rounded_coords = { dim: array.coords[dim].round( precision ) for dim in sdims }
        return array.assign_coords( rounded_coords )

if __name__ == '__main__':
    from geoproc.plot.animation import SliceAnimation
    import yaml
    CURDIR = os.path.dirname(os.path.abspath(__file__))
    opspec_file = os.path.join( CURDIR, "specs", "lakes-test.yml")
    with open(opspec_file) as f:
        opspecs = yaml.load( f, Loader=yaml.FullLoader )
        lakeMaskProcessor = LakeMaskProcessor( opspecs )
        results = lakeMaskProcessor.process_lakes()
        animation = SliceAnimation( list(results.values()) )
        animation.show()

