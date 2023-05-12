# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import logging
import argparse

import subprocess
from glob import glob
from typing import Dict, List, Tuple, Union, Optional
from multiprocessing import Pool, Lock, cpu_count

import rioxarray as rxr

globallock = Lock()


class AvirisWarp:

    def __init__(self, output_dir: str, temporary_output_dir: str = None) -> None:

        # main output directory, it is normally a CSS directory
        self.output_dir = output_dir

        # sometimes we need to output to other directories, but need to retain
        # which files have been processed on the main output_dir to not
        # repeat processing and waste resources
        self.temporary_output_dir = temporary_output_dir

    def get_file_paths(self, input_file: str) -> Tuple[str,str,str]:
        """
        Get file paths of the files extracted from raw data.
        """
        infile_dir, infile_name = os.path.split(input_file)
        base1, dir1 = os.path.split(infile_dir)
        base0, dir0 = os.path.split(base1)
        ofile_name = infile_name[:-4] if infile_name.endswith("_img") else infile_name
        ifile_outputdir = os.path.join(self.output_dir, dir0, dir1)
        return  infile_dir, ifile_outputdir, ofile_name + ".tif"

    def get_unprocessed_filepaths(self, files_glob: str) -> List[str]:
        """
        Get a filtered list of unprocessed files.
        """
        files_list = glob(files_glob)
        filtered_file_list = []
        logging.info(f'Found {len(files_list)} total raw files.')

        for input_file in files_list:
            input_dir, output_dir, output_file = self.get_file_paths(input_file)
            output_file_path = os.path.join(output_dir, output_file)
            if self.needs_processing(output_file_path):
                filtered_file_list.append( input_file )
        
        logging.info(f'Found {len(filtered_file_list)} files that need processing.')
        return filtered_file_list

    def process_files(self, files_glob: str, num_procs: int = cpu_count()) -> None:
        """
        Process multiple files via multiprocessing.
        """
        files_list = self.get_unprocessed_filepaths(files_glob)
        logging.info(f'Using {num_procs} processors for {len(files_list)} files from {files_glob}')
        
        p = Pool(processes=num_procs)
        p.map(self.process_file, files_list)
        p.close()
        p.join()
        return

    def needs_processing(self, output_file) -> bool:
        """
        Validate if file needs processing and is correctly formatted.
        """
        try:
            test_data = rxr.open_rasterio(output_file)
        except:
            if os.path.isfile(output_file): os.remove(output_file)
            return True
        return False

    def process_file(self, input_file: str) -> None:
        """
        Process single filename.
        """
        # gather the file paths
        input_dir, output_dir, output_file = self.get_file_paths(input_file)

        # select the output directory based on the available output_dirs
        if self.temporary_output_dir is not None:
            output_dir = os.path.join(
                self.temporary_output_dir,
                os.path.basename(os.path.dirname(output_dir)),
                os.path.basename(output_dir)
            )

        os.makedirs(output_dir, mode=0o777, exist_ok=True)
        output_file_path = os.path.join(output_dir, output_file)

        # lock file for multi-node, multi-processing
        lock_filename = f'{output_file_path}.lock'

        # Skip this process if lock file exist
        # TODO: VERIFY THIS SECTION, this IF statement
        if os.path.isfile(lock_filename) and \
            not self.needs_processing(output_file_path):
            logging.info(f'Skipping {input_file}: File exists at {output_file_path}')
            return

        # Open lock filename
        open(lock_filename, 'w').close()
        logging.info(f'Processing file {input_file}')
        
        self.copy_files(f"{input_dir}/*README*", output_dir)
        t0 = time.time()

        # best performing gdalwarp options, start gdal warp process
        args = [ 
            'gdalwarp', '-co', 'COMPRESS=LZW', '-co', 'BIGTIFF=YES', '-q',
            '--config', 'GDAL_CACHEMAX', '512', '-wm', '512',
            input_file, output_file_path
        ]
        rv = subprocess.call(args)

        if rv == 0:
            logging.info(f'File {output_file} generated in {(time.time()-t0)/60.0:.2f} minutes.')
        else:
            logging.info(f'Error when processing file {input_file}')
        
        # TODO: Remove lock filename

        return

    def copy_files(self, files_glob: str, output_dir: str):
        """
        Copy files from raw data directory to output directory.
        """
        files_list = glob(files_glob)
        for ifile in files_list:
            infile_dir, infile_name = os.path.split(ifile)
            ofile = os.path.join(output_dir, infile_name)
            if not os.path.isfile(ofile):
                # logging.info(f'Copying file {infile_name} to dir {output_dir}')
                shutil.copyfile(ifile, ofile)
        return


def main():

    # Process command-line args.
    desc = 'Use this application to regrid AVIRIS data.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-f',
                        '--files-glob',
                        type=str,
                        required=True,
                        dest='files_glob',
                        help='Regex to select files to process.')

    parser.add_argument(
                        '-o',
                        '--ouput-dir',
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
                        help='Temporary output directory to store analysis ready data.')

    parser.add_argument(
                        '-n',
                        '--num-procs',
                        type=str,
                        required=False,
                        dest='num_procs',
                        default=cpu_count(),
                        help='Number of cores to use. Defaults to CPU count.')

    args = parser.parse_args()

    # Set logging
    logging.basicConfig(format='%(asctime)s %(message)s', level='INFO')
    timer = time.time()

    awarp = AvirisWarp(args.output_dir, args.temporary_output_dir)
    awarp.process_files(args.files_glob.replace('"', ''))
    logging.info(
        f'Took {(time.time()-timer)/60.0:.2f} min, output at {args.output_dir}.')


# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
