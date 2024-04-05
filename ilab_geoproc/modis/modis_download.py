# Example multiprocessing download
# You will need to setup your MODAPS_KEY
# variable in your system
# export MODAPS_KEY="key" should do the trick

import os
import sys
from tqdm import tqdm
from multiprocessing import Pool, cpu_count


def download_file(download_url: str):
    os.system(download_url)
    return


def main():

    # check if environment file is there
    if os.environ.get('MODAPS_KEY') is None:
        sys.exit('You will need to set MODAPS_KEY environment variable.')

    # setup intervals, feel free to setup full interval if needed
    intervals_2019 = [f'2019/{str(day).zfill(3)}' for day in range(65, 366)]
    intervals_2020 = [f'2020/{str(day).zfill(3)}' for day in range(1, 65)]
    intervals = intervals_2019 + intervals_2020

    # List of files to download with their respective url
    download_urls = []

    # Iterate over each tile
    for time_interval in tqdm(intervals):

        url = \
            'wget -e robots=off -m -np -A "*h09v05*.hdf" -nd -r ' + \
            f'"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MODTBGA/{time_interval}" ' + \
            f'--header "Authorization: Bearer {os.environ["MODAPS_KEY"]}" -P .'
        download_urls.append(url)

    # print(download_urls)

    # Set pool, start parallel multiprocessing
    p = Pool(processes=cpu_count() * 2)
    p.map(download_file, download_urls)
    p.close()
    p.join()


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
