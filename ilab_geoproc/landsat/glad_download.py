import os
import sys
import csv
import time
import argparse
import logging
import numpy as np
import pandas as pd
from multiprocessing import Pool, Lock, cpu_count


def getParser():
    """
    Get parser object for main initialization.
    """
    desc = 'Use this to specify the regions and years to download Landsat ARD. ' + \
        'Regions follow the GLAD ARD tile system.'
    parser = argparse.ArgumentParser(description=desc)
    
    parser.add_argument(
        '-i', '--input', type=str, required=True,
        help='Full file path to a csv containing the tiles to download')
    
    parser.add_argument(
        '-u', '--uname', type=str, required=True,
        help='Username for your GLAD account')
    
    parser.add_argument(
        '-p', '--psswrd', type=str, required=True,
        help='Password for your GLAD account')
    
    parser.add_argument(
        '-o', '--outPath', type=str, default='.',
        help='Parent directory for the Landsat ARD')
    
    parser.add_argument(
        '-s', '--intStart', type=int, default=47,
        help='The first interval to download')
    
    parser.add_argument(
        '-e', '--intEnd', type=int, default=1012,
        help='The last interval to download')

    parser.add_argument(
        '-np', '--numProcs', type=int, default=cpu_count(),
        help='Number of parallel processes')

    return parser.parse_args()


def download_file(download_url: str):
    os.system(download_url)
    return


def main():

    # Process command-line args.
    args = getParser()

    # Arguments 
    tilePath = args.input
    outPath = args.outPath
    intStart = args.intStart
    intEnd = args.intEnd

    # Set logging
    logging.basicConfig(format='%(asctime)s %(message)s', level='INFO')
    timer = time.time()

    logging.info(f'Using {args.input} as data input.')

    # Read input CSV with labels
    labels = pd.read_csv(tilePath)
    labels = labels['TILE'].values.tolist()
    logging.info(f'{str(len(labels))} tiles to process')

    # Get files required for download
    num = int(intEnd - intStart)
    intervals = np.linspace(intStart, intEnd, num=num, endpoint=True, dtype=int)
    logging.info(f'Downloading intervals: {intStart} to {intEnd} ({num} total)')

    # List of files to download with their respective url
    download_urls = []

    # Iterate over each tile
    for tile in labels:

        # set latitude value
        lat = tile[-3:]
        
        for interval in intervals:
            
            # output filename
            output = os.path.join(outPath, lat, tile,  f'{interval}.tif')

            # if filename does not exist, start processing
            if not os.path.isfile(output):

                # create possible missing directory
                os.makedirs(os.path.dirname(output), exist_ok=True)

                # store curl command to execute
                download_command = f'curl -u {args.uname}:{args.psswrd} -X GET ' + \
                    f'https://glad.umd.edu/dataset/landsat_v1.1/{lat}/{tile}/{interval}.tif -o {output}'
                download_urls.append(download_command)

    logging.info(f'Downloading {len(download_urls)} missing files.')

    # Set pool, start parallel multiprocessing
    p = Pool(processes=args.numProcs)
    p.map(download_file, download_urls)
    p.close()
    p.join()

    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, output at {args.outPath}.')


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
