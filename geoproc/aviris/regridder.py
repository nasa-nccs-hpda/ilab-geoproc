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
        p = Pool( processes=nproc )
        p.map( self.process_file, files_list )
        p.close()

    def process_file(self, input_file: str ):
        args = [ 'gdalwarp', input_file, self.output_file_path(input_file)  ]
        t0 = time.time()
        rv = subprocess.call(args)

        globallock.acquire()
        if rv == 0:    print( f"File '{input_file}' processed in {(time.time()-t0)/60.0:.2f} minutes." )
        else:          print( "Error when processing file '{}'".format(input_file) )
        globallock.release()

    def output_file_path(self, input_file: str ):
        infile_dir, infile_name = os.path.split(input_file)
        ofile_name = infile_name[:-4] if infile_name.endswith("_img") else infile_name
        return  os.path.join( self.outputDir, ofile_name + ".tif" )

def main(argv):
    if len(argv) < 3:
        binary = os.path.basename(argv[0])
        print( "Usage: {} <files_glob> <output_dir> ".format(binary) )
        sys.exit(0)

    files_glob = argv[1]
    output_dir = argv[2]

    awarp = AvirisWarp( output_dir )
    awarp.process_files( files_glob )

if __name__ == '__main__':
#    main(sys.argv)

    output_dir = "/tmp/"
    files_glob = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris/ang20170714t213741_rdn_v2p9/ang*_rdn_v2p9_img"
    awarp = AvirisWarp( output_dir )
    awarp.process_files( files_glob )

#    gdalwarp ang20170731t224547_corr_v2p9_img ang20170731t224547_corr_v2p9.tif