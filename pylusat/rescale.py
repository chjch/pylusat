import numpy as np
import pandas as pd
from pandas import DataFrame
from geopandas import GeoDataFrame
from scipy import stats


def reclassify(input_df, input_col, reclassify_def, output_col, nodata=1):
    """
    Reclassify values in an existing column based on key-value pairs provided
    in a dictionary.

    The function can handle both categorical and interval definitions. For
    interval definition, the keys of the dictionary should be a tuple of two
    numbers corresponding to the start and end of each interval. The intervals
    are right closed.

    Parameters
    ----------
    input_df : DataFrame or GeoDataFrame
        Input DataFrame with the column need to be reclassified.
    input_col : str
        The name of the input column containing the old values.
    reclassify_def : dict
        The dictionary consists of definitions to convert old values to new
        values.
    output_col: str
        The name of the output column.
    nodata : int or float, optional
        The value used to fill the nodata records.
    Returns
    -------
    input_df : DataFrame or GeoDataFrame
        The output DataFrame with the reclassified values.

    """
    key_type = set(map(type, [*reclassify_def]))
    value_type = set(map(type, reclassify_def.values()))
    if len(value_type) > 1:
        raise ValueError("Values of the reclassify dictionary must be "
                         "exclusively of integer, string, or float.")
    value_type = list(value_type)[0].__name__

    if key_type == {tuple}:
        # get the lowest interval and its corresponding remapped value
        lowest_interval, lowest_new = next(iter(reclassify_def.items()))
        intervals = pd.IntervalIndex.from_tuples([*reclassify_def])
        output_sr = (
            pd.cut(input_df[input_col], intervals).cat.rename_categories(
                {pd.Interval(*k): reclassify_def[k]
                 for k in reclassify_def.keys()}
            )
        )
        output_sr.loc[input_df[input_col] == lowest_interval[0]] = lowest_new
        output_sr = output_sr.astype(value_type)
        if output_sr.isna().values.any():
            output_sr.fillna(nodata, inplace=True)
    elif key_type == {int} or key_type == {str} or key_type == {float}:
        output_sr = input_df[input_col].map(reclassify_def)
        if output_sr.isna().values.any():
            output_sr.fillna(nodata, inplace=True)
    else:
        raise ValueError("Keys of the reclassify dictionary must be "
                         "exclusively of string, number, or tuple of two "
                         "numbers.")

    input_df[output_col] = output_sr
    return input_df


def linear(input_df, input_col, output_col,
           start=None, end=None,
           output_min=1, output_max=9):
    """
    Rescale a column in a DataFrame linearly.

    If argument start is greater than end, the rescaling is in the
    same direction as values in the input column, i.e., smaller (bigger) values
    in the input column correspond to smaller (bigger) values in the output.
    If argument start is less than end, the rescaling is in the reverse
    direction as values in the input column.
    The start and end of the input column do not necessarily to be the minimum
    and maximum of the input column. Values beyond the specified bound will be
    assigned to output_min and output_max, depending on which side they are on.

    Parameters
    ----------
    input_df : DataFrame or GeoDataFrame
        Input DataFrame containing a column need to be rescaled.
    input_col : str
        Name of the old column.
    output_col : str
        Name of the new column.
    start : int or float
        Value from which the rescaling starts.
    end : int or float
        Value from which the rescaling ends.
    output_min : int or float
        The minimum value of the output column.
    output_max : int or float
        The maximum value of the output column.

    Returns
    -------
    input_df : DataFrame or GeoDataFrame
        Output DataFrame containing the rescaled column.

    """
    if start is None:
        start = input_df[input_col].min()
    if end is None:
        end = input_df[input_col].max()
    input_range = abs(end - start)
    output_range = abs(output_max - output_min)
    if end > start:
        input_df[output_col] = (
            output_min
            + (input_df[input_col] - start) * output_range / input_range
        )
        input_df.loc[input_df[input_col] > end, output_col] = output_max
        input_df.loc[input_df[input_col] < start, output_col] = output_min
    else:
        input_df[output_col] = (
            output_max
            - (input_df[input_col] - end) * output_range / input_range
        )
        input_df.loc[input_df[input_col] < end, output_col] = output_max
        input_df.loc[input_df[input_col] > start, output_col] = output_min
    return input_df


def gamma(input_df, input_col, output_col, output_min=1, output_max=9):
    """
    Rescale values in a column based on an asymptotic gamma distribution.

    The function calls a gamma object from the stats module in the SciPy
    package, see more detail from:
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.gamma.html
    First, Maximum Likelihood Estimation (MLE) is used to estimate the shape
    and scale parameters from the data. Then, the function calculates a new
    value for its associated old value, x, by scaling the probability of the
    random variable being less than or equal to x, based on the the estimated
    cumulative density function (cdf).

    Parameters
    ----------
    input_df : DataFrame or GeoDataFrame
        Input DataFrame containing a column need to be rescaled.
    input_col : str
        Name of the old column.
    output_col : str
        Name of the new column.
    output_min : int or float
        The minimum value of the output column.
    output_max : int or float
        The maximum value of the output column.

    Returns
    -------
    input_df : DataFrame or GeoDataFrame
        Output DataFrame containing the rescaled column.
    """
    df = input_df[~np.isnan(input_df[input_col])]
    a, loc, b = stats.gamma.fit(df[input_col], floc=0)
    input_df[output_col] = output_min
    new_scale = output_max - output_min
    rescale_start = output_min + 1
    input_df.loc[~np.isnan(input_df[input_col]), output_col] = (
        stats.gamma.cdf(df[input_col], a, loc=0, scale=b)
        * (new_scale - rescale_start)
        + rescale_start
    )
    return input_df
