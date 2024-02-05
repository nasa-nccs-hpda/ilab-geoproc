# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import argparse
import subprocess
import rioxarray as rxr
from glob import glob
from pathlib import Path
from datetime import date
from typing import List, Tuple
from multiprocessing import Pool, Lock, cpu_count

globallock = Lock()

# python glad_reproject_zach.py 
# -f '/explore/nobackup/projects/ilab/data/LandSatABoVE_Regrid_C2/above_landsat_vrt/*.vrt'
# -o '/explore/nobackup/projects/ilab/data/LandSatABoVE_Regrid_C2_Extended' 
# -hs 18 -he 23 -vs 18 -ve 23

class GladReproject:

    def __init__(
                self,
                output_dir: str,
                temporary_output_dir: str = None,
                h_start_tile: int = 0,
                h_end_tile: int = 17,
                v_start_tile: int = 0,
                v_end_tile: int = 17,
                start_interval: int = 392,
                end_interval: int = 979,
                version: str = '001',
                run_date: str = '20240201'
            ) -> None:

        # main output directory, it is normally a CSS directory
        self.output_dir = output_dir
        logging.info(f'Output directory: {self.output_dir}')

        # output vrt_ids from glad
        # self.vrt_ids = [*range(47, 1013, 1)]
        # self.vrt_ids = [*range(392, 977, 1)]

        # calculate glad landsat time metadata
        self.time_metadata = self.get_gladard_time_metadata()
        logging.info(
            f'Landsat intervals as of today: {len(self.time_metadata)}')

        # horizontal tiles from ABoVE to start and end from
        self.h_start_tile = h_start_tile
        self.h_end_tile = h_end_tile

        # vertical tiles from ABoVE to start and end from
        self.v_start_tile = v_start_tile
        self.v_end_tile = v_end_tile

        # above grid list
        self.tiles_list = self.get_above_grid_list(
            h_start_tile=self.h_start_tile,
            h_end_tile=self.h_end_tile,
            v_start_tile=self.v_start_tile,
            v_end_tile=self.v_end_tile,
        )
        logging.info(
            f'Total ABoVE tiles to process {len(self.tiles_list)}')

        # Set the date in which this is being run
        self.run_date = run_date

        # Set the version of this run
        self.version = version

        # sometimes we need to output to other directories, but need to retain
        # which files have been processed on the main output_dir to not
        # repeat processing and waste resources
        self.temporary_output_dir = temporary_output_dir

        # GLAD ARD time intervals
        self.start_interval = start_interval
        self.end_interval = end_interval

    def get_above_grid_list(
                self,
                h_start_tile=0,
                h_end_tile=18,
                v_start_tile=0,
                v_end_tile=18
            ):
        """
        Get above grid list.
        """
        tiles_list = []
        for h in range(h_start_tile, h_end_tile + 1):
            for v in range(v_start_tile, v_end_tile + 1):
                tiles_list.append(f"h{h:03d}v{v:03d}")
        return tiles_list

    def get_gladard_time_metadata(self):
        """
        Get time metadata as a dict from # ID = (YEAR - 1980) x 23 + int
        https://glad.umd.edu/Potapov/ARD/ARD_manual_v1.1.pdf
        """
        scene_id_metadata = dict()
        for year_range in range(1982, date.today().year + 1):
            for interval_range in range(1, 24):
                scene_id = (year_range - 1980) * 23 + interval_range
                scene_id_metadata[f'{scene_id}'] = {
                    'year': year_range, 'interval': f'{interval_range:02d}'}
        return scene_id_metadata

    def get_file_paths(self, input_file: str) -> Tuple[str, str, str]:
        """
        Get file paths of the files extracted import this from raw data.
        """
        infile_dir, infile_name = os.path.split(input_file)
        base1, dir1 = os.path.split(infile_dir)
        base0, dir0 = os.path.split(base1)
        if infile_name.endswith("_img"):
            ofile_name = infile_name[:-4]
        else:
            ofile_name = infile_name
        ifile_outputdir = os.path.join(self.output_dir, dir0, dir1)
        return infile_dir, ifile_outputdir, ofile_name

    def get_filtered_file(self, input_file):
        """
        Get filtered file.
        """
        input_dir, output_dir, output_file = self.get_file_paths(input_file)
        output_file_path = os.path.join(output_dir, output_file)
        if self.needs_processing(output_file_path):
            return input_file

    def get_unprocessed_filepaths(self, files_glob: str) -> List[str]:
        """
        Get a filtered list of unprocessed files.
        """
        files_list = glob(files_glob)
        logging.info(f'Found {len(files_list)} total raw files.')

        p = Pool(processes=cpu_count())
        filtered_file_list = list(
            filter(None, p.map(self.get_filtered_file, files_list)))
        p.close()
        p.join()

        logging.info(f'{len(filtered_file_list)} files need processing.')
        return filtered_file_list

    def process_files(
            self, vrts_dir: str, num_procs: int = cpu_count()) -> None:
        """
        Process multiple files via multiprocessing.
        """
        vrt_files_list = []
        for interval in range(self.start_interval, self.end_interval + 1):
            vrt_files_list = os.path.join(vrts_dir, f'{str(interval)}.vrt')
        p = Pool(processes=num_procs)
        p.map(self.process_file, vrt_files_list)
        p.close()
        p.join()

    def process_file(self, vrt_filename):

        vrt_id = Path(vrt_filename).stem

        # ID = (Year-1980) × 23 + Interval
        translated_date = \
            f'{self.time_metadata[vrt_id]["year"]}' + \
            f'{self.time_metadata[vrt_id]["interval"]}'

        for full_tile in self.tiles_list:

            hh, vv = full_tile[1:4], full_tile[5:]
            full_tile = f'B{full_tile}'

            x_max = str(-3400020 + ((int(hh) + 1) * (180 * 1000)))
            x_min = str(-3400020 + (int(hh) * (180 * 1000)))
            y_max = str(4640000 - (int(vv) * (180 * 1000)))
            y_min = str(4640000 - ((int(vv) + 1) * (180 * 1000)))

            full_output_dir = os.path.join(
                self.output_dir, full_tile
            )
            os.makedirs(full_output_dir, exist_ok=True)

            output_filename = os.path.join(
                full_output_dir,
                f"ABoVE.GladARD.{translated_date}." +
                f"{full_tile}.{self.version}.{self.run_date}.tif"
            )

            args = [
                'gdalwarp', '-co',
                'COMPRESS=LZW', '-co',
                'BIGTIFF=YES', '-q',
                '--config', 'GDAL_CACHEMAX', '512',
                '-wm', '512',
                '-dstnodata', '0',
                '-t_srs', 'ESRI:102001',
                '-tr', '30', '30',
                '-te', x_min, y_min, x_max, y_max,
                vrt_filename,
                output_filename
            ]
            print(' '.join(args))

            t0 = time.time()
            rv = subprocess.call(args)

            if rv == 0:
                logging.info(
                    f'{output_filename} took {(time.time()-t0)/60.0:.2f} min')
            else:
                logging.info(f'Error when processing file {vrt_filename}')
        return

    def needs_processing(self, output_file) -> bool:
        """
        Validate if file needs processing and is correctly formatted.
        """
        try:
            rxr.open_rasterio(output_file)
        except Exception:
            if os.path.isfile(output_file):
                os.remove(output_file)
            return True
        return False


def getParser():
    """
    Get parser object for main initialization.
    """
    # Process command-line args.
    desc = 'Use this application to regrid Landsat ARD data.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-vd',
                        '--vrts-dir',
                        type=str,
                        required=True,
                        dest='vrts_dir',
                        help='Dir where vrts are stored')

    parser.add_argument(
                        '-st',
                        '--start-interval',
                        type=int,
                        required=False,
                        default=392,
                        dest='start_interval',
                        help='GLAD ARD time interval to start from.')

    parser.add_argument(
                        '-et',
                        '--end-interval',
                        type=int,
                        required=False,
                        default=1012,
                        dest='end_interval',
                        help='GLAD ARD time interval to end at.')

    parser.add_argument(
                        '-o',
                        '--output-dir',
                        type=str,
                        required=True,
                        dest='output_dir',
                        help='Output directory to store analysis ready data.')

    parser.add_argument(
                        '-to',
                        '--temporary-output-dir',
                        type=str,
                        required=False,
                        default=None,
                        dest='temporary_output_dir',
                        help='Temporary output directory to store ARD.')

    parser.add_argument(
                        '-n',
                        '--num-procs',
                        type=str,
                        required=False,
                        dest='num_procs',
                        default=cpu_count(),
                        help='Number of cores to use. Defaults to CPU count.')

    parser.add_argument(
                        '-hs',
                        '--horizontal-start-tile',
                        type=int,
                        required=False,
                        default=0,
                        dest='h_start_tile',
                        help='Starting ABoVE tile.')

    parser.add_argument(
                        '-he',
                        '--horizontal-end-tile',
                        type=int,
                        required=False,
                        default=17,
                        dest='h_end_tile',
                        help='Horizontal ending ABoVE tile.')

    parser.add_argument(
                        '-vs',
                        '--vertical-start-tile',
                        type=int,
                        required=False,
                        default=0,
                        dest='v_start_tile',
                        help='Vertical starting ABoVE tile.')

    parser.add_argument(
                        '-ve',
                        '--vertical-end-tile',
                        type=int,
                        required=False,
                        default=17,
                        dest='v_end_tile',
                        help='Vertical ending ABoVE tile.')

    return parser.parse_args()


def main():

    # Process command-line args.
    args = getParser()

    # Set logging
    logging.basicConfig(format='%(asctime)s %(message)s', level='INFO')
    timer = time.time()

    awarp = GladReproject(
        args.output_dir,
        args.temporary_output_dir,
        args.h_start_tile,
        args.h_end_tile,
        args.v_start_tile,
        args.v_end_tile,
        args.start_interval,
        args.end_interval
    )

    # awarp.process_files(args.vrts_dir)  # args.files_glob.replace('"', '')
    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, output: {args.output_dir}.')


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
