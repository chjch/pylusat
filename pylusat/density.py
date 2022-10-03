import pandas as pd
import numpy as np
import geopandas as gpd
from geopandas import GeoDataFrame
from pylusat.base import GeoDataFrameManager, UnitHandler


def _buffer(input_gdf, buffer_dist):
    """create buffers around the input_gdf using specified buffer distance"""

    input_unit = GeoDataFrameManager(input_gdf).geom_unit_id
    buff_length, buff_unit = buffer_dist.split()
    # calculate the length of buffer in the unit used by input_gdf
    buff_factor = float(buff_length)/UnitHandler(input_unit).convert(buff_unit)
    return input_gdf.buffer(buff_factor)


def _buffer_factor(input_gdf, buffer_dist):
    """create buffers around the input_gdf using specified buffer distance"""

    input_unit = GeoDataFrameManager(input_gdf).geom_unit_id
    buff_length, buff_unit = buffer_dist.split()
    # calculate the length of buffer in the unit used by input_gdf
    buff_factor = float(buff_length)/UnitHandler(input_unit).convert(buff_unit)
    return buff_factor


def of_point(input_gdf, point_gdf, pop_clm=None,
             search_radius=None, area_unit='square meters'):
    """
    Calculate density of points in each input geometry.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame in which points are counted.
    point_gdf : GeoDataFrame
        Point GeoDataFrame.
    pop_clm : str
        Population column which contains values to represent each occurrence
        of the point feature.
    search_radius : str, optional
        A string of buffering distance and unit, separated by space.
        e.g., "1 mile".
    area_unit : str, optional
        A string of the area unit used for density calculation.
        e.g., "square meters".

    Returns
    -------
    output_sr : pd.Series
        A pandas Series that contains the density of point in each input
        geometry of the input GeoDataFrame.

    Examples
    --------
    Calculate density of points (schools) in polygon layer (Alachua County 
    census tracts) in square miles.

    >>> pylusat.density.of_point(acs2016_gdf, schools_gdf, 
                                 area_unit='square mile')
    0   2.389447
    1   0.000000
    2   1.714565
    3   4.974934
    4   2.494981
    ...
    150 0.6607739
    151 3.332871
    152 0.967817
    153 0.116269
    154 1.140540

    Calculate density of points (schools) in polygon layer (Alachua County 
    census tracts) in square miles. Each occurrence of schools is represented 
    by the enrollment column.

    >>> pylusat.density.of_point(acs2016_gdf, schools_gdf, "ENROLLMENT", 
                                 '1 mile', 'square mile')
    0   0.000159
    1   0.000252
    2   0.000132
    3   0.000117
    4   0.000099
    ...
    150 0.000084
    151 0.000114
    152 0.000085
    153 0.000031
    154 0.000024
    """
    input_gdf_manager = GeoDataFrameManager(input_gdf)
    point_gdf_manager = GeoDataFrameManager(point_gdf)
    assert point_gdf_manager.geom_type_validate("Point"), (
        "The geometry of point GeoDataFrame must be Point."
    )

    if not search_radius:
        assert input_gdf_manager.geom_type_validate("Polygon"), (
            "The geometry of input GeoDataFrame must be Polygon "
            "if `search_radius` is None."
        )
        search_unit = input_gdf_manager.geom_unit_id
        input_copy = input_gdf
    else:
        input_copy = input_gdf.copy()
        input_copy.geometry = _buffer(input_copy, search_radius)
        search_unit = search_radius.split()[1]

    joint_gdf = gpd.sjoin(input_copy, point_gdf, how='left', op='intersects')
    by_input_index = joint_gdf.groupby(level=0)
    if pop_clm is None:
        output_sr = by_input_index["index_right"].count()
    else:
        output_sr = by_input_index[pop_clm].sum()
    output_sr.fillna(0)
    output_sr.index = input_gdf.index

    search_area = input_copy.area
    # convert search area to specified areal unit
    search_area *= UnitHandler(f'square {search_unit}').convert(area_unit)

    output_sr = output_sr / search_area
    return output_sr


def of_line(input_gdf, line_gdf, cellsize=30, search_radius=None,
            area_unit="square meters", geomtoarray=None):
    """
    Calculate density of line length in each input geometry.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame in which length of lines are summed.
    line_gdf : GeoDataFrame
        Line GeoDataFrame whose lengths are summed.
    cellsize : float, optional
        The cell size used to rasterize the line_gdf.
    search_radius : str, optional
        A string of buffering distance and unit, separated by space.
        e.g., "1 mile".
    area_unit : str, optional
        A string of the area unit used for density calculation.
        e.g., "square meters".
    geomtoarray : {tuple of (np.ndarray, Affine, np.ndarray, float), None}
        The output of ``rasterize_geometry`` function. If a desired output has
        already been created for the `line_gdf` has already been created,
        set it to be this argument to use it.

    Returns
    -------
    output_sr : pd.Series
        A pandas Series that contains the density of line in each input
        geometry of the input GeoDataFrame.

    Examples
    --------
    Calculate density of lines (highway) per square mile in Alachua County 
    census tract polygons.

    >>> pylusat.density.of_line(acs2016_gdf, highway_gdf, 
                                search_radius='1 mile', area_unit='square mile')
    0   0.000425
    1   0.000705
    2   0.000273
    3   0.000753
    4   0.000358
    ...
    150 0.000266
    151 NaN
    152 0.000277
    153 NaN
    154 0.000620    
    """
    from pylusat.utils import rasterize_geometry
    from rasterstats import zonal_stats
    import warnings

    input_gdf_manager = GeoDataFrameManager(input_gdf)
    line_gdf_manager = GeoDataFrameManager(line_gdf)
    assert line_gdf_manager.geom_type_validate("Line"), (
        "The geometry of line GeoDataFrame must be Line."
    )

    line_data = rasterize_geometry(line_gdf, cellsize) if geomtoarray is None \
        else geomtoarray

    if not search_radius:
        assert input_gdf_manager.geom_type_validate("Polygon"), (
            "The geometry of input GeoDataFrame must be Polygon, "
            "if `search_radius` is None."
        )
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            zstats = zonal_stats(input_gdf, line_data[0], affine=line_data[1],
                                 stats=['sum'], nodata=0)
        search_area = input_gdf.area
    else:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            buff_factor = _buffer_factor(input_gdf, search_radius)
            input_buff = input_gdf.centroid.buffer(buff_factor)
            zstats = zonal_stats(input_buff, line_data[0], affine=line_data[1],
                                 stats=['sum'], nodata=0)
        search_unit = search_radius.split()[1]
        search_area = input_buff.area
        # convert search area to specified areal unit
        search_area *= UnitHandler(f'square {search_unit}').convert(area_unit)

    output_arr = np.array([v if v is not None else np.nan
                           for d in zstats
                           for v in d.values()])
    return pd.Series(output_arr*cellsize/search_area, index=input_gdf.index)
