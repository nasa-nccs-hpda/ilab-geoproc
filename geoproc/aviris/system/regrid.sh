#!/bin/bash

source /app/anaconda/platform/x86_64/centos/7/3-2021.11/bin/activate \
        /home/appmgr/app/anaconda/platform/x86_64/centos/7/3-2021.11/envs/ilab

procs=$( ps -ef | grep "above_transfer.py" | grep -v "grep" )

if [ -z "$procs" ]
then
        python /att/nobackup/mjstroud/ABoVE/regrid_only.py | tee /att/nobackup/mjstroud/ABoVE/log/log_$( date +%Y.%m.%d.%H%M ).out
else
        echo "Transfer already running. Cancelling this attempt." > /att/nobackup/mjstroud/ABoVE/log/log_$( date +%Y.%m.%d.%H%M ).out

fi

