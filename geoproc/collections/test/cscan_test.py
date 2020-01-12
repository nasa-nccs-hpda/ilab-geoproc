from geoproc.collections.scan import FileScanner
import os

collectionName = "merra_daily_local_test1"
data_dir = os.path.expanduser( "~/Dropbox/Tom/Data/MERRA/DAILY" )

args = dict( path=data_dir, ext="nc"  )
scanner = FileScanner( collectionName, **args )
scanner.write()