# geoProc
Geoprocessing routines for Earth Science Applications

### Installation

##### Build Conda Env
```
>> conda create --name geoproc
>> conda activate geoproc
(geoproc)>> conda install -c conda-forge xarray dask distributed matplotlib datashader colorcet holoviews numpy geopandas descartes utm shapely regionmask iris rasterio cligj bottleneck  umap-learn scipy scikit-learn numba 
(geoproc)>> pip install wget

```

##### Install geoProc
```
(geoproc)>> git clone git@github.com:nasa-nccs-cds/geoProc.git
(geoproc)>> cd geoProc
(geoproc)>> python setup.py install
```
