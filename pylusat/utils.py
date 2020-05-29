from rasterio import features
from affine import Affine
import numpy as np
from geopandas import GeoDataFrame
from pandas import DataFrame


def rasterize_geometry(gdf, cellsize, value_clm=None, value_fill=0):
    """
    Transform vector data into a 2-d array. If any (or a part of) geometry
    presents at a given cell, the cell will be assigned to a value of 1,
    otherwise 0.

    Parameters
    ----------
    gdf : GeoDataFrame
        Input GeoDataFrame.
    cellsize : int or float
        Cell size used to transform the vector data.
    value_clm : str, optional
        The name of the column which contains the values for each cell in the
        output array.
    value_fill : int, optional
        Fill value for all areas not covered by the input geometries.
    Returns
    -------
    arr : np.ndarray
        Output numpy array.
    trans : Affine
        An object of the Affine class.
    extent : tuple
        a tuple containing ``min_x``, ``min_y``, ``max_x``, ``max_y``
        values for the bounds of the series as a whole.
        See GeoSeries.bounds for the bounds of the geometries contained in
        the series.
    nodata : int or float
        The no data value used during the rasterization.
    """
    extent = gdf.total_bounds
    output_shape = (int(round((extent[3] - extent[1]) / cellsize)),
                    int(round((extent[2] - extent[0]) / cellsize)))
    trans = Affine(cellsize, 0, extent[0], 0, -cellsize, extent[3])
    if value_clm is None:
        arr = features.rasterize(gdf[gdf.geometry.name],
                                 out_shape=output_shape,
                                 fill=value_fill,
                                 transform=trans)
    else:
        arr = features.rasterize(
            tuple(zip(gdf[gdf.geometry.name], gdf[value_clm])),
            out_shape=output_shape, fill=value_fill, transform=trans
        )
    nodata = value_fill
    return arr, trans, extent, nodata


def cntrd_array(gdf):
    """
    Get the coordinates of the centroids in a 2D array.

    Parameters
    ----------
    gdf : GeoDataFrame
        Input GeoDataFrame.
    Returns
    -------
    output : np.ndarray
        An n by 2 2D array where each row contains the coordinates (x and y)
        of the centroids of each geometry in the input GeoDataFrame.
    """
    if isinstance(gdf, GeoDataFrame):
        return np.column_stack((gdf.centroid.x.values,
                                gdf.centroid.y.values))
    else:
        raise TypeError("The input data must be a GeoDataFrame.")


def inv_affine(gdf, cellsize, max_y, min_x):
    """
    Convert (x, y) coordinates of the centroids of a GeoDataFrame to
    (row, column) on a grid.

    Parameters
    ----------
    gdf : GeoDataFrame
        Input GeoDataFrame for the function.
    cellsize : int or float
        Cell size used to grid the vector data.
    max_y : int or float
        Upper bound on the y axis of the grid.
    min_x : int or float
        Lower bound on the x axis of the grid.

    Returns
    -------
    np.ndarray
        An n by 2 2D-array of (row, column) indices for the centroid of each
        geometry in the input GeoDataFrame.
    """
    return np.column_stack(
        (np.round((max_y - gdf.centroid.y) / cellsize).values,   # row
         np.round((min_x - gdf.centroid.x) / -cellsize).values)  # column
    )


def read_raster(raster, nodata=None):
    """
    Read the raster data and return numpy array.

    Parameters
    ----------
    raster : str
        A path to a tif file or a connection string to a raster on PostgreSQL.
    nodata : int or float
        Value for no data cells.

    Returns
    -------
    raster_arr : np.ndarray
        The numpy array converted from the raster data.
    cellsize : int or float
        The cell size of the raster data.
    max_y : int or float
        The y coordinate of the upper left corner of the raster data.
    min_x : int or float
        The x coordinate of the upper left corner of the raster data.
    nodata : int or float
        The no data value used during the conversion.
    """
    from osgeo import gdal
    try:
        raster_data = gdal.Open(raster)
        raster_band = raster_data.GetRasterBand(1)
        raster_trans = raster_data.GetGeoTransform()
        raster_arr = raster_band.ReadAsArray()
        if nodata is not None:
            raster_arr[
                np.where(raster_arr == raster_band.GetNoDataValue())
            ] = nodata
        cellsize = raster_trans[1]
        max_y = raster_trans[3]
        min_x = raster_trans[0]
        return raster_arr, cellsize, max_y, min_x, nodata
    except Exception:
        raise ValueError("Not a valid raster data.")


def random_ahp_weight(n=3):
    """
    Generate randomized Analytic Hierarchy Process (AHP) weights.

    This function generates random weights, i.e., priority vector, using the
    AHP method (1990, Saaty). The randomly generated weights are ensured to
    be consistent by evaluating the consistency ratio (CR).

    Parameters
    ----------
    n : int, optional, default 3
        Number of AHP weights to generate, which must be between 3 and 10.

    Returns
    -------
    np.ndarray
        An array that contains the weights (priority vector of AHP).
    """
    if n < 3 or n > 10:
        raise ValueError("The number must be between 3 and 10.")
    # dict of random consistency index
    ri_dict = {3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24,
               7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

    # an array of scales for pair-wise comparison
    scale_pair_comp = np.append(1 / (np.arange(9) + 1), np.arange(1, 9) + 1)

    while True:
        # upper triangular part of AHP's reciprocal matrix
        triu_weights = np.random.choice(scale_pair_comp, np.sum(np.arange(n)))

        ahp = np.identity(n)   # the reciprocal matrix
        ahp[np.triu_indices(n, 1)] = triu_weights
        ahp[np.tril_indices(n, -1)] = 1 / ahp.T[np.tril_indices(n, -1)]

        eig_val, eig_vec = np.linalg.eig(ahp)
        principal_eig_val = eig_val[0].real
        principal_eig_vec = eig_vec[:, 0].real

        ci = (principal_eig_val - n) / (n - 1)   # consistency index
        cr = ci / ri_dict[n]                     # consistency ratio
        if cr < 0.1:       # general rule of thumb: CR less than 10%
            break
    priority_vec = principal_eig_vec / np.sum(principal_eig_vec)
    return priority_vec


def weighted_sum(df, col_weights):
    """
    Calculate a weighted sum over a list of existing columns.

    Parameters
    ----------
    df : DataFrame or GeoDataFrame
        Input DataFrame contains the columns for summation.
    col_weights : dict
        Dict of ``{column name: float}``, where float is the weight for the
        column specified by the column name.
    Returns
    -------
    np.ndarray
        An array contains the result of the weighted sum.
    """
    wgt_df = DataFrame([*col_weights.values()], index=[*col_weights])
    return df[[*col_weights]].dot(wgt_df)
