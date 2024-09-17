# Landsat GLAD ARD

The Landsat GLAD ARD dataset is a collection of harmonized Landsat data developed by the GLAD UMD
group. The ILAB group is responsible for curating this dataset in the CSS system at the NCCS. The
scripts from this directory are part of the processing required to keep this data archive updated.

The main customer of the GLAD ARD data is the ABoVE group. The download process is composed of three
main steps:

- download
- generating VRTs
- regridding

We do it this way because transfer nodes to CSS (abovex201) only have 2 CPU cores, which makes the 
data transfer process extremely slow. We have a temporary transfer node to accelerate the process
for this rounds of upgrades (2024-04-03). As of 9/16/2024, we have more transfer nodes so can download 
directly to CSS.

![GLAD ARD ABoVE Download](glad-ard.png)

The data has two paths at the NCCS:
  - /css/landsat/Collection2/GLAD_ARD/Native_Grid: original data files downloaded from GLAD ARD
  - /css/landsat/Collection2/GLAD_ARD/ABoVE_Grid: regridded dataset using the ABoVE domain

An additional symlink to the data is under /css/above/glad.umd.edu/Collection2/GLAD_ARD.

## Quick Start during Development

Go to working directory:

```bash
ssh ilabx201
cd /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat
```

Activate anaconda environment:

```bash
module load anaconda
conda activate ilab-pytorch
```

This will load all the needed dependencies to start working on the data.
Below we have documented the different steps needed for the complete download.

## Operation Methods

### 1. GLAD ARD Downloader

The following script allows us to download the GLAD imagery in parallel and across multiple nodes.
We need to be careful to not run out of quota on the intermediate ILAB space. The following is an
example of how to test the GLAD Downloader. You would do the same that is described here, but with
the formal ABoVE_Tiles_All.csv file (which we will fix at some point). The starting interval is 392
for the beginning of the archive. The 1012 interval is the end of 2023. The current intervals can be 
found here: https://glad.umd.edu/dataset/glad_ard2/. As of 8/20/2024 interval is 1026. Unless the 
processing changes, can just process the new interval.

```bash
python /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/1_glad_download.py -i /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/GLAD_ARD_Collection2_Download_Tiles/GLAD_ARD_Tiles_ABoVE_ALL.csv -s 392 -e 1026
```

If needing to process in parallel, an example operations command for the ADAPT login nodes is: 

```bash
pdsh -w forest[201-210] 'bash /explore/nobackup/people/jacaraba/development/ilab-geoproc/ilab_geoproc/landsat/run_download_pdsh.sh'
pdsh -w ilab[201-212] 'bash /explore/nobackup/people/jacaraba/development/ilab-geoproc/ilab_geoproc/landsat/run_download_pdsh.sh'
```

Once the data has been downloaded, go ahead and transfer the data to CSS:

fpsync method (preferred)

```bash
ssh ilabx201
fpsync -f 1000 -n 32 /explore/nobackup/projects/ilab/data/LandsatABoVE_GLAD_ARD_Native_All /css/landsat/Collection2/GLAD_ARD/Native_Grid_Update/LandsatABoVE_GLAD_ARD_Native_All
```

shiftc method

```bash
ssh ilabx201
shiftc -r -d --wait --monitor=color /explore/nobackup/projects/ilab/data/LandsatABoVE_GLAD_ARD_Native_All /css/landsat/Collection2/GLAD_ARD/Native_Grid_Update
```

### 2. GLAD ARD VRT Generator

The second step of this workflow is to generate a VRT for each tile that includes the depth
in time of the particular tile. To make this run in a timely fashion we will use all the
available nodes. For this we need to create some filenames that will allow us to pdsh across
multiple nodes. The steps are as follow:

- we create the filename with the intervals
- we split these into the nodes we have available
- we generate the final interval filenames with the node appended to the end of the filename

The following script takes care of the entire setup process:

```bash
bash setup_gen_vrt.sh
```

Once this is setup, we can proceed to generate the VRTs across multiple nodes:

```bash
pdsh -w ilab[201-212] 'bash /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/run_gen_vrt_pdsh.sh'
pdsh -w forest[201-210] 'bash /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/run_gen_vrt_pdsh.sh'
```

### 3. Glad ARD Regridder

The last step is to regrid the imagery. For the operational workflow we are working on 2024-04-03, the following paths
are what we need:

- Original Data: /css/landsat/Collection2/GLAD_ARD/Native_Grid
- VRTs: /explore/nobackup/projects/ilab/data/ABoVE_Grid_Update/ABoVE_Grid_Landsat_VRTs
- Intermediate Output Data Explore: /explore/nobackup/projects/ilab/data/ABoVE_Grid_Update
- Final Output Data CSS: /css/landsat/Collection2/GLAD_ARD/ABoVE_Grid_Update

Given this information, the following script is used for reprojection purposes. This assumes we already have the
VRTs in place, and the files per node with the individual time intervals per node.

The best way to run this is to:

1. Create a screen session on adaptlogin
2. Modify the horizontal and vertical tiles from the run_reproject_pdsh.sh file
3. Run setup of pdsh files to run in parallel (already done, no need to repeat)

```bash
cd /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat
bash setup_reproject.sh
```

4. Run the following command through the different nodes

```bash
pdsh -w ilab[201-212] 'bash /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/run_reproject_pdsh.sh'
pdsh -w forest[201-210] 'bash /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/run_reproject_pdsh.sh'
```

5. Monitoring the performance and run time using `htop` from one of the ilab nodes
6. Transfer the data to CSS, once this is confirmed, you can delete the data from Explore and repeat the process with other tiles.

```bash
ssh ilabx201
fpsync -f 1000 -n 32 /explore/nobackup/projects/ilab/data/ABoVE_Grid_Update /css/landsat/Collection2/GLAD_ARD/ABoVE_Grid_Update
```

## Tips and Tricks

### Copy Data from One Dir to Another

This is an example of how to copy data from one temporary directory to another.

```bash
rsync -av /explore/nobackup/projects/ilab/data/LandSatARD_C2_ABoVE_TEMP/51N/ /css/landsat/Collection2/GLAD_ARD/Native_Grid/51N
```
