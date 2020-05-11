import numpy as np
from geopandas import GeoDataFrame
from pandas import Series
from pylusat.base import GeoDataFrameManager
from pylusat.utils import (rasterize_geometry, cntrd_array,
                           inv_affine, read_raster)


class _ArrayDistance:

    SUPPORT_DIST = ["Point", "Line", "Raster"]

    def __init__(self, target_type, method, dtype):
        if target_type.title() not in self.SUPPORT_DIST:
            raise ValueError('Unsupported target data. Must be "Point", '
                             '"Line", or "Raster".')
        self.target_type = target_type
        self.method = method
        self.dtype = dtype

    @staticmethod
    def _kdtree(target_arr):
        from scipy.spatial import cKDTree
        return cKDTree(target_arr)

    def query(self, source_arr, target_arr):
        kdtree = self._kdtree(target_arr)
        dist_method = 1 if self.method.lower() == 'manhattan' else 2
        dist_arr = kdtree.query(source_arr, p=dist_method)[0]
        if self.dtype is not float:
            return dist_arr.astype(self.dtype)
        else:
            return dist_arr


def _validate_target_geom(gdf, geom_type):
    gdf_manager = GeoDataFrameManager(gdf)
    assert gdf_manager.geom_type_validate(geom_type), (
        "The target geometry must be {}.".format(geom_type)
    )

        
def to_point(input_gdf, point_gdf, method='euclidean', dtype=float):
    """
    Calculate distance for each geometry in the input GeoDataFrame to its
    nearest neighbor in the point GeoDataFrame.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame. Centroids of the input geometries are used.
    point_gdf : GeoDataFrame
        The GeoDataFrame contains the point geometries to which distances are
        calculated.
    method : str, optional
        Method used to calculate distances. Either 'euclidean' or 'manhattan'.
    dtype : str or np.dtype, optional
        Use a np.dtype or Python type to cast the output distance to the
        desired type.

    Returns
    -------
    Series
        A pandas Series containing the distances of each input feature to its
        nearest point.
    """
    target_geom = "Point"
    _validate_target_geom(point_gdf, target_geom)
    pnt_dist = _ArrayDistance(target_geom, method, dtype)
    input_arr = cntrd_array(input_gdf)
    point_arr = cntrd_array(point_gdf)
    pnt_dist_arr = pnt_dist.query(input_arr, point_arr)
    return Series(pnt_dist_arr, index=input_gdf.index)


def to_line(input_gdf, line_gdf, cellsize=30, method="euclidean", dtype=float):
    """
    Calculate distances from input_gdf to line_gdf.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame. Centroids of the input geometries are used.
    line_gdf : GeoDataFrame
        A GeoDataFrame whose geometry is of line. 
    cellsize : float
        Cell size used to rasterize the line_gdf. 
    method : str, optional
        Method used to calculate distances. Either 'euclidean' or 'manhattan'.
    dtype : str or np.dtype, optional
        Use a np.dtype or Python type to cast the output distance to the
        desired type.

    Returns
    -------
    Series
        A pandas Series of distances from each feature in input_gdf to its
        nearest neighbor in line_gdf.
    Notes
    -----
    To rapidly query distances, the line_gdf is burned into numpy array by
    using rasterize function from the rasterio package.
    """
    target_geom = "Line"
    _validate_target_geom(line_gdf, target_geom)
    line_grid, _, extent, nodata = rasterize_geometry(line_gdf, cellsize)

    max_y = extent[3]  # max_y from extent
    min_x = extent[0]  # min_x from extent

    input_arr = inv_affine(input_gdf, cellsize, max_y=max_y, min_x=min_x)
    line_arr = np.argwhere(line_grid != nodata)

    line_dist = _ArrayDistance("Line", method, dtype)
    line_dist_arr = line_dist.query(input_arr, line_arr) * cellsize

    return Series(line_dist_arr, index=input_gdf.index)


def to_cell(input_gdf, raster, value, nodata=None,
            method="euclidean", dtype=float):
    """
    Calculate distance for each geometry to its nearest-neighbor cell that has
    a specific value.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame
    raster : str
        A path to a tif file or a connection string to a raster on PostgreSQL.
    value : int or float
        Cells in the raster with this value will be used as targets for
        distance calculation.
    nodata : int or float
        Value for no data cells.
    method : str, optional, default "euclidean"
        Method used to calculate distances. Either 'euclidean' or 'manhattan'.
    dtype : str or np.dtype, optional
        Use a np.dtype or Python type to cast the output distance to the
        desired type.

    Returns
    -------
    Series
        A pandas Series of distances from each feature in input_gdf to the
        nearest cell (has the specified value) in the raster dataset.
    """
    raster_grid, cellsize, max_y, min_x, nodata = read_raster(raster, nodata)
    input_arr = inv_affine(input_gdf, cellsize, max_y, min_x)
    raster_arr = np.argwhere(raster_grid == value)

    raster_dist = _ArrayDistance("Raster", method, dtype)
    raster_dist_arr = raster_dist.query(input_arr, raster_arr) * cellsize

    return Series(raster_dist_arr, index=input_gdf.index)
