import os
import sys
import time
import shutil
import logging
import argparse

import subprocess
from glob import glob
from osgeo import gdal
from typing import Dict, List, Tuple, Union, Optional
from multiprocessing import Pool, Lock, cpu_count

def create_vrt(vrt_filename, files_list):
    vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
    my_vrt = gdal.BuildVRT(vrt_filename, files_list, options=vrt_options)
    print(f'{vrt_filename} created.')
    return

def main():
    
    data_ids = [*range(47, 1013, 1)]
    vrt_filenames = []

    #for id in data_ids:
    #    vrt_filenames.append(f'{id}.vrt')

    for data_id in data_ids:

        print(f'starting with {data_id}')
        files_list = glob(f'/adapt/nobackup/projects/ilab/data/LandSatABoVE/*/*/{data_id}.tif')
        vrt_filename = f'/adapt/nobackup/projects/ilab/data/LandSatABoVE/test/{data_id}.vrt'
        create_vrt(vrt_filename, files_list)


        # Build VRT of false color image for manual water detection
        # this is for bands 1,2,1 in RGB respectively
        #gt= subG.GetGeoTransform()
        #proj= subG.GetProjection()
        #driver =gdal.GetDriverByName('GTiff')
        #driver.Register()
        #basename = os.path.splitext(filename)[0]
        #p = Pool(processes=num_procs)
        #p.map(self.process_file, files_list)
        #p.close()
        #p.join()

        #with multiprocessing.Pool(processes=3) as pool:
        #    results = pool.starmap(merge_names, product(names, repeat=2))
        #print(results)


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
