# geoProc
Geoprocessing roputines for Earth Science Applications

### Installation

##### Build Conda Env
```
>> conda create --name geoproc
>> conda activate geoproc
(geoproc)>> conda install -c conda-forge xarray dask distributed matplotlib numpy geopandas descartes shapely regionmask iris rasterio
(geoproc)>> pip install wget

```

##### Install geoProc
```
(geoproc)>> git clone git@github.com:nasa-nccs-cds/geoProc.git
(geoproc)>> cd geoProc
(geoproc)>> python setup.py install
```