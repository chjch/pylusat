from rasterio import features
from affine import Affine
import numpy as np
from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely.geometry import Polygon


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


def _calc_ahp(r_mtx):
    # random consistency index based on saaty 1990
    ri_dict = {3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24,
               7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    n = r_mtx.shape[0]
    eig_val, eig_vec = np.linalg.eig(r_mtx)
    # principal eigenvalue, i.e., the highest valued eigenvalue
    principal_eig_val = np.max(eig_val).real
    principal_eig_vec = eig_vec[:, eig_val.argmax()].real

    ci = (principal_eig_val - n) / (n - 1)   # consistency index
    cr = ci / ri_dict[n]                     # consistency ratio

    # the normalized principal eigenvector is called the priority vector
    priority_vec = principal_eig_vec / np.sum(principal_eig_vec)
    return priority_vec, cr


def ahp(r_mtx):
    """
    Compute the priority vector of the Analytic Hierarchy Process (AHP).

    The computed priority vector can be used as weights in a decision-making
    process based on multiple criteria. The function also returns the
    Consistency Ratio (CR) to check whether decisions of pair-wise comparisons
    are consistent.

    Parameters
    ----------
    r_mtx : np.ndarray
        The reciprocal matrix.

    Returns
    -------
    priority_vec : np.ndarray
        The priority vector computed by AHP.
    cr : float
        Consistency Ratio (1990, Saaty). The rule of thumb is CR <= 0.1.
    """
    assert r_mtx.ndim == 2, "The reciprocal matrix must be 2-D."
    nrow, ncol = r_mtx.shape
    assert nrow == ncol, "The reciprocal matrix must be a square matrix."
    # validate the number of criteria is between 3 and 10
    assert 3 <= nrow <= 10, (
        "The number of rows/columns must be between 3 and 10."
    )
    # validate matrix's elements are valid members of the AHP fundamental scale
    ahp_scale = np.append(1 / (np.arange(9)+1), np.arange(1, 9)+1)
    assert (
        np.isin(r_mtx[np.tril_indices(nrow)], ahp_scale).all().item() is True
    ), ("One or more elements of the input matrix "
        "is not a valid member of "
        "the AHP fundamental scale.")
    # validate the matrix is indeed reciprocal
    assert (
        1 / r_mtx.T[np.tril_indices(nrow)] ==
        r_mtx[np.tril_indices(nrow)]
    ).all().item() is True, "Invalid reciprocal matrix."
    return _calc_ahp(r_mtx)


def random_ahp(n=3):
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
    priority_vec : np.ndarray
        An array that contains the weights (priority vector of AHP).
    """
    if n < 3 or n > 10:
        raise ValueError("The number must be between 3 and 10.")

    # an array of scales for pair-wise comparison
    ahp_scale = np.append(1 / (np.arange(9) + 1), np.arange(1, 9) + 1)

    while True:
        # upper triangular part of AHP's reciprocal matrix
        triu_weights = np.random.choice(ahp_scale, np.sum(np.arange(n)))

        r_mtx = np.identity(n)   # the reciprocal matrix
        r_mtx[np.triu_indices(n, 1)] = triu_weights
        r_mtx[np.tril_indices(n, -1)] = 1 / r_mtx.T[np.tril_indices(n, -1)]

        priority_vec, cr = _calc_ahp(r_mtx)
        if cr < 0.1:       # general rule of thumb: CR less than 10%
            break
    return priority_vec, cr


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
    weighted_sum : np.ndarray
        An array contains the result of the weighted sum.
    """
    wgt_df = DataFrame([*col_weights.values()], index=[*col_weights])
    return df[[*col_weights]].dot(wgt_df)


def gridify(input_gdf, width=None, height=None, num_cols=None, num_rows=None):
    """
    Create a grid based on the input_gdf by specifying width and/or height of
    the cells of the grid.

    num_cols and num_rows can be used to define the grid as well. If nothing
    specified, the cell size of the grid will be the span on x axis (width)
    divided by 30.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame based on which the grid is created.
    width : int or float
        Cell width.
    height : int or float
        Cell height.
    num_cols : int
        Number of columns. When specified, this number will determine cell
        width.
    num_rows : int
        Number of rows. When specified, this number will determine cell height.

    Returns
    -------
    GeoDataFrame
        The output grid (polygons).
    """
    xmin, ymin, xmax, ymax = input_gdf.total_bounds

    if width and height:
        pass
    else:
        if not width and not height:
            width = height = (xmax - xmin) / 30
        else:
            if width:
                height = width
            elif height:
                width = height

    if num_cols and num_rows:
        # width and height are calculated based on num_cols and num_rows
        width = (xmax - xmin) / num_cols
        height = (ymax - ymin) / num_rows
    else:
        if num_cols:
            width = height = (xmax - xmin) / num_cols
        elif num_rows:
            height = width = (ymax - ymin) / num_rows
        else:
            pass

    cols = np.arange(xmin - width/2, xmax + width/2, width)
    rows = np.arange(ymin - height/2, ymax + height/2, height)

    polygons = [
        Polygon([
            (x, y),
            (x+width, y),
            (x+width, y+height),
            (x, y+height)
        ])
        for y in rows
        for x in cols
    ]

    return GeoDataFrame({'geometry': polygons}, crs=input_gdf.crs)
