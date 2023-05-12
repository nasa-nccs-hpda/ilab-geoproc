import yaml, os
from geoproc.surfaceMapping.processing import LakeMaskProcessor

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
opspec_file = os.path.join(BASEDIR, "specs", "lakes-test.yml")
reproject_inputs = False
with open(opspec_file) as f:
    opspecs = yaml.load(f, Loader=yaml.FullLoader)
    lakeMaskProcessor = LakeMaskProcessor(opspecs)
    lakeMaskProcessor.process_lakes( reproject_inputs, format="tif" )

