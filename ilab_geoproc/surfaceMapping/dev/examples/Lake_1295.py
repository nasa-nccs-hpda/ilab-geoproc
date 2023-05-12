from geoproc.surfaceMapping.lakeExtentMapping import WaterMapGenerator
import yaml, os

BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
opspec_file = os.path.join(BASEDIR, "specs", "lakes1.yml")

with open(opspec_file) as f:
    opspecs = yaml.load(f, Loader=yaml.FullLoader)
    waterMapGenerator = WaterMapGenerator(opspecs)
    waterMapGenerator.view_water_map_results( "Lake1295"  )
