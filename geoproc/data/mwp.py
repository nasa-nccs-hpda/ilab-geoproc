import time, os, urllib, sys
from typing import Dict, List
from urllib.error import HTTPError
from multiprocessing import Pool
from geoproc.util.configuration import ConfigurableObject


class MWPDataManager(ConfigurableObject):

    def __init__(self, data_dir: str, data_source_url: str, **kwargs ):
        ConfigurableObject.__init__( **kwargs )
        self.data_dir = data_dir
        self.data_source_url = data_source_url


    def download_tile( self, location: str = "120W050N", **kwargs  ) -> List[str]:
        t0 = time.time()
        print("\n Executing download_MWP_files " )
        download =  self.getParameter( "download",  **kwargs )
        start_day = self.getParameter( "start_day", **kwargs )
        end_day =   self.getParameter( "end_day",   **kwargs )
        year =      self.getParameter( "year",      **kwargs )
        product =   self.getParameter( "product",   **kwargs )
        files = []
        for iFile in range(start_day,end_day+1):
            target_file = f"MWP_{year}{iFile}_{location}_{product}.tif"
            target_file_path = os.path.join( self.data_dir, target_file )
            if not os.path.exists( target_file_path ):
                if download:
                    target_url = self.data_source_url + f"/{location}/{year}/{target_file}"
                    try:
                        urllib.request.urlretrieve( target_url, target_file_path )
                        print(f"Downloading url {target_url} to file {target_file_path}")
                        files.append( target_file_path )
                    except HTTPError:
                        print( f"     ---> Can't access {target_url}")
            else:
                files.append( target_file_path )
        print( f" Completed download_MWP_files  in {time.time()-t0:.3f} seconds" )
        return files

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

    def _segment(self, strList: List[str], nSegments ):
        seg_length = int( round( len( strList )/nSegments ) )
        return [strList[x:x + seg_length] for x in range(0, len(strList), seg_length)]

    def download_tile_list(self, locations: List[str] ):
        for location in locations:
            self.download_tile( location )

    def download_tiles(self, nProcesses: int = 8 ):
        locations = dataMgr.get_global_locations()
        with Pool(nProcesses) as p:
            p.map(dataMgr.download_tile_list, locations, nProcesses)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print( "Usage: >> geoproc.data.mwp <dataDirectory>\n       Downloads all MWP tiles to the data directory")
    else:
        dataMgr = MWPDataManager( sys.argv[1], "https://floodmap.modaps.eosdis.nasa.gov/Products" )
        dataMgr.setDefaults( product = "3D3OT", download = True, year = 2019, start_day = 1, end_day = 365 )
        dataMgr.download_tiles( 10 )

