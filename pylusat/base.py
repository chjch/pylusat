from pyproj import Proj
from geopandas import GeoDataFrame


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
    def geom_unit_id(self):
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


def _pluralize(name):
    # convert unit name to its corresponding plural form
    if name.endswith("Inch"):
        return name.replace("Inch", "Inches")
    elif name.endswith("Foot"):
        return name.replace("Foot", "Feet")
    else:
        return name + "s"


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
                   "Mile": "mi",
                   "Foot": "ft",
                   "Yard": "yd",
                   "Inch": "in"}

    # normal unit names
    VALID_NAMES = {v[0]: k for k, v in UNIT_MAP.items()}

    def __init__(self, unit):
        unit_validation = UnitHandler.validate(unit)
        if unit_validation is None:
            raise ValueError("The unit provided is invalid or not supported.")
        else:
            self.unit_id = unit_validation

    @property
    def fullname(self):
        return self.UNIT_MAP[self.unit_id][0]

    @property
    def factor(self):
        return self.UNIT_MAP[self.unit_id][1]

    @property
    def plural(self):
        return _pluralize(self.fullname)

    @classmethod
    def _unit_name_map(cls):
        return {**cls.VALID_NAMES, **cls.OTHER_NAMES,
                **{_pluralize(k): v for k, v in cls.VALID_NAMES.items()},
                **{_pluralize(k): v for k, v in cls.OTHER_NAMES.items()}}

    @classmethod
    def validate(cls, unit):
        try:
            unit_lower = unit.lower()
            unit_title = unit.title()
            unit_name_map = cls._unit_name_map()
            if unit_lower in cls.UNIT_MAP.keys():
                return unit_lower
            elif unit_title in unit_name_map.keys():
                return unit_name_map[unit_title]
            else:
                return None
        except Exception as err:
            print(err)

    def convert(self, to_unit):
        to_unit = UnitHandler(to_unit)
        if to_unit.unit_id == "m":
            return self.factor
        else:
            return self.factor / to_unit.factor
