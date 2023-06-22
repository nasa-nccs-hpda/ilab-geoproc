import os
import sys
import time
import argparse
import logging
import numpy as np
import pandas as pd
from multiprocessing import Pool, cpu_count


def getParser():
    """
    Get parser object for main initialization.
    """
    desc = 'Use this to specify the regions and years to download ' + \
        'Landsat ARD. Regions follow the GLAD ARD tile system.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        '-i', '--input-tiles', type=str,
        default='/explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/Collection2_requests/ABoVE_Tilesextend.csv',
        required=False, dest='input_tiles',
        help='Full file path to a csv containing the tiles to download')

    parser.add_argument(
        '-u', '--username', type=str, default='glad', dest='username',
        help='Username for your GLAD account')

    parser.add_argument(
        '-p', '--password', type=str, default='ardpas', dest='password',
        help='Password for your GLAD account')

    parser.add_argument(
        '-o', '--output-path', type=str,
        default='/css/landsat/Collection2/GLAD_ARD/Native_Grid',
        dest='output_path', help='Parent directory for the Landsat ARD')

    parser.add_argument(
        '-s', '--interval-start', type=int, default=47, dest='interval_start',
        help='The first time interval to download')

    parser.add_argument(
        '-e', '--interval-end', type=int, default=1012, dest='interval_end',
        help='The last time interval to download')

    parser.add_argument(
        '-np', '--num-procs', type=int, default=cpu_count(), dest='num_procs',
        help='Number of parallel processes')

    return parser.parse_args()


def download_file(download_url: str):
    os.system(download_url)
    return


def main():

    # Process command-line args.
    args = getParser()

    # Arguments
    tile_path = args.input_tiles
    out_path = args.output_path
    int_start = args.interval_start
    int_end = args.interval_end

    # Set logging
    logging.basicConfig(format='%(asctime)s %(message)s', level='INFO')
    timer = time.time()

    logging.info(f'Using {args.input_tiles} as data input.')

    assert os.path.isfile(tile_path), f'CSV file not found: {tile_path}'

    # Read input CSV with labels
    labels = pd.read_csv(tile_path)
    labels = labels['TILE'].values.tolist()
    logging.info(f'{str(len(labels))} tiles to process')

    # Get files required for download
    num = int(int_end - int_start)
    intervals = np.linspace(
        int_start, int_end, num=num, endpoint=True, dtype=int)
    logging.info(
        f'Downloading intervals: {int_start} to {int_end} ({num} total)')

    # List of files to download with their respective url
    download_urls = []

    # Iterate over each tile
    for tile in labels:

        # set latitude value
        lat = tile[-3:]

        for interval in intervals:

            # output filename
            output = os.path.join(out_path, lat, tile,  f'{interval}.tif')

            # if filename does not exist, start processing
            if not os.path.isfile(output):

                # create possible missing directory
                os.makedirs(os.path.dirname(output), exist_ok=True)

                # store curl command to execute
                download_command = \
                    f'curl -u {args.username}:{args.password} -X GET ' + \
                    f'https://glad.umd.edu/dataset/landsat_v1.1/' + \
                    f'{lat}/{tile}/{interval}.tif -o {output}'
                download_urls.append(download_command)

    logging.info(f'Downloading {len(download_urls)} missing files.')

    # Set pool, start parallel multiprocessing
    p = Pool(processes=args.num_procs)
    p.map(download_file, download_urls)
    p.close()
    p.join()

    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, output at {args.output_path}.')


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
