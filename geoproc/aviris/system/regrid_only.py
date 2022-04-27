'''
ornl_auto_data_transfer.py
==========================
Program to transfer desired ORNL data to NCCS storage systems.
This will be accomplished via the following...
    -   Leverage the ORNL update_metadata_curl_files.py script to pull
        desired collection metadata from the CMR.
    -   Use gathered metadata to execute curl commands that will pull the
        selected data collections.

6/17/19
Matthew Stroud - NCCS
'''

# Imports

import sys
import subprocess as sp
import ast
import os
import logging as log
import multiprocessing as mp
import json

#pool = mp.Pool()

# Logging
log.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=log.DEBUG, stream=sys.stdout)


# Define locations.
AVIRIS_DATA_LOC = "/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/"
ADJUSTED_DATA_LOC = "/css/above/AVIRIS_Analysis_Ready/"
SCRIPT_LOC = "/att/nobackup/mjstroud/ABoVE/geoProc/geoproc/aviris/regridder.py"
# Define the process.
def regrid(source):
  log.info(f"Regridding {source}")
  sp.call(f"{SCRIPT_LOC} {source} {ADJUSTED_DATA_LOC}", shell=True)
  log.debug(f"{SCRIPT_LOC} {source} {ADJUSTED_DATA_LOC}")
  log.info(f"Regridding {source}: Done")
# Generate list of files that haven't been regridded.
fileList = []
processedFiles = os.listdir(ADJUSTED_DATA_LOC)
for i in os.listdir(AVIRIS_DATA_LOC):
  if i[-3:]=="rfl":
    if i not in processedFiles:
      file = AVIRIS_DATA_LOC+i
      file = "'"+file+"/"+os.listdir(file)[0]+"/"+"*img'"
      fileList.append(file)

# Run the process on the new data.

#pool.map(regrid, fileList)

for i in fileList:
  regrid(i)

log.info("Done!")

'''


# AVIRIS Data Regridding
# Define locations.
AVIRIS_DATA_LOC = "/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/"
ADJUSTED_DATA_LOC = "/css/above/AVIRIS_Analysis_Ready"
SCRIPT_LOC = "/att/nobackup/mjstroud/ABoVE/geoProc/geoproc/aviris/regridder.py"
# Define the process.
def regrid(source):
  log.info(f"Regridding {source[0]}")
  sp.call(f"{SCRIPT_LOC} {source[0]} {ADJUSTED_DATA_LOC}/{source[1]}", shell=True)
  log.info(f"Regridding {source[0]}: Done")
# Generate list of files that haven't been regridded.
fileList = []
processedFiles = os.listdir(ADJUSTED_DATA_LOC)
for i in os.listdir(AVIRIS_DATA_LOC):
  if i[-3:]=="rfl":
    if i in processedFiles:
      file = AVIRIS_DATA_LOC+i
      file = "'"+file+"/"+os.listdir(file)[0]+"/"+"*img'"
      fileList.append([file, i])

# Run the process on the new data.
#pool.map(regrid, fileList)
for i in fileList:
  regrid(i)

'''

