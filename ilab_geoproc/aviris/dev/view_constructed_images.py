import xarray as xa
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.pyplot as plt
import os
image_files = [ 'aviris-image.perceptron-R2-100.nc', "ang20170714t213741_Avg-Chl.tif", "aviris-image.rf-R2-100.tif" ]
DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris/constructed_images"

figure, axes = plt.subplots(1,0)
norm=Normalize( 0.0, 500.0 )

array: xa.DataArray = xa.open_rasterio( os.path.join(DATA_DIR, 'aviris-image.rf-R2-100.tif' ) ).squeeze()
array.plot.imshow( ax = axes[0], cmap="jet", norm=norm )
axes[0].title.set_text("perceptron constructed image")

array: xa.DataArray = xa.open_rasterio( os.path.join(DATA_DIR, "ang20170714t213741_Avg-Chl.tif" ) ).squeeze()
array.plot.imshow( ax = axes[1], cmap="jet", norm=norm )
axes[1].title.set_text("Avg-Chl")

plt.show()


