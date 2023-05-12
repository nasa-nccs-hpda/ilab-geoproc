from glob import glob
import xarray as xa
from geoproc.xext.xgeo import XGeo
import os

class FormatConverter:

    def __init__(self):
        pass

    def convert(self, files_glob: str, varname: str ):
        for file in glob(files_glob):
            input: xa.Dataset = self.open( file )
            self.write( os.path.splitext(file)[0], input[varname] )

    def open(self, file_path: str ) -> xa.Dataset:
        print( f"Opening input file {file_path}")
        return xa.open_dataset( file_path )

    def write( self, base_file_name: str, data_array: xa.DataArray ):
        output_file =  base_file_name + ".tif"
        print(f"Writing output_file {output_file}")
        data_array.xgeo.to_tif( output_file )


if __name__ == '__main__':
    input_files = '/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris/constructed_images/*.nc'
    fc = FormatConverter()
    fc.convert( input_files, 'constructed_image' )