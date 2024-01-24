# ilab-geoproc

Geoprocessing routines for Earth Science Applications.

## Objectives

This project houses several general application used within the ILAB for
processes such as data downloads, preprocessing, etc. It was not designed
as a Python package, but more as a suite of projects.

## Relevant Projects

- [Landsat ARD Management](https://github.com/nasa-nccs-hpda/ilab-geoproc/tree/main/ilab_geoproc/landsat)
- [AVIRIS Management](https://github.com/nasa-nccs-hpda/ilab-geoproc/tree/main/ilab_geoproc/aviris)

## Installation

You can simply clone this repository and use any of the tools needed for your
project. Feel free to active the ilab-pytorch environment from within the Explore
system. If you need to build your own environment, below are some instructions
on how to build a conda environment.

### Build Conda Env

```
>> conda create --name geoproc
>> conda activate geoproc
(geoproc)>> conda install -c conda-forge xarray dask distributed matplotlib datashader colorcet holoviews numpy geopandas descartes utm shapely regionmask iris rasterio cligj bottleneck  umap-learn scipy scikit-learn numba 
(geoproc)>> pip install wget

```

### Install geoProc

```
(geoproc)>> git clone git@github.com:nasa-nccs-cds/geoProc.git
(geoproc)>> cd geoProc
(geoproc)>> python setup.py install
```
