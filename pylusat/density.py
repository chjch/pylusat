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
    buff_factor = buff_length / UnitHandler(input_unit).convert(buff_unit)
    return input_gdf.buffer(buff_factor)


def of_point(input_gdf, point_gdf, buffer_dist=None, input_clm=None):
    """
    Calculate density of points in each input geometry.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame in which points are counted.
    point_gdf : GeoDataFrame
        Point GeoDataFrame.
    buffer_dist : str, optional
        A string of buffering distance and unit separated by space.
        e.g., "1 mile".
    input_clm : str
        Column that contains values to multiply each occurrence of point.

    Returns
    -------
    output_sr : pd.Series
        A pandas Series that contains the density of point in each input
        geometry of the input GeoDataFrame.
    """
    input_gdf_manager = GeoDataFrameManager(input_gdf)
    assert input_gdf_manager.geom_type_validate("Polygon"), (
        "The geometry of input GeoDataFrame must be Polygon."
    )
    point_gdf_manager = GeoDataFrameManager(point_gdf)
    assert point_gdf_manager.geom_type_validate("Point"), (
        "The geometry of point GeoDataFrame must be Point."
    )
    if buffer_dist is not None:
        input_gdf.geometry = _buffer(input_gdf, buffer_dist)
    joint_gdf = gpd.sjoin(input_gdf, point_gdf, how='left', op='intersects')
    by_input_index = joint_gdf.groupby(level=0)
    if input_clm is None:
        output_sr = by_input_index["index_right"].count()
    else:
        output_sr = by_input_index[input_clm].sum()
    output_sr.fillna(0)
    output_sr.index = input_gdf.index
    output_sr = output_sr / input_gdf.geometry.area
    return output_sr


def of_line(input_gdf, line_gdf, cellsize=30, search_radius=None,
            areal_unit="square meters", geomtoarray=None):
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
        A string of buffering distance and unit separated by space.
        e.g., "1 mile".
    areal_unit : str, optional
        A string of the area unit used for density calculation.
        e.g., "square meters".
    geomtoarray ：np.ndarray, optional
        If a desired ndarray for the line geometries has already been created,
        set it to be this argument to use it.

    Returns
    -------
    output_sr : pd.Series

    """
    from utils import rasterize_geometry
    from rasterstats import zonal_stats

    input_gdf_manager = GeoDataFrameManager(input_gdf)
    assert input_gdf_manager.geom_type_validate("Polygon"), (
        "The geometry of input GeoDataFrame must be Polygon."
    )

    line_gdf_manager = GeoDataFrameManager(line_gdf)
    assert line_gdf_manager.geom_type_validate("Line"), (
        "The geometry of line GeoDataFrame must be Line."
    )

    line_data = rasterize_geometry(line_gdf, cellsize) if geomtoarray is None \
        else geomtoarray
    search_length, search_unit = search_radius.split()
    try:
        areal_name = areal_unit.split()[1]
    except Exception:
        raise ValueError("Invalid areal unit.")

    output_arr = np.array(
        zonal_stats(_buffer(input_gdf.centroid, search_radius), line_data[0],
                    affine=line_data[1], stats=['sum'], nodata=0)
    )

    # convert length from search radius to match the specified areal unit
    search_dist = UnitHandler(search_unit).convert(areal_name) * search_length
    return pd.Series(
        output_arr * cellsize / (np.pi * search_dist**2),
        index=input_gdf.index
    )
