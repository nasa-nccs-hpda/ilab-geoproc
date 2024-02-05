import os
import sys
import time
import logging
import argparse
import numpy as np
from glob import glob
from osgeo import gdal
from itertools import repeat
from multiprocessing import Pool, cpu_count


__author__ = 'jordan.a.caraballo-vega@nasa.gov'
__status__ = 'Production'


def getParser():
    """
    Get parser object for main initialization.
    """
    desc = 'Use this to specify the regions and years to download ' + \
        'Landsat ARD. Regions follow the GLAD ARD tile system.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        '-i', '--input-path', type=str,
        default='/css/landsat/Collection2/GLAD_ARD/Native_Grid',
        dest='input_path', help='Parent directory for the Landsat ARD')

    parser.add_argument(
        '-o', '--output-path', type=str,
        default='/css/landsat/Collection2/GLAD_ARD/ABoVE_Grid_Update/' +
        'ABoVE_Grid_Landsat_VRTs',
        dest='output_path', help='Output directory for the VRT')

    parser.add_argument(
        '-s', '--interval-start', type=int, default=392, dest='interval_start',
        help='The first time interval to download')

    parser.add_argument(
        '-e', '--interval-end', type=int, default=1012, dest='interval_end',
        help='The last time interval to download')

    parser.add_argument(
        '-if', '--interval-filename', type=int,
        default=None, dest='interval_filename',
        help='Filename of intervals, used only when distributed across nodes')

    parser.add_argument(
        '-np', '--num-procs',
        type=int, default=cpu_count() * 2, dest='num_procs',
        help='Number of parallel processes')

    return parser.parse_args()


def create_vrt(files_list, vrt_filename):
    """
    Generate VRT filenames
    """
    vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
    gdal.BuildVRT(vrt_filename, files_list, options=vrt_options)
    logging.info(f'{vrt_filename} created.')
    return


def setup_vrt_dependencies(interval, input_path, output_path):

    # output filename
    vrt_filename = os.path.join(output_path, f'{interval}.vrt')

    # if filename does not exist, start processing
    if not os.path.isfile(vrt_filename):

        # store curl command to execute
        logging.info(f'Gathering tile VRT regex list for {interval}')
        vrt_regex_list = glob(
            os.path.join(input_path, '*', '*', f'{interval}.tif'))

        # generate vrt
        logging.info(f'Generating VRT for {interval}.')
        create_vrt(vrt_regex_list, vrt_filename)

    return


def main():

    # Process command-line args.
    args = getParser()

    # Arguments
    input_path = args.input_path
    out_path = args.output_path
    int_start = args.interval_start
    int_end = args.interval_end
    interval_filename = args.interval_filename

    # Set logging
    logging.basicConfig(format='%(asctime)s %(message)s', level='INFO')
    timer = time.time()

    # only calculate intervals if filename is not given
    if interval_filename is not None:
        # Read intervals from filename
        intervals = open(interval_filename, 'r').read().splitlines()
        logging.info(
            f'Downloading intervals: {intervals[0]} to {intervals[1]}' +
            ' ({len(intervals)} total)')
    else:
        # Get files required for download
        num = int(int_end - int_start)
        intervals = np.linspace(
            int_start, int_end, num=num, endpoint=True, dtype=int)

        logging.info(
            f'Downloading intervals: {int_start} to {int_end} ({num} total)')

    # create possible missing directory
    os.makedirs(out_path, exist_ok=True)

    # Set pool, start parallel multiprocessing
    p = Pool(processes=args.num_procs)
    p.starmap(
        setup_vrt_dependencies,
        zip(
            intervals,
            repeat(input_path),
            repeat(out_path)
        )
    )
    p.close()
    p.join()

    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, {args.output_path}.')


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
