import xarray as xa
import matplotlib.pyplot as plt

dest_file = "/tmp/lake_4_patched_water_masks.tif"

da = xa.open_rasterio(dest_file)

fig = plt.figure(figsize=(16,8))
ax = fig.add_subplot(111)
ax.imshow(da.variable.data[0])
plt.show()

