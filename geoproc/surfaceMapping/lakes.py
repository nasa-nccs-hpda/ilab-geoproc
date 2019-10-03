import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
import urllib.request
from urllib.error import HTTPError
import os

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Birkitt"
location: str = "120W050N"
product: str = "1D1OS"
year = 2019

def download_MWP_files( year: int = 2019, start_day: int = 1, end_day: int = 365, location: str = "120W050N", product: str = "1D1OS", download = False ):
    files = []
    for iFile in range(start_day,end_day+1):
        target_file = f"MWP_{year}{iFile}_{location}_{product}.tif"
        target_file_path = os.path.join( DATA_DIR, target_file )
        if not os.path.exists( target_file_path ):
            if download:
                target_url = f"https://floodmap.modaps.eosdis.nasa.gov/Products/{location}/{year}/{target_file}"
                try:
                    urllib.request.urlretrieve( target_url, target_file_path )
                    print(f"Downloading url {target_url} to file {target_file_path}")
                    files.append(target_file)
                except HTTPError:
                    print( f"     ---> Can't access {target_url}")
        else:
            files.append( target_file_path )
    return files


files = download_MWP_files( year, 1, 365, location, product )

#testFileIndex  = 35
# TEST_FILE = files[testFileIndex]
# da: xr.DataArray = xr.open_rasterio( TEST_FILE )
# band0 = da[0]
# ax = plt.axes(projection=ccrs.PlateCarree())
# band0.plot.imshow(cmap='jet')
# ax.coastlines()

fig = plt.figure()

ims = []
for file in files:
    da: xr.DataArray = xr.open_rasterio( file )
    im = plt.imshow( da[0].values, animated=True)
    ims.append([im])

ani = animation.ArtistAnimation(fig, ims, interval=50, blit=True, repeat_delay=1000)

ani.save( os.path.join( DATA_DIR, f'MWP_{year}_{location}_{product}.mp4' ) )

plt.show()