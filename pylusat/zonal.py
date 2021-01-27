from rasterstats import zonal_stats
import pandas as pd
from affine import Affine
from geopandas import GeoDataFrame
from pylusat.base import GeoDataFrameManager
from pylusat.utils import read_raster


def _to_affine(cellsize, max_y, min_x):
    """Construct an Affine object."""
    return Affine(cellsize, 0, min_x, 0, -cellsize, max_y)


def zonal_stats_raster(zone_gdf, raster, stats=None,
                       stats_prefix='zone', nodata=None):
    """
    Return specified stats for each geometry in the zone GeoDataFrame.

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
    stats_prefix : str, default 'zone'
        The prefix used to name the output columns of the calculated stats.
        The output column name will be concatenated by a underscore.
        e.g., 'zone_mean'
    nodata : int or float
        Value for no data cells.

    Returns
    -------
    output_gdf : GeoDataFrame
         Returns a GeoDataFrame containing new column(s) for each type of
         statistic specified in the ``stats`` argument.
    """
    if not GeoDataFrameManager(zone_gdf).geom_type_validate("Polygon"):
        raise ValueError("zone GeoDataFrame must be polygon.")

    raster_arr, cellsize, max_y, min_x, nodata = read_raster(raster, nodata)
    affine = _to_affine(cellsize, max_y, min_x)
    zonal_output = zonal_stats(vectors=zone_gdf.geometry, raster=raster_arr,
                               nodata=nodata, affine=affine, stats=stats,
                               all_touched=True)
    zone_gdf.reset_index(drop=True, inplace=True)
    if not stats:
        from rasterstats.utils import DEFAULT_STATS
        stats = DEFAULT_STATS
    else:
        stats = stats.split()
    col_names = [f'{stats_prefix}_{stat}' for stat in stats]
    output_gdf = zone_gdf.join(pd.DataFrame(zonal_output))
    output_gdf.rename(columns=dict(zip(stats, col_names)), inplace=True)
    return output_gdf
