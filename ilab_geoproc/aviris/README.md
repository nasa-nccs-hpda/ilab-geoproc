## Sample execution of regridder script:

```bash
>> cd /att/pubrepo/ILAB/projects/geoProc/
>> ./geoproc/aviris/regridder.py  '/att/pubrepo/ABoVE/archived_data/ORNL/ABoVE_Airborne_AVIRIS_NG/data/ang201707*rfl/ang201707*_rfl_v2p9/ang201707*_v2p9_img' /css/above/AVIRIS_Analysis_Ready
```

## Things to check

- Is it faster if the environment is in another location (not anaconda)
- Where to do the globbing of files?
- Can we speed up gdal warp with multiprocessing?
- Is multiprocessing actually working?
- What about a system with more resources?

## Number of Upper Directories Missing

```bash
Wed Mar 23 09:21:31 EDT 2022
[jacaraba@abovex101 system]$ ls -d /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl | wc
    847     847   77924
[jacaraba@abovex101 system]$ ls -d /css/above/AVIRIS_Analysis_Ready/*rfl | wc
    437     437   24035
[jacaraba@ilab104 ~]$ ls /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*/*h2o*img | wc
    847     847  128744
[jacaraba@ilab104 ~]$ ls -d /css/above/AVIRIS_Analysis_Ready/*rfl | wc
    436     436   23980
[jacaraba@ilab104 ~]$ ls -d /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/*rfl | wc
    423     423   35532


[jacaraba@ilab104 ~]$ ls /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/*rfl/*/*corr*.tif | wc
    423     423   61335
[jacaraba@ilab104 ~]$ ls /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/*rfl/*/*corr*.tif*aux* | wc
    372     372   56916
```

There are a total of 847 directories, the total of h2o files is 847, the total of corr files is 847.

There are a total of 436 directories in /css/above/AVIRIS_Analysis_Ready/*rfl.


There are a total of 423 directories in /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/*rfl.
The total of directories is 859, for which we need to check which directories are repeated.
There are a total of 423 h2o files, 

26

## Benchmarking Regridder with new updates

Command for testing

```bash
python regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170628t165756rfl/ang20170628t165756_rfl_v2p9/*img' -o /css/above/AVIRIS_Analysis_Ready/AVIRIS_Analysis_Ready_Test
```

## Testing Regridder

```bash
python regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang201707*rfl/ang201707*_rfl_v2p9/ang201707*_v2p9_img' /css/above/AVIRIS_Analysis_Ready
```

```bash
[jacaraba@abovex101 system]$ ls /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang201707*rfl/ang201707*_rfl_v2p9/ang201707*_v2p9_img | more
/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170701t182520rfl/ang20170701t182520_rfl_v2p9/ang20170701t182520_corr_v2p9_img
/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170701t182520rfl/ang20170701t182520_rfl_v2p9/ang20170701t182520_h2o_v2p9_img
/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170701t183738rfl/ang20170701t183738_rfl_v2p9/ang20170701t183738_corr_v2p9_img
/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170701t183738rfl/ang20170701t183738_rfl_v2p9/ang20170701t183738_h2o_v2p9_img
...
```

## New version testing

```bash
python regridder.py -f /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl -o /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady
```



(ilab) [jacaraba@ilab112 aviris]$ python regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang201707*rfl/ang201707*_rfl_v2p9/ang201707*_v2p9_img' -o /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady
connect localhost port 6026: Connection refused
2022-03-23 10:04:00,512 Found 2 total raw files.
IN_FILE  /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170731t222832rfl/ang20170731t222832_rfl_v2p9 ang20170731t222832_corr_v2p9_img
IN_DIR  /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170731t222832rfl/ang20170731t222832_rfl_v2p9 /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/ang20170731t222832rfl/ang20170731t222832_rfl_v2p9 ang20170731t222832_corr_v2p9.tif
IN_FILE  /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170731t222832rfl/ang20170731t222832_rfl_v2p9 ang20170731t222832_h2o_v2p9_img
IN_DIR  /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/ang20170731t222832rfl/ang20170731t222832_rfl_v2p9 /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/ang20170731t222832rfl/ang20170731t222832_rfl_v2p9 ang20170731t222832_h2o_v2p9.tif
2022-03-23 10:04:00,528 Took 0.19 min, output at /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady.


## This is what we really need

(ilab) [jacaraba@ilab112 aviris]$ ls /css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img | wc
   1694    1694  258335

(ilab) [jacaraba@ilab112 aviris]$ ls /css/above/AVIRIS_Analysis_Ready/*rfl/*_rfl_*/*_*.tif | wc
    850     850   98175

## Processing Steps

Single ILAB node
```bash
module load singularity
singularity exec -B /adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab,/css/above /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady
```

singularity exec -B /adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab,/css/above /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_h2o_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady

singularity exec -B /adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab,/css/above /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_corr_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady


PRISM node - TBD
```bash
singularity exec -B /adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab,/css/above /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady
```

singularity shell -B /css,/adapt/nobackup/people/jacaraba,/adapt/nobackup/projects/ilab /adapt/nobackup/projects/ilab/containers/ilab-base_gdal-3.3.3.sif

## TODO

- Ray for multiprocessing in the entire cluster
- Document time for experiment with single node (ilab112)
- Document time for experiment with single node Jordan version ILAB (10 files) (ilab111)
- Document time for experiment with single node Jordan version PRISM (10 files)
- Document time for experiment with single node Jordan version multi-thread gdalwarp ILAB (2 files) (ilab110)
- Document time for experiment with single node Jordan version 9000 ws gdalwarp ILAB (10 files) (ilab109)
- Document time for experiment with single node Jordan version 500 ws gdalwarp PRISM 38 files (gpu013)

- Document time for experiment with single node Jordan version multi-thread gdalwarp ILAB (2 files) (ilab110)
250.75 minutes for 30G Mar 24 11:45 ang20180814t194203_corr_v2r2.tif

## References

- https://trac.osgeo.org/gdal/wiki/UserDocs/GdalWarp#WillincreasingRAMincreasethespeedofgdalwarp
- https://github.com/OpenDroneMap/ODM/issues/778

## Example command monitor Directories

```bash
watch -n 30 'ls -lth ang20190708t003752rfl/ang20190708t003752_rfl_v2v2/; ls -lth ang20190703t002744rfl/ang20190703t002744_rfl_v2v1/; ls -lth ang20190801t162339rfl/ang20190801t162339_rfl_v2v2/; ls -lth ang20180818t232352rfl/ang20180818t232352_rfl_v2r2/; ls -lth ang20180721t223058rfl/ang20180721t223058_rfl_v2r2/'
```



python /adapt/nobackup/people/jacaraba/development/geoProc/geoproc/aviris/regridder.py -f '/css/above/daac.ornl.gov/daacdata/above/ABoVE_Airborne_AVIRIS_NG/data/*rfl/*_rfl_*/*_*_img' -o /css/above/AVIRIS_Analysis_Ready -to /adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady