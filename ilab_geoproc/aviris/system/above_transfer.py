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

# Configuration

# Location of metadata query script, and destination for pulled metadata.
metadata_dir = "/att/nobackup/mjstroud/ABoVE/"
# Output location for downloaded data.
#data_dir = "/att/pubrepo/ORNL/ABoVE_Archive/"
data_dir = "/css/above/"
# Project tags to exclude undesired collections.
exclude_list = ["BOREAS", "CARVE", "CMS", "NACP"]
# Set log verbosity and format.
log.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=log.DEBUG, stream=sys.stdout)

# Pre-Defined Functions

def fix_bools(string):
    """
    Replace lowercase 'true' and 'false' values in metadata with propercase
    'True' and 'False' that will be recognized by python when converted
    from string to boolean.
    """
    new_string = string.replace("true","True")
    new_string = new_string.replace("false","False")
    return new_string


def cmrQuery():
    """
    Use ORNL's CMR query script to generate curl commands to pull tagged
    metadata
    """
    log.info("Querying CMR.")
    sys.path.append(metadata_dir)
    import update_metadata_curl_files as umcf
    umcf.main(
        data_center="all",
        project="above",
        update_collections=True,
        update_granules=True,
        events=umcf.PrintEvents(),
        temp_dir="{}tmp".format(metadata_dir),
        output_dir="{}out".format(metadata_dir)
    )
    log.info("Querying CMR: Done")


def removeCollections(excludeList):
    """
    Exclude specific collections that will be ABoVE tagged, but that are not
    desired. This will delete the CMR generated directories.
    """
    log.info("Removing unwanted collections.")
    log.debug("Exclude list -> {}".format(excludeList))
    # Remove generated curl commands for excluded collections.
    for collection in excludeList:
        sp.call("rm -rf {}out/{}*".format(metadata_dir,collection),shell=True)
        log.debug("{} excluded.".format(collection))
    log.info("Collections filtered.")


def getCollections():
    """
    Get a list of generated directories by the CMR query.
    """
    collections = [dir for dir in os.listdir(metadata_dir+"out/")
                    if not os.path.isfile(os.path.join(metadata_dir+"out/"))]
    log.info("Collections queued.")
    log.debug("Collections -> {}".format(collections))
    return collections


def asfCollection():
    # Command to pull ASF file list.
    sp.call("curl 'https://api.daac.asf.alaska.edu/services/search/param?platform=UAVSAR&bbox=-166.7,49.08,-95.42,71.18&output=json' -o {}asf.json".format(metadata_dir), shell=True)
    with open("{}asf.json".format(metadata_dir)) as asfFiles:
        fileDicts = json.load(asfFiles)
    fileList = []
    for i in fileDicts:
        for j in i:
            fileList.append(j.get('downloadUrl'))
    return fileList


def wgetCommand(file):
  if "ngee" in file:
    return
  else:
    sp.call("wget -N -c --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --no-check-certificate --auth-no-challenge=on -r --reject \"index.html*\" -np -e robots=off --directory-prefix={} {}".format(data_dir,file),shell=True)
    log.debug("Command -> wget -N -c --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --no-check-certificate --auth-no-challenge=on -r --reject \"index.html*\" -np -e robots=off --directory-prefix={} {}".format(data_dir,file))



# Go through collection list and get metadata for each collection.
# Then use the metadata to pull data from HTTPS server.
def pullCollection(collection):
    log.info("Getting {} data.....".format(collection))
    collection_dir = metadata_dir+"out/"+collection

    # Get generated curl command for collection.
    with open(collection_dir+"/metadata/metadata.curl") as file:
        first_line = file.readline()
    sp.call("cd "+collection_dir+"/metadata/ && "+first_line,shell=True)
    log.debug("Command -> {}".format(first_line))

    # Read metadata pulled via curl command.
    try:
        with open(collection_dir+"/metadata/"+collection+".json") as file:
            metadata = file.readline()
        log.info("{} metadata acquired.".format(collection))
    except:
        log.info("CMR metadata not found for {}".format(collection))
        return

    # Fix boolean values in metadata and convert to dictionary.
    metadata = ast.literal_eval(fix_bools(metadata))

    # Exclude undesired collections not tagged by name.
    cancel = False
    for exclude in exclude_list:
        if(metadata.get('dataset_id').find(exclude)!=-1):
            cancel = True
            break
    if(cancel):
        log.info("Collection {} to be excluded....skipping".format(collection))
        return

    # From the metadata pull the link to download data.
    link = metadata.get('links')[0].get('href')
    addChar = ""
    if link[-1]!="/":
        addChar = "/"

    # Get the list of files in the collection.
    fileList = []
    dirs = [link]
    log.info("Getting file list for {}.".format(collection))
    while dirs:
        newDirs = []
        for dir in dirs:
            log.debug("Command -> wget -q -O - -np -nd --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --no-check-certificate --auth-no-challenge=on {} | grep \"<tr\" | grep -v \"href=\\\"?\" | grep -v \"Parent Directory\" | awk -F \'href=\\\"\' \'{{print $2}}\' | awk -F \'\\\"\' \'{{print $1}}\'".format(dir))
            children = sp.check_output("wget -q -O - -np -nd --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --no-check-certificate --auth-no-challenge=on {} | grep \"<tr\" | grep -v \"href=\\\"?\" | grep -v \"Parent Directory\" | awk -F \'href=\\\"\' \'{{print $2}}\' | awk -F \'\\\"\' \'{{print $1}}\'".format(dir),shell=True).decode("utf-8").split('\n')[:-1]
            for child in children:
                if child == "":
                    continue
                elif child[-1] != "/":
                    fileList.append(dir+child)
                else:
                    newDirs.append(dir+child)
        dirs = newDirs
    return fileList

def compFile(f):
    root = f[0]
    file = f[1]
    if file[-4:]==".zip":
        log.info("Unzipping {}/{}".format(root,file))
        sp.call("mkdir {0}/{2} && unzip -u {0}/{1} -d {0}/{2}".format(root,file,file[:-4]),shell=True)
        return
    if file[-7:]==".tar.gz":
        log.info("Decompressing {}/{}".format(root,file))
        sp.call("mkdir {0}/{2} && tar xvzf {0}/{1} -C{0}/{2}".format(root,file,file[:-7]),shell=True)


# Runtime

cmrQuery()
removeCollections(exclude_list)

pool = mp.Pool(4)

for collection in getCollections():
    try:
        pool.map(wgetCommand,pullCollection(collection))
    except:
        continue

pool.map(wgetCommand, asfCollection())

log.info("Extracting compressed files.")
# Unzip all compressed files pulled
fileList = []
for root, dir, files in os.walk(data_dir):
    for file in files:
        cont = True
        for d in dir:
            if file==d+".zip" or file==d+".tar.gz":
                cont = False
                break
        if cont:
            fileList.append([root,file])
pool.map(compFile, fileList)

"""
# AVIRIS Regrid
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
for i in fileList:
  regrid(i)
"""

# Close the Pool.
pool.close()
pool.join()
log.info("Done!")

