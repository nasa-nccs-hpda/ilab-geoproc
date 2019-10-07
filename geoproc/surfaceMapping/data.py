import time, os, urllib
from typing import Dict, List
from urllib.error import HTTPError


class MWPDataManager:

    def __init__(self, data_dir: str, data_source_url: str ):
        self.data_dir = data_dir
        self.data_source_url = data_source_url


    def download_tile( self, location: str = "120W050N", year: int = 2019, start_day: int = 1, end_day: int = 365, product: str = "3D3OT", download = False ) -> List[str]:
        t0 = time.time()
        print("\n Executing download_MWP_files " )
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

    def get_global_locations(self) -> List[str]:
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
        print( "\n".join(global_locs) )


    def download_all_tiles(self, year: int = 2019, start_day: int = 1, end_day: int = 365, product: str = "3D3OT" ):
        pass

if __name__ == '__main__':
    dataMgr = MWPDataManager( "", "https://floodmap.modaps.eosdis.nasa.gov/Products" )
    dataMgr.get_global_locations()
