import os
import sys
from osgeo import gdal
from glob import glob

for hls_dir in os.listdir(sys.argv[1]):

    hls_full_dir = os.path.join(sys.argv[1], hls_dir)

    # check if the string is a dir
    if not os.path.isdir(hls_full_dir):
        continue

    print(hls_full_dir)

    # get the sensor of the dir
    sensor = hls_dir.split('.')[1]
    print("HLS Dir: ", hls_dir, "Sensor: ", sensor)

    # select bands based on sensor
    if sensor == 'S30':
        bands = ['B02', 'B03', 'B04', 'B8A', 'B11', 'B12']
    else:
        bands = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07']

    # gather list of images to stack
    image_list = []
    for band in bands:
        image_list.append(os.path.join(hls_full_dir, f'{hls_dir}.v2.0.{band}.subset.tif'))
    print(image_list)

    VRT = os.path.join(hls_full_dir, f'{hls_dir}.vrt')
    gdal.BuildVRT(VRT, image_list, separate=True, callback=gdal.TermProgress_nocb)

    stacked_image = gdal.Open(VRT, 0)  # open the VRT in read-only mode
    gdal.Translate(os.path.join(sys.argv[1], f'{hls_dir}.tif'), stacked_image, format='GTiff',
               creationOptions=['COMPRESS:DEFLATE', 'TILED:YES'],
               callback=gdal.TermProgress_nocb)
    del stacked_image  # close the VRT
