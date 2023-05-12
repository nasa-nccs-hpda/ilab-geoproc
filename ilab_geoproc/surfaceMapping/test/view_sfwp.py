from typing import List, Union, Tuple, Dict, Optional
import xarray as xa
import numpy as np, os
from typing import Dict, List, Tuple
from osgeo import osr, gdalconst, gdal
from pyproj import Proj, transform
from shapely.geometry import Polygon
import xarray as xr, regionmask, utm
from geoproc.xext.xextension import XExtension
import rasterio
from rasterio import Affine as A
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling, transform, calculate_default_transform
import matplotlib.pyplot as plt


def reproject_to_geographic( image: xr.DataArray ) -> xr.DataArray:
    with rasterio.Env():
        src_shape = image.shape
        src_transform = image.transform
        src_crs =  CRS( {'init': image.crs.split("=")[1].upper() } )
        source: np.ndarray = image.data
        xaxis: np.ndarray = image.coords[image.dims[1]].data
        yaxis: np.ndarray = image.coords[image.dims[0]].data

        dst_shape = src_shape
        dst_crs = CRS(  {'init': 'EPSG:4326'} )
        dst_transform = calculate_default_transform(src_crs, dst_crs, dst_shape[1], dst_shape[0],
                                                    left=src_transform[2],
                                                    bottom=src_transform[5] + src_transform[3] * dst_shape[1] + src_transform[4] * dst_shape[0],
                                                    right=src_transform[2] + src_transform[0] * dst_shape[1] + src_transform[1] * dst_shape[0],
                                                    top=src_transform[5])[0]
        destination = np.zeros(dst_shape, np.uint8)

        reproject(
            source,
            destination,
            src_transform=src_transform,
            src_crs=src_crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest)

        (lons, lats) = transform( Proj(**src_crs), Proj(**dst_crs), xaxis, yaxis )

        result = xr.DataArray(destination, dims=['lat', 'lon'], coords=dict(lat=np.array(lats), lon=np.array(lons) ))
        result.attrs['transform'] = dst_transform
        result.attrs['crs'] = dst_crs
        return result


def plot_image( file_path: str, crange: List[float], image_index: int = 0):
    print(f"Viewing geotiff: {file_path}")
    array: xa.DataArray = xa.open_rasterio(file_path)
    names = array.attrs['descriptions']
    fig, ax = plt.subplots(1, 1)
    image = reproject_to_geographic( array[image_index] )
    print(f"Plotting array {names[image_index]}, shape = {image.shape}")
    image.plot.imshow(ax=ax, cmap="jet", vmin=crange[0], vmax=crange[1])
    ax.title.set_text(names[image_index])
    plt.show()


plot_band = "dswe"
result_name = '/Users/tpmaxwel/GoogleDownloads/swe_prediciton_LE07-C01-T1_SR_036012.tif' # '/Users/tpmaxwel/GoogleDrive/dswe/dswe_LE07-C01-T1_SR_36-12.tif' # ''/Users/tpmaxwel/GoogleDrive/dswe/dswe_LE07-C01-T1_SR_36-12.tif'
print(f"Viewing result {result_name}")
#taskMgr.plot_image( result_name, [0,5], 5 )
plot_image( result_name, [0,256], 0 )

