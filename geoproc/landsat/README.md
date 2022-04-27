# LandSat

## GladRegridder Over LandSat Data

singularity exec -B /adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab,/css/above /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady



python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/landsat/GladRegridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img'



python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/landsat/GladRegridder.py -f '/adapt/nobackup/projects/ilab/data/LandSatABoVE/54N/*/*.tif' -o /adapt/nobackup/projects/ilab/data/LandSatABoVE/test





