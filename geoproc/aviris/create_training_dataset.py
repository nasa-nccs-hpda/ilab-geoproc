import xarray as xa
import numpy as np
import os, pickle

DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
aviris_tile = "ang20170714t213741"
scale_threshold = 10.0
n_training_samples = "full"

def get_indices(valid_mask: np.ndarray) -> np.ndarray:
    return np.extract(valid_mask, np.array(range(valid_mask.size)))

print("Reading Data")

target_file = os.path.join(DATA_DIR, "results", f"{aviris_tile}_Avg-Chl.nc")
target_dataset: xa.DataArray = xa.open_dataset(target_file)
y_data_full: np.ndarray = target_dataset.band_data.squeeze().stack(samples=('x', 'y'))
valid_mask: np.ndarray = np.isnan(y_data_full) != True
y_data_filtered = y_data_full.where(valid_mask, drop=True)

input_file = os.path.join(DATA_DIR, "results", f"{aviris_tile}_corr_v2p9.nc")
aviris_dataset: xa.Dataset = xa.open_dataset(input_file)
filtered_input_bands: xa.DataArray = aviris_dataset.band_data.where(aviris_dataset.scale < scale_threshold, drop=True)
train_data_filtered = filtered_input_bands.stack(samples=('x', 'y')).transpose().isel(samples=get_indices(valid_mask))

if n_training_samples == "full":
    x_data_norm = train_data_filtered.reset_index( "samples" )
    y_data = y_data_filtered.reset_index( "samples" )
else:
    x_data_norm = train_data_filtered[:n_training_samples].reset_index( "samples" )
    y_data = y_data_filtered[:n_training_samples].reset_index( "samples" )

xoutFile = os.path.join(outDir, f"{aviris_tile}_xtrain_{n_training_samples}.nc")
print(f"Writing xtraining data to {xoutFile}")
xdset = xa.Dataset( { "xdata": x_data_norm } )
xdset.to_netcdf(xoutFile)

youtFile = os.path.join(outDir, f"{aviris_tile}_ytrain_{n_training_samples}.nc")
print(f"Writing ytraining data to {youtFile}")
ydset = xa.Dataset( { "ydata": y_data } )
ydset.to_netcdf(youtFile)