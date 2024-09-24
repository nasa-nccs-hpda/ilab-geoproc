# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import argparse
import subprocess
import numpy as np
import rioxarray as rxr
from glob import glob
from pathlib import Path
from datetime import date
from typing import List, Tuple
from multiprocessing import Pool, Lock, cpu_count

globallock = Lock()


class GladReproject:

    def __init__(
                self,
                output_dir: str,
                temporary_output_dir: str = None,
                h_start_tile: int = 0,
                h_end_tile: int = 17,
                v_start_tile: int = 0,
                v_end_tile: int = 17,
                intervals: list = list(range(392, 1013)),
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
        self.intervals = intervals

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

    def process_files(
            self, vrts_dir: str, num_procs: int = cpu_count()) -> None:
        """
        Process multiple files via multiprocessing.
        """
        # get vrt filenames from the interval provided
        vrt_files_list = []
        for interval in self.intervals:
            vrt_files_list.append(
                os.path.join(vrts_dir, f'{str(interval)}.vrt'))

        # get combination of ABoVE tiles and GLAD intervals
        processing_list = []
        for tile_id in self.tiles_list:
            for vrt_id in vrt_files_list:
                processing_list.append(
                    {
                        'tile_id': tile_id,
                        'vrt_id': vrt_id
                    }
                )

        # start parallel process
        p = Pool(processes=num_procs)
        p.map(self.process_file, processing_list)
        p.close()
        p.join()

    def process_file(self, processing_dict):

        tile_id = processing_dict['tile_id']
        vrt_filename = processing_dict['vrt_id']
        logging.info(f'Processing {tile_id} for {vrt_filename}')

        vrt_id = Path(vrt_filename).stem

        # ID = (Year-1980) × 23 + Interval
        translated_date = \
            f'{self.time_metadata[vrt_id]["year"]}' + \
            f'{self.time_metadata[vrt_id]["interval"]}'
        logging.info(f'Processing {vrt_id} with date {translated_date}')

        # set tile metadata for processing
        hh, vv = tile_id[1:4], tile_id[5:]
        tile_id = f'B{tile_id}'

        # set default output directory
        full_output_dir = os.path.join(
            self.output_dir, tile_id
        )

        # set default output filename
        output_filename = os.path.join(
            full_output_dir,
            f"ABoVE.GladARD.{translated_date}." +
            f"{tile_id}.{self.version}.{self.run_date}.tif"
        )

        # check if the file exists
        if os.path.exists(output_filename):
            return

        # set temporary output if defined
        if self.temporary_output_dir is not None:

            # set default output directory
            full_output_dir = os.path.join(
                self.temporary_output_dir, tile_id
            )

            # set default output filename
            output_filename = os.path.join(
                full_output_dir,
                f"ABoVE.GladARD.{translated_date}." +
                f"{tile_id}.{self.version}.{self.run_date}.tif"
            )

            if os.path.exists(output_filename):
                return

        # if the directory does not exist, create dir
        os.makedirs(full_output_dir, exist_ok=True)

        # set math for tile extent
        x_max = str(-3400020 + ((int(hh) + 1) * (180 * 1000)))
        x_min = str(-3400020 + (int(hh) * (180 * 1000)))
        y_max = str(4640000 - (int(vv) * (180 * 1000)))
        y_min = str(4640000 - ((int(vv) + 1) * (180 * 1000)))

        # set gdal arguments
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
        logging.info(' '.join(args))

        # get time, call subprocess
        t0 = time.time()
        rv = subprocess.call(args)

        # check the success of the subprocess
        if rv == 0:
            logging.info(
                f'{output_filename} took {(time.time()-t0)/60.0:.2f} min')
        else:
            logging.info(f'Error when processing file {vrt_filename}')

        return


def getParser():
    """
    Get parser object for main initialization.
    """
    # Process command-line args.
    desc = 'Use this application to regrid Landsat ARD data.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        '-vd', '--vrts-dir', type=str, required=True,
        dest='vrts_dir', help='Dir where vrts are stored')

    parser.add_argument(
        '-if', '--interval-filename', type=str, default=None,
        dest='interval_filename',
        help='Filename of intervals, used only when distributed across nodes')

    parser.add_argument(
        '-st', '--start-interval', type=int, required=False,
        default=392, dest='interval_start',
        help='GLAD ARD time interval to start from.')

    parser.add_argument(
        '-et', '--end-interval', type=int, required=False, default=1012,
        dest='interval_end', help='GLAD ARD time interval to end at.')

    parser.add_argument(
        '-o', '--output-dir', type=str, required=True, dest='output_dir',
        help='Output directory to store analysis ready data.')

    parser.add_argument(
        '-to', '--temporary-output-dir', type=str, required=False,
        default=None, dest='temporary_output_dir',
        help='Temporary output directory to store ARD.')

    parser.add_argument(
        '-n', '--num-procs', type=str, required=False,
        dest='num_procs', default=cpu_count(),
        help='Number of cores to use. Defaults to CPU count.')

    parser.add_argument(
        '-hs', '--horizontal-start-tile', type=int, required=False,
        default=0, dest='h_start_tile', help='Starting ABoVE tile.')

    parser.add_argument(
        '-he', '--horizontal-end-tile', type=int, required=False,
        default=17, dest='h_end_tile', help='Horizontal ending ABoVE tile.')

    parser.add_argument(
        '-vs', '--vertical-start-tile', type=int, required=False, default=0,
        dest='v_start_tile', help='Vertical starting ABoVE tile.')

    parser.add_argument(
        '-ve', '--vertical-end-tile', type=int, required=False,
        default=17, dest='v_end_tile', help='Vertical ending ABoVE tile.')

    return parser.parse_args()


def main():

    # Process command-line args.
    args = getParser()

    # Arguments
    int_start = args.interval_start
    int_end = args.interval_end
    interval_filename = args.interval_filename

    # Set logging
    logging.basicConfig(format='%(asctime)s %(message)s', level='INFO')
    timer = time.time()

    # Get list of intervals
    # only calculate intervals if filename is not given
    if interval_filename is not None:
        # Read intervals from filename
        intervals = open(interval_filename, 'r').read().splitlines()
        logging.info(
            f'Downloading intervals: {intervals[0]} to {intervals[-1]}' +
            f' ({len(intervals)} total)')
    else:
        # Get files required for download
        num = int(int_end - int_start)
        intervals = np.linspace(
            int_start, int_end, num=num, endpoint=True, dtype=int)

        logging.info(
            f'Downloading intervals: {int_start} to {int_end} ({num} total)')

    # Initialize GladReproject Object
    awarp = GladReproject(
        args.output_dir,
        args.temporary_output_dir,
        args.h_start_tile,
        args.h_end_tile,
        args.v_start_tile,
        args.v_end_tile,
        intervals
    )

    awarp.process_files(args.vrts_dir)
    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, output: {args.output_dir}.')


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
