import os
import sys
import time
import argparse
import logging
import numpy as np
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from itertools import repeat


import sys

sys.path.append('/home/jacaraba/.local/lib/python3.12/site-packages')

import ee
import os
import json
import fiona
import folium
import geemap
import geedim as gd
import geopandas as gpd
import rioxarray as rxr
from glob import glob
from pathlib import Path
from shapely.geometry import box

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
        '-i', '--input-tiles', type=str,
        default='/explore/nobackup/projects/ilab/software/ilab-geoproc/' +
        'ilab_geoproc/landsat/Collection2_requests/ABoVE_Tiles_all.csv',
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
        '-s', '--interval-start', type=int, default=392, dest='interval_start',
        help='The first time interval to download')

    parser.add_argument(
        '-e', '--interval-end', type=int, default=1012, dest='interval_end',
        help='The last time interval to download')

    parser.add_argument(
        '-np', '--num-procs',
        type=int, default=cpu_count() * 2, dest='num_procs',
        help='Number of parallel processes')

    return parser.parse_args()


def download_file(s1_collection, output_filename, ee_bbox, polarization):
    print(output_filename, ee_bbox)
    if os.path.isfile(output_filename):
        return
    im = gd.mask.MaskedImage(s1_collection, dtype='float32', bands=[polarization])
    im.download(output_filename, region=ee_bbox, crs='EPSG:4326', scale=10)
    return

def main():

    # Process command-line args.
    # args = getParser()

    tiles_filename = '/explore/nobackup/people/jacaraba/projects/PatagoniaChile/tiles_limite_patagonia.gpkg'
    tiles_gdf = gpd.read_file(tiles_filename)

    gee_account='id-sl-senegal-service-account@ee-3sl-senegal.iam.gserviceaccount.com'
    gee_key='/home/jacaraba/gee/ee-3sl-senegal-8fa70fe1c565.json'

    study_area_filename = '/explore/nobackup/people/jacaraba/projects/PatagoniaChile/limite_patagonia_EPSG4326.gpkg'
    output_dir = '/explore/nobackup/people/jacaraba/projects/PatagoniaChile/SAR_Data'
    os.makedirs(output_dir, exist_ok=True)

    polarization = 'VH' # 'VH'
    start_date = '2021-01-01'
    end_date = '2023-12-31'
    start_month = 6
    end_month = 8

    # get credentials
    credentials = ee.ServiceAccountCredentials(gee_account, gee_key)
    ee.Initialize(credentials)  # gd initialize does not take service account
    print("Initialized")

    s1_collection_list = []
    s1_output_filenames = []
    s1_geometry_list = []

    # iterate over each tile and get geometry
    for index, row in tiles_gdf.iterrows():

        row = tiles_gdf.iloc[[index]]
        xmin, ymin, xmax, ymax = row.total_bounds

        # Create a GEE rectangle geometry using the bounds
        ee_bbox = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax])


        # Filter the Sentinel-1 IW ImageCollection
        s1_collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                        .filterBounds(ee_bbox)
                        .filterDate(start_date, end_date)
                        .filter(ee.Filter.calendarRange(start_month, end_month,'month'))
                        .filter(ee.Filter.eq('instrumentMode', 'IW'))
                        .select(polarization)
        )

        def compute_gee_power(image: ee.image.Image) -> ee.element.Element:
            return ee.Image(10).pow(image.divide(10)).rename(polarization).copyProperties(image, ['system:time_start'])

        s1_collection = s1_collection.map(compute_gee_power)
        s1_collection = s1_collection.median()
        s1_collection = s1_collection.clip(ee_bbox) #.toBands().clip(ee_bbox)

        output_filename = os.path.join(
            output_dir, f'{row["TILE"].values[0]}_pol_{polarization}_{start_date}_to_{end_date}_months_{start_month}_to_{end_month}_10m.tif')

        s1_collection_list.append(s1_collection)
        s1_output_filenames.append(output_filename)
        s1_geometry_list.append(ee_bbox)

        im = gd.mask.MaskedImage(s1_collection, dtype='float32', bands=[polarization])
        im.download(output_filename, region=ee_bbox, crs='EPSG:4326', scale=10)

    """
    p = Pool(processes=cpu_count()*2)
    p.starmap(
        download_file,
        zip(
            s1_collection_list,
            s1_output_filenames,
            s1_geometry_list,
            repeat(polarization)
        )
    )
    """
    """

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

    logging.info('Gathering tile URLs')

    # Iterate over each tile
    for tile in tqdm(labels):

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
                    'https://glad.umd.edu/dataset/glad_ard2/' + \
                    f'{lat}/{tile}/{interval}.tif -o {output}'
                download_urls.append(download_command)

    logging.info(f'Downloading {len(download_urls)} missing files.')

    # Set pool, start parallel multiprocessing
    p = Pool(processes=args.num_procs)
    p.map(download_file, download_urls)
    p.close()
    p.join()

    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, {args.output_path}.')
    """

# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
