#! /usr/bin/env python
from glob import glob
from typing import Dict, List, Tuple, Union, Optional
import sys, time, shutil
import xarray as xa
import subprocess
from multiprocessing import Pool, Lock, cpu_count
import os.path

globallock = Lock()

class AvirisWarp:

    def __init__(self, outputDir: str):
        self.outputDir = outputDir

    def needs_processing(self, output_file ) -> bool:
        try:
            test_data = xa.open_rasterio(output_file)
        except:
            if os.path.isfile(output_file): os.remove(output_file)
            return True
        return False

    def get_unprocessed_filepaths(self, files_glob: str ) -> List[str]:
        filelist = glob( files_glob )
        filtered_file_list = []
        for input_file in filelist:
            input_dir, output_dir, output_file = self.get_file_paths(input_file)
            output_file_path = os.path.join(output_dir, output_file)
            if self.needs_processing(output_file_path):
                filtered_file_list.append( input_file )
        print( f"Processing {len(filtered_file_list)} files out of {len(filelist)}, files requiring processing = {[os.path.basename(f) for f in filelist]}")
        return filtered_file_list

    def process_files( self, files_glob: str, **kwargs ):
        files_list = self.get_unprocessed_filepaths( files_glob )
        nproc = kwargs.get('np', cpu_count() )
        print( f"Using {nproc} processors to process {len(files_list)} files from the glob '{files_glob}'")
        p = Pool( processes=nproc )
        p.map( self.process_file, files_list )
        p.close()
        p.join()

    def process_file( self, input_file: str ):
        input_dir, output_dir, output_file = self.get_file_paths(input_file)
        output_file_path = os.path.join( output_dir, output_file )
        if not self.needs_processing( output_file_path ):
            globallock.acquire()
            print( f"Skipping file {input_file}: Processed file already exists at {output_file_path}")
            globallock.release()
        else:
            globallock.acquire()
            print(f"Processing file '{input_file}'")
            globallock.release()

            self.copy_files( f"input_dir/*README*", output_dir )
            t0 = time.time()

            args = [ 'gdalwarp', '-co', 'COMPRESS=LZW', '-co', 'BIGTIFF=YES', input_file, output_file_path ]
            rv = subprocess.call(args)

            globallock.acquire()
            if rv == 0:    print( f"File '{output_file}' generated in {(time.time()-t0)/60.0:.2f} minutes in output-dir {output_dir}." )
            else:          print( f"Error when processing file '{input_file}'" )
            globallock.release()

    def get_file_paths( self, input_file: str ) -> Tuple[str,str,str]:
        infile_dir, infile_name = os.path.split(input_file)
        base1, dir1 = os.path.split(infile_dir)
        base0, dir0 = os.path.split(base1)
        ofile_name = infile_name[:-4] if infile_name.endswith("_img") else infile_name
        ifile_outputdir = os.path.join( self.outputDir, dir0, dir1 )
        os.makedirs( ifile_outputdir, mode=0o777, exist_ok=True )
        return  infile_dir, ifile_outputdir, ofile_name + ".tif"

    def copy_files(self, files_glob, output_dir ):
        files_list = glob(files_glob)
        for ifile in files_list:
            infile_dir, infile_name = os.path.split( ifile )
            ofile = os.path.join( output_dir, infile_name )
            if not os.path.isfile( ofile ):
                print( f"Copying file {infile_name} to dir {output_dir}")
                shutil.copyfile( ifile, ofile )

def main(argv):
    if len(argv) < 3:
        binary = os.path.basename(argv[0])
        print( "Usage: {} <files_glob> <output_dir> [ <nproc> ]".format(binary) )
        sys.exit(0)

    t0 = time.time()
    kwargs = {}
    files_glob = argv[1]
    output_dir = argv[2]
    if len(argv) > 3:
        kwargs['np'] = argv[3]

    awarp = AvirisWarp( output_dir )
    awarp.process_files( files_glob.replace('"', ''), **kwargs )
    print( f"Files processed in {(time.time()-t0)/60.0:.2f} minutes to output-dir {output_dir}.")

if __name__ == '__main__':
    main(sys.argv)