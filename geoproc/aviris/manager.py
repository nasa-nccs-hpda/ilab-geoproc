import xarray as xa
import numpy as np
from typing import List, Union, Tuple, Optional
from sklearn.linear_model import LinearRegression
import os, math


class AvirisDataManager:

    def __init__(self, nbands: int, name = "band_data" ):
        self.nbands = nbands
        self.name = name

    def get_indices(self, valid_mask: np.ndarray) -> np.ndarray:
        return np.extract(valid_mask, np.array(range(valid_mask.size)))

    def normalize( self, input_bands: xa.DataArray, uniform = False ) -> Tuple[xa.DataArray,Optional[xa.DataArray]]:
        axes = {} if uniform else dict(dim=['x', 'y'])
        centered = input_bands - input_bands.mean( **axes )
        scale = centered.std( **axes )
        band_data: xa.DataArray =  centered / scale
#        result = band_data.assign_coords( dict( x=input_bands.x, y=input_bands.y ) )
        band_data.attrs["transform"] = input_bands.transform
        band_data.attrs["crs"] = input_bands.crs
        return band_data, scale

    def mean_squared_error(self, x: np.ndarray, y: np.ndarray) -> float:
        diff = x - y
        return math.sqrt( np.mean( diff * diff ) )

    def read( self, filepath: str, ignore_value = None ) -> xa.DataArray:
        full_input_bands: xa.DataArray = xa.open_rasterio( filepath )
        nodata_value = int(full_input_bands.attrs['data_ignore_value']) if ignore_value is None else ignore_value
        raw_input_bands = full_input_bands[0:self.nbands,:,:]
        input_bands: xa.DataArray = raw_input_bands.where(raw_input_bands != nodata_value, float('nan') )
        input_bands.name = self.name
        return input_bands

    def get_binned_sampling(self, x_data_train: xa.DataArray, y_data_train: xa.DataArray, n_bins: int=16, n_samples_per_bin: int = 50) -> Tuple[xa.DataArray, xa.DataArray]:
        training_indices = []
        samples_axis = y_data_train[y_data_train.dims[0]]
        groupby = samples_axis.groupby_bins(y_data_train, n_bins)
        for sbin in groupby:
            binned_indices: xa.DataArray = sbin[1].astype(np.int64)
            ns = binned_indices.size
            if ns <= n_samples_per_bin:
                training_indices.append(binned_indices.values)
            else:
                selection_indices = np.linspace(0, ns - 1, n_samples_per_bin).astype(np.int64)
                sample_indices = binned_indices.isel(samples=selection_indices)
                training_indices.append(sample_indices.values)
            print(f"  *  Bin range = {sbin[0]}; NSamples total = {ns}, actual = {training_indices[-1].size} ")

        np_training_indices = np.concatenate(training_indices)
        x_data_binned = x_data_train.isel(samples=np_training_indices, drop=True)
        y_data_binned = y_data_train.isel(samples=np_training_indices, drop=True)
        print(f"Using {y_data_binned.size} samples out of {y_data_train.size}: {(y_data_binned.size * 100.0) / y_data_train.size:.2f}%")
        return x_data_binned, y_data_binned

    def restructure_for_training(self, x_data_array: xa.DataArray, y_data_array: xa.DataArray ) ->  Tuple[xa.DataArray, xa.DataArray]:
        dims = x_data_array.dims[1:]
        x_stacked_data, y_stacked_data = x_data_array.stack( samples=dims ), y_data_array.stack( samples=dims ).squeeze()
        x_undef = np.isnan( x_stacked_data.values.sum( axis=0 ) )
        y_undef = np.isnan( y_stacked_data.values )
        valid_mask = np.logical_not( np.logical_or( x_undef, y_undef ) )
        x_stacked_data_masked = x_stacked_data.isel(samples=self.get_indices(valid_mask)).transpose()
        y_stacked_data_masked = y_stacked_data.isel(samples=self.get_indices(valid_mask))
        samples_coord = np.array(range(x_stacked_data_masked.shape[0]))
        return x_stacked_data_masked.assign_coords(samples=samples_coord), y_stacked_data_masked.assign_coords(samples=samples_coord)

    def regress( self, x_data_train: xa.DataArray, y_data_train: xa.DataArray, **kwargs ) -> Tuple[np.ndarray,float,LinearRegression]:
        x, y = x_data_train.values, y_data_train.values
        estimator: LinearRegression = LinearRegression()
        reg = estimator.fit( x, y, **kwargs )
        y_prediction = estimator.predict(x)
        mse_train = self.mean_squared_error( y, y_prediction )
        comps: np.ndarray = reg.coef_
        print(f" ----> TRAIN SCORE: MSE= {mse_train:.2f}")
        return comps, mse_train, estimator

    def plot_components(self, comps: np.ndarray, titles: List[str], **kwargs ):
        from geoproc.plot.bar import MultiBar
        highlights = kwargs.get( "highlight", None )
        colors = None
        if highlights is not None:
            colors_list = ['g'] * comps.shape[1]
            for iC in highlights: colors_list[iC] = 'r'
            colors = np.array(colors_list)
        normalize = kwargs.get("normalize", True )
        band_names = {ib: f"b{ib}" for ib in range(0, comps.shape[1], 10)}
        barplots = MultiBar("Band weighting", band_names)
        if normalize: comps = comps / np.abs(comps).max( axis=1, keepdims=True )
        for iC in range(comps.shape[0]):
            barplots.addPlot(titles[iC], comps[iC, :], colors )
        barplots.show()

    def pca(self, x_data_train: xa.DataArray, n_components: int ) -> Tuple[np.ndarray,np.ndarray,np.ndarray]:
        from sklearn.decomposition import PCA
        pca: PCA = PCA( n_components=n_components )
        np_reduced_data = pca.fit_transform( x_data_train )
        comps: np.ndarray = pca.components_
        evar: np.ndarray = pca.explained_variance_ratio_
        return ( np_reduced_data, comps, evar )

    def ica(self, x_data_train: xa.DataArray, n_components: int ) -> Tuple[np.ndarray,np.ndarray,np.ndarray]:
        from sklearn.decomposition import FastICA
        ica: FastICA = FastICA( n_components=n_components, random_state = 0, whiten = True )
        np_reduced_data = ica.fit_transform( x_data_train )
        comps: np.ndarray = ica.components_
        mixing: np.ndarray = ica.mixing_
        return ( np_reduced_data, comps, mixing )

if __name__ == '__main__':
    DATA_DIR = "/Users/tpmaxwel/Dropbox/Tom/Data/Aviris"
    outDir = "/Users/tpmaxwel/Dropbox/Tom/InnovationLab/results/Aviris"
    aviris_tile = "ang20170714t213741"
    n_input_bands = 106
    plot_pca = False
    plot_ica = True
    plot_regression = True
    n_components = 6
    n_bins = 16
    n_samples_per_bin = 10

    input_file = os.path.join( DATA_DIR, f"{aviris_tile}_rfl_v2p9", f"{aviris_tile}_corr_v2p9_img" )
    target_file = os.path.join(DATA_DIR, f"{aviris_tile}_Avg-Chl.tif")
    mgr = AvirisDataManager( n_input_bands )

    input_bands =  mgr.read( input_file )
    (norm_input_bands, scaling) = mgr.normalize( input_bands )

    nodata_val = int( input_bands.attrs['data_ignore_value'] )
    target_bands = mgr.read(target_file, nodata_val )
    (norm_target_bands, target_scaling) = mgr.normalize( target_bands )

    x_data_train, y_data_train = mgr.restructure_for_training( norm_input_bands, norm_target_bands )
    ( x_binned_training, y_binned_training ) = mgr.get_binned_sampling( x_data_train, y_data_train, n_bins, n_samples_per_bin )

    regress_components, mse = mgr.regress(x_binned_training, y_binned_training )
    regress_title = f"Ref, MSE={mse:.2f}"

    comps = regress_components.reshape(1,regress_components.size)
    for ib in range( comps.shape[1] ):
        print( f"{ib}: {comps[0,ib]:.2f}")
    mgr.plot_components( comps, [ regress_title ] )



