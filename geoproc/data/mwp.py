import time, os, wget, sys
from typing import Dict, List
from multiprocessing import Pool
import xarray as xr
from geoproc.util.configuration import ConfigurableObject, Region


class MWPDataManager(ConfigurableObject):

    def __init__(self, data_dir: str, data_source_url: str, **kwargs ):
        ConfigurableObject.__init__( self, **kwargs )
        self.data_dir = data_dir
        self.data_source_url = data_source_url

    def get_location_dir( self, location: str ) -> str:
        loc_dir = os.path.join( self.data_dir, location )
        if not os.path.exists(loc_dir): os.makedirs(loc_dir)
        return loc_dir

    def delete_if_empty( self, location: str  ):
        ldir = self.get_location_dir( location )
        try: os.rmdir( ldir )
        except OSError: pass

    def download_tile( self, location: str = "120W050N", **kwargs  ) -> List[str]:
        t0 = time.time()
        download =  self.getParameter( "download",  **kwargs )
        start_day = self.getParameter( "start_day", **kwargs )
        end_day =   self.getParameter( "end_day",   **kwargs )
        year =      self.getParameter( "year",      **kwargs )
        product =   self.getParameter( "product",   **kwargs )
        location_dir = self.get_location_dir( location )
        files = []
        for iFile in range(start_day,end_day+1):
            target_file = f"MWP_{year}{iFile}_{location}_{product}.tif"
            target_file_path = os.path.join( location_dir, target_file )
            if not os.path.exists( target_file_path ):
                if download:
                    target_url = self.data_source_url + f"/{location}/{year}/{target_file}"
                    try:
                        wget.download( target_url, target_file_path )
                        print(f"Downloading url {target_url} to file {target_file_path}")
                        files.append( target_file_path )
                    except Exception:
                        print( f"     ---> Can't access {target_url}")
            else:
                files.append( target_file_path )
                print(f"     ---> Skipping (already downloaded): {target_file_path}")
        return files

    def get_array_data(self, files: List[str] ) ->  List[xr.DataArray]:
        bbox: Region = self.getParameter("bbox")
        if bbox is None:
            data_arrays: List[xr.DataArray] = [xr.open_rasterio(file)[0] for file in files]
        else:
            data_arrays: List[xr.DataArray] = [xr.open_rasterio(file)[0, bbox.origin[0]:bbox.bounds[0], bbox.origin[1]:bbox.bounds[1]] for file in files]
        return data_arrays

    def download_tile_data(self, location: str = "120W050N", **kwargs  ) -> List[xr.DataArray]:
        files = self.download_tile( location, **kwargs )
        return self.get_array_data( files )

    def get_global_locations( self ) -> List:
        global_locs = []
        for ix in range(10,181,10):
            for xhemi in [ "E", "W" ]:
                for iy in range(10,71,10):
                    for yhemi in ["N", "S"]:
                        global_locs.append( f"{ix:03d}{xhemi}{iy:03d}{yhemi}")
        for ix in range(10,181,10):
            for xhemi in [ "E", "W" ]:
                global_locs.append( f"{ix:03d}{xhemi}000S")
        for iy in range(10, 71, 10):
            for yhemi in ["N", "S"]:
                global_locs.append(f"000E{iy:03d}{yhemi}")
        return global_locs

    def remove_empty_directories(self, nProcesses: int = 8):
        locations = dataMgr.get_global_locations()
        with Pool(nProcesses) as p:
            p.map(dataMgr.delete_if_empty, locations, nProcesses)

    def _segment(self, strList: List[str], nSegments ):
        seg_length = int( round( len( strList )/nSegments ) )
        return [strList[x:x + seg_length] for x in range(0, len(strList), seg_length)]

    def download_tiles(self, nProcesses: int = 8 ):
        locations = dataMgr.get_global_locations()
        with Pool(nProcesses) as p:
            p.map(dataMgr.download_tile, locations, nProcesses)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print( "Usage: >> geoproc.data.mwp <dataDirectory>\n       Downloads all MWP tiles to the data directory")
    else:
        dataMgr = MWPDataManager( sys.argv[1], "https://floodmap.modaps.eosdis.nasa.gov/Products" )
        dataMgr.setDefaults( product = "1D1OS", download = True, year = 2019, start_day = 1, end_day = 365 )
        dataMgr.download_tiles( 10 )
        dataMgr.remove_empty_directories(10)
