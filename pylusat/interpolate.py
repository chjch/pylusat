import numpy as np
from scipy.spatial import cKDTree
from pandas import Series
from pylusat.utils import cntrd_array


def idw(input_gdf, value_gdf, value_clm, power=2, n_neighbor=12,
        search_radius=None, leafsize=14, min_dist=1e-12, dtype=float):
    """
    Interpolation using inverse distance weighting (IDW).

    This function implements an `IDW interpolation
    <https://en.wikipedia.org/wiki/Inverse_distance_weighting>`. The power
    parameter dictates how fast the influence to a given location by its
    nearby objects decays. `idw_cv`, a k-fold cross validation method is
    offered to determine the most appropriate value of the `power` parameter.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame. Centroids of the input geometries are used.
    value_gdf : GeoDataFrame
        GeoDataFrame containing the values needed to be interpolated.
    value_clm : str
        The name of the column that holds the values in value_gdf.
    power : int or float, optional
        The power parameter in IDW.
    n_neighbor : int, optional
        Number of neighborhoods used for IDW.
    search_radius : float, optional
        Maximum distance used to find neighbors. If not provided, the function
        will search for all neighbors specified by n_neighbors.
    leafsize : positive int, optional
        The number of points at which the algorithm switches over to
        brute-force. Default: 14. See `scipy.spatial.cKDTree` for further
        information.
    min_dist : float, optional
        The distance below which the interpolated value will be set to equal to
        the value of its closest neighbor.
    dtype : str or np.dtype, optional
        Use a np.dtype or Python type to cast the interpolated values to the
        desired type.

    Returns
    -------
    output_sr : Series
        pandas Series that contains the interpolated values for all feature in
        the input_gdf.

    Examples
    --------
    Interpolate Enrollment values in Schools GeoDataFrame to the second power
    with 12 neighborhoods.

    >>> pylusat.interpolate.idw(acs2016_gdf, schools_gdf, 'ENROLLMENT',
                                power=2.00, n_neighbor=12)
    0    26.407251
    1   137.199332
    2   205.822340
    3   231.137558
    4   158.283367

    150 239.502760
    151 404.536623
    152 233.601194
    153 228.459787
    154 490.956496

    """
    if not (isinstance(n_neighbor, int) and
            1 <= n_neighbor <= len(value_gdf.index)):
        # number of neighbors <= number of points created the tree
        raise ValueError("n_neighbor must be a positive integer that is less "
                         "than or equal to the number of rows in value_gdf.")

    value_gdf = value_gdf.reset_index(drop=True)
    value_coords = cntrd_array(value_gdf)
    kdtree = cKDTree(value_coords, leafsize=leafsize)

    if not search_radius:
        search_radius = np.inf
    dd: np.ndarray
    ii: np.ndarray
    dd, ii = kdtree.query(cntrd_array(input_gdf), k=n_neighbor,
                          distance_upper_bound=search_radius)

    if n_neighbor == 1:
        return value_gdf[value_clm][ii]
    if dtype is None:
        dtype = value_gdf[value_clm].dtype

    n = len(input_gdf.index)
    output_arr = np.zeros(n, dtype=dtype)
    if min_dist <= 0:
        min_dist = 1e-12

    for j in range(n):
        within_min = (dd[j] <= min_dist)
        if np.any(within_min):
            output_arr[j] = value_gdf[value_clm][ii[j][within_min][0]]
            continue

        w = 1 / dd[j]**power
        output_arr[j] = np.dot(w, value_gdf[value_clm][ii[j]]) / np.sum(w)

    output_sr = Series(output_arr, index=input_gdf.index)
    return output_sr


def idw_cv(data, yname, func, k=10, seed=None, **kwargs):
    n = len(data.index)  # total number of observations
    f = int(np.ceil(n/k))  # sample size in each fold
    np.random.seed(seed)
    # randomly assign observations to the k-th fold
    s = np.random.choice(np.tile(np.arange(k), f), n, replace=False)

    data = data.reset_index(drop=True)
    mse = np.zeros(k)   # mean square error
    for i in range(k):
        data_test = data.loc[s == i, ]
        data_train = data.loc[s != i, ]
        observed_y = data_test[yname]
        fitted_y = func(data_test, data_train, yname, **kwargs)
        mse[i] = np.mean(np.power((observed_y - fitted_y), 2))
    return np.mean(mse)
