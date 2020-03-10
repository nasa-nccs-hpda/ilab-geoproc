import geopandas as gpd
import pandas as pd
from shapely.geometry import *
from typing import List, Union, Tuple, Dict, Optional
import xarray as xr
from glob import glob
import functools
from  xarray.core.groupby import DatasetGroupBy
from geoproc.util.configuration import sanitize, ConfigurableObject
from geoproc.surfaceMapping.util import TileLocator
import matplotlib.pyplot as plt
import numpy as np
import os, time, collections

class WaterMapGenerator(ConfigurableObject):

    def __init__( self, opspecs: Dict, **kwargs ):
        self._opspecs = { key.lower(): value for key,value in opspecs.items() }
        ConfigurableObject.__init__( self, **kwargs )
        self.water_maps: xr.DataArray = None
        self.water_probability: xr.DataArray = None
        self.persistent_classes: xr.DataArray = None
        self.yearly_lake_masks: xr.DataArray = None
        self.roi_bounds: gpd.GeoSeries = None
        self.mask_value = 5

    def get_water_map_colors(self) -> List[Tuple]:
        return [(0, 'nodata', (0, 0, 0)),
               (1, 'land', (0, 1, 0)),
               (2, 'water', (0, 0, 1)),
               (3, 'int-land', (0, 0.6, 0)),
               (4, 'int-water', (0, 0, 0.6)),
               (self.mask_value, 'mask', (1, 1, 0.7)) ]

    @classmethod
    def get_date_from_year(cls, year: int):
        from datetime import datetime
        return np.datetime64( datetime(year, 7, 1) )

    def get_viable_file(self, fpaths: List[str] ) -> str:
        for fpath in fpaths:
            if os.path.isfile(fpath):
                return fpath
        raise Exception( f"None of the tested file paths are viable: {fpaths}")

    def get_yearly_lake_area_masks( self, opspec: Dict, **kwargs) -> Optional[xr.DataArray]:
        from geoproc.xext.xrio import XRio
        t0 = time.time()
        images = {}
        data_dir = opspec.get('data_dir')
        wmask_opspec = opspec.get('water_masks')
        if wmask_opspec is None: return None
        lake_masks_dir: str = wmask_opspec.get('location', "" ).replace("{data_dir}",data_dir)
        lake_index = opspec.get('index')
        lake_id = opspec.get('id' )
        yearly_lake_masks_file = os.path.join(data_dir, f"Lake{lake_id}_fill_masks.nc")
        cache = kwargs.get('cache',"update")
        lake_mask_nodata = int( wmask_opspec.get('nodata', 256) )
        if cache==True and os.path.isfile( yearly_lake_masks_file ):
            yearly_lake_masks_dataset: xr.Dataset = xr.open_dataset(yearly_lake_masks_file)
            yearly_lake_masks: xr.DataArray = yearly_lake_masks_dataset.yearly_lake_masks
        else:
             for sdir in glob( f"{lake_masks_dir}/*" ):
                year = os.path.basename(sdir)
                filepaths = [ f"{lake_masks_dir}/{year}/{prefix}{lake_index}_{year}.tif" for prefix in ["lake", ""] ]
                images[int(year)] = self.get_viable_file( filepaths )
             sorted_file_paths = collections.OrderedDict(sorted(images.items()))
             time_values = np.array([self.get_date_from_year(year) for year in sorted_file_paths.keys()], dtype='datetime64[ns]')
             yearly_lake_masks: xr.DataArray = XRio.load(list(sorted_file_paths.values()), band=0, mask_value=lake_mask_nodata, index=time_values)
             yearly_lake_masks = yearly_lake_masks.where( yearly_lake_masks != lake_mask_nodata, self.mask_value )

        if cache in [ True, "update" ]:
            result = xr.Dataset(dict(yearly_lake_masks=sanitize(yearly_lake_masks)))
            result.to_netcdf(yearly_lake_masks_file)
            print(f"Saved cropped_data to {yearly_lake_masks_file}")

        yearly_lake_masks = yearly_lake_masks.persist()
        print(f"Done yearly_lake_masks in time {time.time() - t0} secs")
        return yearly_lake_masks

    def get_persistent_classes(self, opspec: Dict, **kwargs) -> xr.DataArray:
        print(f"Executing get_persistent_classes")
        t0 = time.time()
        thresholds = opspec.get('water_class_thresholds', [ 0.05, 0.95 ] )
        perm_water_mask: xr.DataArray = self.water_probability > thresholds[1]
        boundaries_mask: xr.DataArray = self.water_probability > 1.0
        if self.yearly_lake_masks is None:
            perm_land_mask = self.water_probability < thresholds[0]
            result = xr.where(boundaries_mask, self.mask_value,
                            xr.where(perm_water_mask, 2,
                                     xr.where(perm_land_mask, 1, 0)))
        else:
            yearly_lake_masks = self.yearly_lake_masks.interp_like(self.water_probability, method='nearest')
            perm_land_mask: xr.DataArray = (yearly_lake_masks == 0)
            roi_mask: xr.DataArray = np.logical_or( ( yearly_lake_masks == self.mask_value ), boundaries_mask )
            result = xr.where( roi_mask, self.mask_value,
                                  xr.where(perm_water_mask, 2,
                                     xr.where(perm_land_mask, 1, 0)))
        result = result.persist()
        result.name = "Persistent_Classes"
        print(f"Done get_persistent_classes in time {time.time() - t0}")
        return result.assign_attrs( cmap = dict( colors=self.get_water_map_colors() ) )

    def get_water_probability( self, opspec: Dict, **kwargs ) -> xr.DataArray:
        from datetime import datetime
        print(f"Executing get_water_probability" )
        t0 = time.time()
        cache = kwargs.get( "cache", "update" )
        yearly = 'water_masks' in opspec
        data_dir = opspec.get('data_dir')
        lake_id = opspec['id']
        water_probability_file = os.path.join(data_dir, f"{lake_id}_water_probability.nc")

        if cache==True and os.path.isfile( water_probability_file ):
            water_probability_dataset: xr.Dataset = xr.open_dataset(water_probability_file)
            water_probability: xr.DataArray = water_probability_dataset.water_probability
        else:
            water = self.water_maps.isin([2, 3])
            land = self.water_maps.isin([1])
            unmasked = (self.water_maps[0] != self.mask_value).drop_vars(self.water_maps.dims[0])

            if yearly:
                water_cnts = water.groupby("time.year").sum()
                land_cnts  = land.groupby("time.year").sum()
            else:
                water_cnts = water.sum(axis=0)
                land_cnts = land.sum(axis=0)
            visible_cnts = (water_cnts + land_cnts)
            water_probability: xr.DataArray = water_cnts / visible_cnts
            water_probability = water_probability.where( unmasked, 1.01 )
            water_probability.name = "water_probability"
            if yearly:
                time_values = np.array( [ np.datetime64( datetime( year, 7, 1 ) ) for year in water_probability.year.data ], dtype='datetime64[ns]' )
                water_probability = water_probability.assign_coords( year=time_values ).rename( year='time' )
            if cache in [True,"update"]:
                result = xr.Dataset(dict(water_probability=sanitize(water_probability)))
                result.to_netcdf(water_probability_file)
                print(f"Saved water_probability to {water_probability_file}")
        water_probability = water_probability.persist()
        print(f"Done get_water_probability in time {time.time() - t0}")
        return water_probability

    def get_water_map(self,  opspec: Dict, inputs: xr.DataArray )-> xr.Dataset:
        da: xr.DataArray = self.time_merge(inputs) if isinstance(inputs, list) else inputs
        threshold = opspec.get('threshold', 0.5 )
        binSize = da.shape[0]
        masked = da[0].isin( [ self.mask_value ] ).drop_vars( inputs.dims[0] )
        land = da.isin( [1] ).sum( axis=0 )
        water =  da.isin( [2,3] ).sum( axis=0 )
        visible = ( water + land )
        reliability = visible / float(binSize)
        prob_h20 = water / visible
        water_mask = prob_h20 >= threshold
        result =  xr.where( masked, self.mask_value, xr.where( water_mask, 2, xr.where( land, 1, 0 ) ) )
        return xr.Dataset( { "water_maps": result,  "reliability": reliability } )

    def get_water_maps( self, data_array: Optional[xr.DataArray], opspec: Dict, **kwargs ) -> xr.DataArray:
        print("\n Executing get_water_maps ")
        t0 = time.time()
        data_dir = opspec.get('data_dir')
        lake_id = opspec['id']
        water_maps_file = os.path.join(data_dir, f"{lake_id}_water_maps.nc")
        cache = kwargs.get( "cache", "update" )
        if cache==True and os.path.isfile( water_maps_file ):
            water_maps_dset: xr.Dataset = xr.open_dataset(water_maps_file)
        else:
            water_maps_opspec = opspec.get('water_maps',{})
            binSize = water_maps_opspec.get( 'bin_size', 8 )
            bin_indices = list(range( 0, data_array.shape[0], binSize ))
            centroid_indices = list(range(binSize//2, bin_indices[-1], binSize))
            time_axis = data_array.coords[ data_array.dims[0] ].values
            time_bins = np.array( [ time_axis[iT] for iT in bin_indices ], dtype='datetime64[ns]' )
            grouped_data: DatasetGroupBy = data_array.groupby_bins( 'time', time_bins, right = False )
            get_water_map_partial = functools.partial( self.get_water_map, water_maps_opspec )
            water_maps_dset:  xr.Dataset = grouped_data.map( get_water_map_partial )
            water_maps_dset = water_maps_dset.assign( time_bins = [ time_axis[i] for i in centroid_indices ]  ).rename( time_bins='time' ).persist()
            if cache in [True,"update"]:
                water_maps_dset.to_netcdf(water_maps_file)
                print(f"Cached water_maps to {water_maps_file}")
        print( f" Completed get_water_maps in {time.time()-t0:.3f} seconds" )
        water_maps_array: xr.DataArray = water_maps_dset.water_maps
        water_maps_array.name = "Water_Maps"
        return water_maps_array.assign_attrs( cmap = dict( colors=self.get_water_map_colors() ) )

    def update_metrics( self, data_array: xr.DataArray, **kwargs ):
        metrics = data_array.attrs.get('metrics', {} )
        metrics.update( **kwargs )
        data_array.attrs['metrics'] = metrics

    def interpolate(self ) -> xr.DataArray:
        spatially_patched_water_maps: xr.DataArray = self.spatial_interpolate( )
        result = self.temporal_interpolate( spatially_patched_water_maps )
        patched_result: xr.DataArray = result.where( result == self.water_maps, result + 2 )
        return patched_result

    # def spatial_interpolate_slow(self, dynamics_class: int = 0) -> xr.DataArray:
    #     print("Spatial Interpolate")
    #     t0 = time.time()
    #     tdim = self.persistent_classes.dims[0]
    #     persistent_classes: xr.DataArray = self.persistent_classes.interp_like(self.water_maps).ffill(tdim).bfill(tdim).persist()
    #     #       persistent_classes: xr.DataArray = self.persistent_classes.interp_like(self.water_maps[0], method='nearest').persist()
    #     t1 = time.time()
    #     dynamics_mask: xr.DataArray = persistent_classes.isin([dynamics_class])
    #     result: xr.DataArray = xr.where(dynamics_mask, self.water_maps, persistent_classes)
    #     patched_result: xr.DataArray = result.where(result == self.water_maps, persistent_classes + 2).persist()
    #     print(f"Done spatial interpolate in time {time.time() - t0}, interp: {t1 - t0}")
    #     return patched_result

    def spatial_interpolate( self, **kwargs  ) -> xr.DataArray:
        print("Spatial Interpolate")
        t0 = time.time()
        interp_persistent_classes: xr.DataArray = self.persistent_classes.interp_like(self.water_maps[0], method='nearest')
        spatial_interpolate_partial = functools.partial(self.spatial_interpolate_slice, interp_persistent_classes )
        result: xr.DataArray = self.water_maps.groupby( "time.year" ).map( spatial_interpolate_partial, **kwargs ).persist()
        print(f"Done spatial interpolate in time {time.time() - t0}")
        return result

    def spatial_interpolate_slice(self, persistent_classes: xr.DataArray, water_maps_slice: xr.DataArray, **kwargs ) -> xr.DataArray:
        dynamics_class = kwargs.get( "dynamics_class", 0 )
        tval = water_maps_slice.coords[ water_maps_slice.dims[0] ].values[0]
        persistent_classes_slice = persistent_classes if persistent_classes.ndim == 2 \
            else persistent_classes.sel( **{persistent_classes.dims[0]:tval}, method="nearest" ).drop_vars( persistent_classes.dims[0] )
        dynamics_mask: xr.DataArray = persistent_classes_slice.isin( [dynamics_class] )
        return water_maps_slice.where( dynamics_mask, persistent_classes_slice  )

    def show(self, data: xr.DataArray, name: str ):
        data.name = name
        if len(data.dims) == 2:
            data.name = name
            data.plot.imshow(cmap=data.attrs.get("cmap","jet"))
            plt.show()
        elif len(data.dims) == 3:
            animation = SliceAnimation(data)
            animation.show()
        else:
            print( f"Error, can't show '{name}' data with {len(data.dims)} dimensions")

    def temporal_interpolate( self, water_maps: xr.DataArray  ) -> xr.DataArray:
        print( "Temporal Interpolate")
        t0 = time.time()
        nodata_mask = water_maps == 0
        water_maps = xr.where( nodata_mask, np.nan, water_maps )
        result = water_maps.ffill( water_maps.dims[0] ).bfill( water_maps.dims[0] )
        print(f"Done interpolate in time {time.time() - t0}")
        return result

    def time_merge( cls, data_arrays: List[xr.DataArray], **kwargs ) -> xr.DataArray:
        time_axis = kwargs.get('time',None)
        frame_indices = range( len(data_arrays) )
        merge_coord = pd.Index( frame_indices, name=kwargs.get("dim","time") ) if time_axis is None else time_axis
        result: xr.DataArray =  xr.concat( data_arrays, dim=merge_coord )
        return result

    def get_date_from_filename(self, filename: str):
        from datetime import datetime
        toks = filename.split("_")
        result = datetime.strptime(toks[1], '%Y%j').date()
        return np.datetime64(result)

    def infer_tile_location(self) -> str:
        if self.yearly_lake_masks is not None:
            return TileLocator.infer_tile_xa( self.yearly_lake_masks )
        if self.roi_bounds is not None:
            if isinstance( self.roi_bounds, list ):
                return TileLocator.get_tile( *self.roi_bounds )
            else:
                return TileLocator.infer_tile_gpd( self.roi_bounds )
        raise Exception( "Must supply either source.location, roi, or lake masks in order to locate region")

    def get_mpw_data(self, opspec: Dict, **kwargs) -> xr.DataArray:
        print( "reading mpw data")
        t0 = time.time()
        data_dir = opspec.get('data_dir')
        lake_id = opspec['id']
        cropped_data_file = os.path.join(data_dir, f"{lake_id}_cropped_data.nc")
        cache = kwargs.get("cache", True)
        download = kwargs.get('download', cache)
        if cache==True and os.path.isfile( cropped_data_file ):
            cropped_data_dataset: xr.Dataset = xr.open_dataset(cropped_data_file)
            cropped_data: xr.DataArray = cropped_data_dataset.cropped_data
        else:
            from geoproc.data.mwp import MWPDataManager
            from geoproc.xext.xrio import XRio
            source_spec = opspec.get('source')
            data_url = source_spec.get('url')
            product = source_spec.get('product')
            location = source_spec.get( 'location', self.infer_tile_location() )

            year_range = opspec.get('year_range')
            day_range = opspec.get('day_range',[0,365])
            dataMgr = MWPDataManager(data_dir, data_url)

            dataMgr.setDefaults(product=product, download=download, years=range(int(year_range[0]),int(year_range[1])), start_day=int(day_range[0]), end_day=int(day_range[1]))
            file_paths = dataMgr.get_tile(location)
            time_values = np.array([ self.get_date_from_filename(os.path.basename(path)) for path in file_paths], dtype='datetime64[ns]')
            cropped_data: xr.DataArray = XRio.load(file_paths, mask=self.roi_bounds, band=0, mask_value=self.mask_value, index=time_values)
            if cache in [True,"update"]:
                cropped_data_dset = xr.Dataset(dict(cropped_data=sanitize(cropped_data)))
                cropped_data_dset.to_netcdf(cropped_data_file)
                print(f"Cached cropped_data to {cropped_data_file}")

        cropped_data.attrs.update( roi = self.roi_bounds )
        cropped_data = cropped_data.persist()
        print(f"Done reading mpw data in time {time.time()-t0}")
        return cropped_data

    def get_opspec(self, lakeId: str ) -> Dict:
        opspec = self._opspecs.get( lakeId.lower() )
        assert opspec is not None, f"Can't find {lakeId.lower()} in opspecs, available opspecs: {self._opspecs.keys()}"
        merged_opspec: Dict = dict( **self._opspecs.get("defaults",{}) )
        for key,value in opspec.items():
            if key in merged_opspec:    merged_opspec[key] = self.merge_opspec_values( merged_opspec[key], value )
            else:                       merged_opspec[key] = value
        merged_opspec['id'] = lakeId
        return merged_opspec

    def merge_opspec_values( self, value0, value1 ):
        if isinstance( value0, collections.Mapping ):
            return { **value0, **value1 }
        else: return value1

    def get_roi_bounds(self, opspec: Dict ):
        data_dir = opspec.get('data_dir')
        roi = opspec.get('roi', None)
        if roi is not None:
            if isinstance(roi, list):
                self.roi_bounds = [ float(x) for x in roi ]
            elif isinstance(roi, str) and "," in roi:
                self.roi_bounds = [ float(x) for x in roi.split(",") ]
            elif isinstance(roi, str):
                self.roi_bounds: gpd.GeoSeries = gpd.read_file( roi.replace("{data_dir}", data_dir) )
            else:
                raise Exception( f" Unrecognized roi: {roi}")
        else:
            assert self.yearly_lake_masks is not None, "Must specify roi to locate lake"
            self.roi_bounds =  TileLocator.get_bounds( self.yearly_lake_masks[0] )

    def get_patched_water_maps(self, lakeId: str, **kwargs) -> xr.DataArray:
        t0 = time.time()
        opspec = self.get_opspec( lakeId.lower() )
        data_dir = opspec.get('data_dir')
        lake_id = opspec['id']
        patched_water_maps_file = f"{data_dir}/{lake_id}_patched_water_masks.nc"
        cache = kwargs.get("cache", "update" )

        if cache==True and os.path.isfile(patched_water_maps_file):
            patched_water_maps: xr.DataArray = xr.open_dataset(patched_water_maps_file).Water_Maps
            patched_water_maps.attrs['cmap'] = dict(colors=self.get_water_map_colors())
        else:
            self.yearly_lake_masks: xr.DataArray = self.get_yearly_lake_area_masks(opspec, **kwargs)
            self.get_roi_bounds( opspec )
            water_mapping_data = self.get_mpw_data( opspec, cache="update" )
            self.water_maps: xr.DataArray =  self.get_water_maps( water_mapping_data, opspec )
            patched_water_maps = self.patch_water_maps( opspec, **kwargs )

        if ((cache == True) and not os.path.isfile(patched_water_maps_file)) or ( cache == "update" ):
            sanitize(patched_water_maps).to_netcdf( patched_water_maps_file )
            print( f"Saving patched_water_maps to {patched_water_maps_file}")

        print(f"Completed get_patched_water_maps in time {(time.time() - t0)/60.0} minutes")
        patched_water_maps.name = "Patched_Water_Maps"
        return patched_water_maps.assign_attrs( roi = self.roi_bounds )

    def write_patched_water_maps(self, lakeId: str, outfile_path: str, **kwargs ):
        from geoproc.xext.xgeo import XGeo
        interp_water_class = kwargs.get( 'interp_water_class', 4 )
        water_classes = kwargs.get('water_classes', [2,4] )
        patched_water_maps: xr.DataArray = self.get_patched_water_maps( lakeId, **kwargs )
        time_axis = patched_water_maps.coords[ patched_water_maps.dims[0] ]
        utm_patched_water_maps: xr.DataArray = patched_water_maps.xgeo.to_utm( [250.0, 250.0] )
        water_counts, class_proportion = self.get_class_proportion(patched_water_maps, interp_water_class, water_classes)
        with open( outfile_path, "a" ) as outfile:
            lines = ["date water_area_km2 percent_interploated\n"]
            for iTime in range( utm_patched_water_maps.shape[0] ):
                percent_interp = class_proportion.values[iTime]
                num_water_pixels = water_counts.values[iTime]
                date = pd.Timestamp( time_axis.values[iTime] ).to_pydatetime()
                lines.append( f"{str(date).split(' ')[0]} {num_water_pixels/16.0:.2f} {percent_interp:.1f}\n")
            outfile.writelines(lines)
            print( f"Wrote results to file {outfile_path}")

    def repatch_water_maps(self, lakeId: str, **kwargs) -> xr.DataArray:
        t0 = time.time()
        opspec = self.get_opspec( lakeId.lower() )
        data_dir = opspec.get('data_dir')
        lake_id = opspec['id']
        patched_water_maps_file = f"{data_dir}/{lake_id}_patched_water_masks.nc"
        cache = kwargs.get("cache", "update" )

        self.yearly_lake_masks: xr.DataArray = self.get_yearly_lake_area_masks(opspec, **kwargs)
        self.get_roi_bounds( opspec )
        self.water_maps: xr.DataArray =  self.get_water_maps( None, opspec, cache=True )
        patched_water_maps = self.patch_water_maps( opspec, **kwargs )

        if ((cache == True) and not os.path.isfile(patched_water_maps_file)) or ( cache == "update" ):
            sanitize(patched_water_maps).to_netcdf( patched_water_maps_file )
            print( f"Saving patched_water_maps to {patched_water_maps_file}")

        print(f"Completed get_patched_water_maps in time {(time.time() - t0)/60.0} minutes")
        patched_water_maps.name = "Patched_Water_Maps"
        return patched_water_maps.assign_attrs( roi = self.roi_bounds )

    def patch_water_maps( self, opspec: Dict, **kwargs ) -> xr.DataArray:
        self.water_probability:  xr.DataArray = self.get_water_probability( opspec, **kwargs )
        self.persistent_classes: xr.DataArray = self.get_persistent_classes( opspec, **kwargs )
        patched_water_maps: xr.DataArray = self.interpolate().assign_attrs( **self.water_maps.attrs )
        patched_water_maps.attrs['cmap'] = dict( colors=self.get_water_map_colors() )
        return patched_water_maps.fillna( self.mask_value )

    def get_cached_water_maps( self, lakeId: str ):
        opspec = self.get_opspec(lakeId.lower())
        self.water_maps: xr.DataArray = self.get_water_maps( None, opspec, cache=True )
        return self.water_maps

    def get_class_proportion(self, class_map: xr.DataArray, target_class: int, relevant_classes: List[int] ) -> Tuple[xr.DataArray,xr.DataArray]:
        sdims = [ class_map.dims[-1], class_map.dims[-2] ]
        total_relevant_population = class_map.isin( relevant_classes ).sum( dim=sdims )
        class_population = (class_map == target_class).sum( dim=sdims )
        return ( total_relevant_population,  ( class_population / total_relevant_population ) * 100 )

    def view_water_map_results(self, lake_id: str, **kwargs ):
        from geoproc.plot.animation import SliceAnimation
        interp_water_class = kwargs.get( 'interp_water_class', 4 )
        water_classes = kwargs.get('water_classes', [2,4] )
        water_maps =  self.get_cached_water_maps(  lake_id )
        patched_water_maps = self.get_patched_water_maps( lake_id, cache=True )
        water_counts, class_proportion = self.get_class_proportion( patched_water_maps, interp_water_class, water_classes )
        animation = SliceAnimation( patched_water_maps, metrics=dict(blue=class_proportion), auxplot=water_maps )
        animation.show()

if __name__ == '__main__':
    from geoproc.plot.animation import SliceAnimation
    import yaml
    CURDIR = os.path.dirname(os.path.abspath(__file__))
    opspec_file = os.path.join( CURDIR, "specs", "lakes1.yml")
    with open(opspec_file) as f:
        opspecs = yaml.load( f, Loader=yaml.FullLoader )
        waterMapGenerator = WaterMapGenerator( opspecs )
        patched_water_maps = waterMapGenerator.get_patched_water_maps( "Lake334" )
        roi = patched_water_maps.attrs.get("roi")
        kwargs = dict( overlays=dict(red=roi.boundary) ) if ( roi and not isinstance(roi,list) ) else {}

        animation = SliceAnimation( [ waterMapGenerator.water_maps, patched_water_maps, waterMapGenerator.persistent_classes ], **kwargs )
        animation.show()