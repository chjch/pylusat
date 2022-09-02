from pyproj import Proj
from geopandas import GeoDataFrame
import numpy as np
import rasterio as rio
from rasterio.vrt import WarpedVRT
from rasterio import DatasetReader
from rasterio.io import MemoryFile
from rasterio.enums import Resampling
from shapely.geometry import box
from shapely.ops import unary_union
from affine import Affine


class GeoDataFrameManager:

    def __init__(self, gdf_obj):
        assert type(gdf_obj) == GeoDataFrame, ("Your input is not a valid "
                                               "GeoDataFrame.")
        self.gdf = gdf_obj

    def geom_type_validate(self, validate_type):
        type_sr = self.gdf.geom_type
        validation_map = {
            "Point": type_sr.isin(["Point", "MultiPoint"]).all(),
            "Line": type_sr.isin(["LineString", "MultiLineString"]).all(),
            "Polygon": type_sr.isin(["Polygon", "MultiPolygon"]).all()
        }
        return validation_map[validate_type]

    @property
    def geom_unit_id(self) -> str:
        proj_str = Proj(self.gdf.crs).definition_string()
        return [_[_.find("=") + 1:] for _ in proj_str.split()
                if _.startswith("units=")][0]

    @property
    def geom_unit_name(self):
        return UnitHandler(self.geom_unit_id).fullname

    @classmethod
    def from_shp(cls, shp_path):
        assert shp_path.endswith(".shp"), "Not a valid shapefile."
        try:
            return cls(GeoDataFrame.from_file(shp_path))
        except Exception as err:
            print(err)


class UnitHandler:

    UNIT_MAP = {'km': ('Kilometer', 1000.0),
                'm': ('Meter', 1.0),
                'dm': ('Decimeter', 0.1),
                'cm': ('Centimeter', 0.01),
                'mm': ('Millimeter', 0.001),
                'kmi': ('International Nautical Mile', 1852.0),
                'in': ('International Inch', 0.0254),
                'ft': ('International Foot', 0.3048),
                'yd': ('International Yard', 0.9144),
                'mi': ('International Statute Mile', 1609.344),
                'fath': ('International Fathom', 1.8288),
                'ch': ('International Chain', 20.1168),
                'link': ('International Link', 0.201168),
                'us-in': ("U.S. Surveyor's Inch", 0.0254000508001016),
                'us-ft': ("U.S. Surveyor's Foot", 0.3048006096012192),
                'us-yd': ("U.S. Surveyor's Yard", 0.9144018288036576),
                'us-ch': ("U.S. Surveyor's Chain", 20.116840233680467),
                'us-mi': ("U.S. Surveyor's Statute Mile", 1609.3472186944373),
                'ind-yd': ('Indian Yard', 0.91439523),
                'ind-ft': ('Indian Foot', 0.30479841),
                'ind-ch': ('Indian Chain', 20.11669506)}

    # alternative unit names
    OTHER_NAMES = {"Metre": "m",
                   "Mile": "us-mi",
                   "Foot": "us-ft",
                   "Yard": "us-yd",
                   "Inch": "us-in"}

    # normal unit names
    VALID_NAMES = {v[0]: k for k, v in UNIT_MAP.items()}

    # additional area names supported
    AREA_NAMES = {'Acre': 'ac',
                  'Hectare': 'ha'}

    def __init__(self, unit):
        validate_1d = self._validate_1d(unit)
        if validate_1d:
            self.unit_id = validate_1d
            self.dimension = 1
            return
        validate_2d = self._validate_2d(unit)
        if validate_2d:
            self.unit_id = validate_2d
            self.dimension = 2
            return
        else:
            raise ValueError(f'{unit} is not a valid unit.')

    @property
    def fullname(self):
        if self.dimension == 1:
            return self.UNIT_MAP[self.unit_id][0]
        else:  # dimension=2
            if self.unit_id == 'ac':
                return 'Acre'
            elif self.unit_id == 'ha':
                return 'Hectare'
            else:
                return f'Square {self.UNIT_MAP[self.unit_id][0]}'

    @staticmethod
    def _pluralize(name):
        # convert unit name to its corresponding plural form
        if name.endswith("Inch"):
            return name.replace("Inch", "Inches")
        elif name.endswith("Foot"):
            return name.replace("Foot", "Feet")
        else:
            return name + "s"

    @property
    def plural(self):
        return self._pluralize(self.fullname)

    @property
    def base_factor(self):
        """conversion factor compare to meter or square meter."""
        if self.dimension == 1:
            return self.UNIT_MAP[self.unit_id][1]
        else:  # dimension=2
            if self.unit_id == 'ac':
                return self.UNIT_MAP['us-ft'][1]**2 * 43560
            elif self.unit_id == 'ha':
                return 10000
            else:
                return self.UNIT_MAP[self.unit_id][1]**2

    def _unit_name_map(self):
        return {**self.VALID_NAMES, **self.OTHER_NAMES,
                **{self._pluralize(k): v for k, v in self.VALID_NAMES.items()},
                **{self._pluralize(k): v for k, v in self.OTHER_NAMES.items()}}

    def _validate_1d(self, unit):
        try:
            unit_lower = unit.lower()
            unit_title = unit.title()
            unit_name_map = self._unit_name_map()
            if unit_lower in self.UNIT_MAP.keys():
                return unit_lower
            elif unit_title in unit_name_map.keys():
                return unit_name_map[unit_title]
            else:
                return None
        except Exception as err:
            print(err)

    def _validate_2d(self, unit):
        try:
            sq, unit_name = unit.split()
            if sq.lower() in ['square', 'sq'] and self._validate_1d(unit_name):
                return self._validate_1d(unit_name)
            else:
                raise ValueError('Not a valid area unit.')
        except ValueError:
            if unit.title() in self.AREA_NAMES.keys():
                return self.AREA_NAMES[unit.title()]
            elif unit[:-1].title() in self.AREA_NAMES.keys():
                return self.AREA_NAMES[unit[:-1].title()]
            else:
                raise ValueError('Not a valid area unit.')

    def convert(self, other_unit):
        other_unit_handler = UnitHandler(other_unit)
        if self.dimension != other_unit_handler.dimension:
            raise TypeError(f'Incompatible units, from {self.fullname} to '
                            f'{other_unit_handler.fullname}.')
        else:
            return self.base_factor / other_unit_handler.base_factor


class RasterManager:

    def __init__(self, rio_dataset: DatasetReader, nodata=None):
        self.rast_ds = rio_dataset
        self.rast_nodata = nodata
        self.dtype = self.rast_ds.dtypes[0]

    @property
    def rast_ds(self):
        return self._rast_ds

    @rast_ds.setter
    def rast_ds(self, rast_obj):
        if type(rast_obj) not in [DatasetReader, WarpedVRT]:
            raise TypeError("Not a valid rasterio dataset.")
        self._rast_ds = rast_obj

    def get_rio_crs(self):
        # get rasterio.crs from the raster dataset
        return self.rast_ds.crs

    def to_array(self):
        # return a numpy.ndarray
        return self.rast_ds.read(1)

    def get_affine(self):
        return self.rast_ds.transform

    def as_rebuild_info(self):
        rast_band = self.to_array()
        rast_affine = self.rast_ds.transform
        if self.rast_nodata is not None:
            rast_band[
                np.where(rast_band == self.rast_ds.nodata)
            ] = self.rast_nodata
            nodata = self.rast_nodata
        else:
            nodata = self.rast_ds.nodata
        cellsize = rast_affine[0]
        min_x = rast_affine[2]
        max_y = rast_affine[5]
        return rast_band, cellsize, max_y, min_x, nodata

    @property
    def wkt(self):
        return self.rast_ds.crs.to_wkt()

    def reproject_vrt(self, crs=None):
        return WarpedVRT(self.rast_ds, crs=crs)

    @classmethod
    def from_path(cls, rast_path, nodata=None):
        try:
            return cls(rio.open(rast_path), nodata)
        except rio.errors.RasterioIOError:
            raise ValueError("Not a valid raster data.") from None

    def rescale(self, cell_size):
        rast_affine = self.get_affine()
        if round(rast_affine[0]) == cell_size:
            return self.rast_ds
        else:
            scale_factor = abs(round(rast_affine[0]) / cell_size)
            # rescaling raster
            with self.rast_ds as dataset:
                data = dataset.read(
                    out_shape=(
                        dataset.count,
                        int(dataset.height * scale_factor),
                        int(dataset.width * scale_factor)
                    ),
                    resampling=Resampling.nearest
                )
                # scale image transform
                transform = dataset.transform * dataset.transform.scale(
                    (dataset.width / data.shape[-1]),
                    (dataset.height / data.shape[-2])
                )
                profile = self.rast_ds.profile
                profile.update(transform=transform,
                               height=int(dataset.height * scale_factor),
                               width=int(dataset.width * scale_factor)
                               )
                with MemoryFile() as memfile:
                    rst = memfile.open(**profile)
                    rst.write(data)
                    rst.close()
                    return memfile.open(driver='GTiff')

    def match_extent(self, matching_rast_obj):
        out_x_res = round(matching_rast_obj.get_affine()[0], 1)
        out_y_res = round(-matching_rast_obj.get_affine()[4], 1)
        b1 = box(*self.rast_ds.bounds)
        b2 = box(*matching_rast_obj.rast_ds.bounds)
        b_union = unary_union((b1, b2))
        out_bnd = b_union.envelope
        left, bottom, right, top = out_bnd.bounds
        out_width = round((right - left) / out_x_res)
        out_height = round((top - bottom) / out_y_res)
        out_transform = Affine(out_x_res, 0, left, 0, -out_y_res, top)
        out_crs = matching_rast_obj.get_rio_crs()
        out_nodata = self.rast_nodata

        vrt_options = {
            'resampling': Resampling.nearest,
            'crs': out_crs,
            'transform': out_transform,
            'height': out_height,
            'width': out_width,
            'nodata': out_nodata
        }
        out_vrt = WarpedVRT(self.rast_ds, **vrt_options)

        with MemoryFile() as memfile:
            rst = memfile.open(driver='GTiff', count=1,
                               dtype=self.dtype, **vrt_options)
            rst.write(out_vrt.read(1), indexes=1)
            rst.close()
            return memfile.open(driver="GTiff")
