#!/bin/bash

# forest[201-210]
# ilab[201-212]

export PATH="/panfs/ccds02/app/modules/anaconda/platform/x86_64/rhel/8.6/3-2022.05/bin:$PATH"
eval "$(conda shell.bash hook)"
conda activate ilab-pytorch

HOSTNAME=`hostname`
echo $HOSTNAME

# /explore/nobackup/projects/ilab/data/LandsatABoVE_GLAD_ARD_Native_All
# /explore/nobackup/people/jacaraba/development/ilab-geoproc/ilab_geoproc/landsat/Collection2_requests/GLAD_ARD_Tiles_ABoVE_forest210
echo /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/Collection2_vrt_requests/GLAD_ARD_Tiles_ABoVE_${HOSTNAME}

python /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/2_gen_vrt.py \
    -if /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/Collection2_vrt_requests/GLAD_ARD_Tiles_ABoVE_${HOSTNAME} \
    -i /css/landsat/Collection2/GLAD_ARD/Native_Grid \
    -o /explore/nobackup/projects/ilab/data/ABoVE_Grid_Update/ABoVE_Grid_Landsat_VRTs \
    -s 392 \
    -e 1012
