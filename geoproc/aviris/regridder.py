#! /usr/bin/env python
from glob import glob
import sys, time
import subprocess
from multiprocessing import Pool, Lock, cpu_count
import os.path

globallock = Lock()

class AvirisWarp:

    def __init__(self, outputDir: str):
        self.outputDir = outputDir

    def process_files( self, files_glob: str, **kwargs ):
        files_list = glob(files_glob)
        nproc = kwargs.get('np', cpu_count() )
        print( f"Using {nproc} processors to process the files {files_list}")
        p = Pool( processes=nproc )
        p.map( self.process_file, files_list )
        p.close()

    def process_file(self, input_file: str ):
        globallock.acquire()
        print( f"Processing file '{input_file}'" )
        globallock.release()
        output_file = self.output_file_path(input_file)
        t0 = time.time()

        args = [ 'gdalwarp', '-co', 'GTiff', '-co', 'COMPRESS=LZW', '-co', 'BIGTIFF=YES', input_file, output_file ]
        rv = subprocess.call(args)

        globallock.acquire()
        if rv == 0:    print( f"File '{output_file}' generated in {(time.time()-t0)/60.0:.2f} minutes." )
        else:          print( f"Error when processing file '{input_file}'" )
        globallock.release()

    def output_file_path(self, input_file: str ):
        infile_dir, infile_name = os.path.split(input_file)
        ofile_name = infile_name[:-4] if infile_name.endswith("_img") else infile_name
        return  os.path.join( self.outputDir, ofile_name + ".tif" )

def main(argv):
    if len(argv) < 3:
        binary = os.path.basename(argv[0])
        print( "Usage: {} <files_glob> <output_dir> [ <nproc> ]".format(binary) )
        sys.exit(0)

    kwargs = {}
    files_glob = argv[1]
    output_dir = argv[2]
    if len(argv) > 3:
        kwargs['np'] = argv[3]

    awarp = AvirisWarp( output_dir )
    awarp.process_files( files_glob, **kwargs )

if __name__ == '__main__':
    main(sys.argv)