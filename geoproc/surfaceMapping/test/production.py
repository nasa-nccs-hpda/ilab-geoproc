from typing import List, Union, Tuple, Dict, Optional
from glob import glob
from geoproc.surfaceMapping.processing import LakeMaskProcessor
from geoproc.plot.animation import SliceAnimation
import os, time, collections

import yaml
CURDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = '/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Birkett'
opspec_file = os.path.join(CURDIR, "specs", "lakes-test.yml")
with open(opspec_file) as f:
    opspecs = yaml.load( f, Loader=yaml.FullLoader )
    lakeMaskProcessor = LakeMaskProcessor( opspecs )
    results = lakeMaskProcessor.process_lakes()
    anim_inputs = [ ]
    for result in results.values():
        anim_inputs.extend( result )
    animation = SliceAnimation( anim_inputs )
    animation.show()


