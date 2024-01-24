# Landsat GLAD ARD

The Landsat GLAD ARD dataset is a collection of harmonized Landsat data developed by the GLAD UMD
group. The ILAB group is responsible for curating this dataset in the CSS system at the NCCS. The
scripts from this directory are part of the processing required to keep this data archive updated.

The main customer of the GLAD ARD data is the ABoVE group. The download process is composed of three
main steps:

- download
- regridding
- moving data to CSS

We do it this way because transfer nodes to CSS (abovex201) only have 2 CPU cores, which makes the 
data transfer process extremely slow.

![GLAD ARD ABoVE Download](glad-ard.png)

The data has two paths at the NCCS:
  - /css/landsat/Collection2/GLAD_ARD/Native_Grid: original data files downloaded from GLAD ARD
  - /css/landsat/Collection2/GLAD_ARD/ABoVE_Grid: regridded dataset using the ABoVE domain

An additional symlink to the data is under /css/above/glad.umd.edu/Collection2/GLAD_ARD.

## Quick Start

Go to working directory:

```bash
cd /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat
```

Activate anaconda environment:

```bash
module load anaconda
conda activate ilab-pytorch
```

This will load all the needed dependencies to start working on the data.
Below we have documented the different steps needed for the complete download.

## Methods

### 1. GLAD ARD Downloader

The following script allows us to download the GLAD imagery in parallel and across multiple nodes.
We need to be careful to not run out of quota on the intermediate ILAB space. The following is an
example of how to test the GLAD Downloader. You would do the same that is described here, but with
the formal ABoVE_Tiles_All.csv file (which we will fix at some point). The starting interval is 392
for the beginning of the archive. The 1012 interval is the end of 2023.

```bash
python /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/glad_download.py -i /explore/nobackup/projects/ilab/software/ilab-geoproc/ilab_geoproc/landsat/Collection2_requests/ABoVE_Tiles_Test.csv -o /explore/nobackup/projects/ilab/data/LandsatABoVE_GLAD_ARD_Native -s 392 -e 1012
```

### 2. Glad ARD Regridder

```bash
singularity exec -B /adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab,/css/above /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady
```

```bash
python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/landsat/GladRegridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img'
```

```bash
python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/landsat/GladRegridder.py -f '/adapt/nobackup/projects/ilab/data/LandSatABoVE/54N/*/*.tif' -o /adapt/nobackup/projects/ilab/data/LandSatABoVE/test
```

## Tips and Tricks

### Copy Data from One Dir to Another

This is an example of how to copy data from one temporary directory to another.

```bash
rsync -av /explore/nobackup/projects/ilab/data/LandSatARD_C2_ABoVE_TEMP/51N/ /css/landsat/Collection2/GLAD_ARD/Native_Grid/51N
```
