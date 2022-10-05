from rasterstats import zonal_stats
import pandas as pd
from affine import Affine
from geopandas import GeoDataFrame
from pylusat.base import GeoDataFrameManager
from pylusat.base import RasterManager


def _to_affine(cellsize, max_y, min_x):
    """Construct an Affine object."""
    return Affine(cellsize, 0, min_x, 0, -cellsize, max_y)


def zonal_stats_raster(zone_gdf, raster, stats=None,
                       stats_prefix='zonal', nodata=None):
    """
    Calculate specified stats for each geometry in the zone GeoDataFrame.

    If raster and zone GeoDataFrame were in different spatial reference
    systems, the raster will be warped (reprojected) to match the spatial
    reference of the zone GeoDataFrame.

    Parameters
    ----------
    zone_gdf : GeoDataFrame
        The zone GeoDataFrame whose geometry must be polygon.
    raster : str
        A path to a tif file or a connection string to a raster on PostgreSQL.
        The raster dataset whose values are summarized.
    stats : list of str, or space-delimited str, optional
        Which statistics to calculate for each zone.
        Defaults to rasterstats.utils.DEFAULT_STATS, i.e.,
        ['count', 'min', 'max', 'mean'].
        Other valid stats are ['sum', 'std', 'median', 'majority', 'minority',
        'unique', 'range', 'nodata', 'nan'].
        See rasterstats for more details.
    stats_prefix : str, default 'zonal'
        The prefix used to name the output columns of the calculated stats.
        The output column name will be concatenated by a underscore.
        e.g., 'zonal_mean'
    nodata : int or float
        Value for no data cells.

    Returns
    -------
    output_gdf : geopandas.GeoDataFrame
         Returns a GeoDataFrame containing new column(s) for each type of
         statistic specified in the ``stats`` argument.
    
    Examples
    --------
    Summarize values of habitat raster in each census tract zone.

    >>> pylusat.zonal.zonal_stats_raster(acs2016_gdf, habitat_tif)
        GEOID10               ACRES TOTALPOP    zonal_max  zonal_mean  zonal_count
    0   12001006001      267.844400     1371        42.0    32.425150         1303
    1   12001006002      144.120683      710        42.0    32.484892          695
    2   12001006003     1493.089927     2291        42.0    21.263203         6949
    3   12001007001      128.644913      828        42.0    33.807512          639
    4   12001007002     1026.058834     1465        42.0    25.799958         4804
    """
    if not GeoDataFrameManager(zone_gdf).geom_type_validate("Polygon"):
        raise ValueError("zone GeoDataFrame must be polygon.")
    gdf_crs = zone_gdf.crs

    rast_manager = RasterManager.from_path(raster, nodata)
    rast_crs = rast_manager.get_rio_crs()

    if gdf_crs.to_epsg() != rast_crs.to_epsg():
        projected_rast = rast_manager.reproject_vrt(
            crs=f"EPSG:{gdf_crs.to_epsg()}"
        )
        rast_manager = RasterManager(projected_rast)

    rast_arr, cellsize, max_y, min_x, nodata = rast_manager.as_rebuild_info()

    affine = _to_affine(cellsize, max_y, min_x)
    zonal_output = zonal_stats(vectors=zone_gdf.geometry, raster=rast_arr,
                               nodata=nodata, affine=affine, stats=stats,
                               all_touched=True)
    zone_gdf.reset_index(drop=True, inplace=True)
    if not stats:
        from rasterstats.utils import DEFAULT_STATS
        stats = DEFAULT_STATS
    elif isinstance(stats, str):
        stats = stats.split()

    col_names = [f'{stats_prefix}_{stat}' for stat in stats]
    output_gdf = zone_gdf.join(pd.DataFrame(zonal_output))
    output_gdf.rename(columns=dict(zip(stats, col_names)), inplace=True)
    return output_gdf
