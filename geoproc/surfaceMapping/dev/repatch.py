from geoproc.plot.animation import SliceAnimation
from geoproc.surfaceMapping.lakeExtentMapping import WaterMapGenerator
import yaml, os

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
opspec_file = os.path.join(BASEDIR, "specs", "lakes1.yml")
with open(opspec_file) as f:
    opspecs = yaml.load(f, Loader=yaml.FullLoader)
    waterMapGenerator = WaterMapGenerator(opspecs)
    patched_water_maps = waterMapGenerator.repatch_water_maps("Lake1295")
    roi = patched_water_maps.attrs.get("roi")
    kwargs = dict(overlays=dict(red=roi.boundary)) if (roi and not isinstance(roi, list)) else {}

    animation = SliceAnimation([waterMapGenerator.water_maps, patched_water_maps, waterMapGenerator.persistent_classes], **kwargs)
    animation.show()