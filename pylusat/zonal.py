from rasterstats import zonal_stats
import pandas as pd
from affine import Affine
from geopandas import GeoDataFrame
from pylusat.base import GeoDataFrameManager
from pylusat.utils import read_raster


def _to_affine(cellsize, max_y, min_x):
    """Construct an Affine object."""
    return Affine(cellsize, 0, min_x, 0, -cellsize, max_y)


def zonal_stats_raster(zone_gdf, raster, stats=None, nodata=None):
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
        Defaults to rasterstats.utils.DEFAULT_STATS which is
        ['count', 'min', 'max', 'mean'].
        Other valid stats are ['sum', 'std', 'median', 'majority', 'minority',
        'unique', 'range', 'nodata', 'nan'].
        See rasterstats for more details.
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
    if zone_gdf.index.name is None:
        zone_index = 'index'
    else:
        zone_index = zone_gdf.index.name

    zone_gdf.reset_index(inplace=True)
    output_gdf = zone_gdf.join(pd.DataFrame(zonal_output))
    output_gdf.set_index(zone_index, inplace=True)
    return output_gdf
