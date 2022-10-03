import numpy as np
import pandas as pd
from pandas import DataFrame
from geopandas import GeoDataFrame
from scipy import stats


def reclassify(input_df, input_col, reclassify_def, output_col, nodata=None):
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

    if key_type == {tuple}:
        # get the lowest interval
        lowest_id = np.argmin(
            [left for left, right in reclassify_def.keys()]
        ).item()
        lowest_left, lowest_right = list(reclassify_def.keys())[lowest_id]
        # change values equal to the lowest left to the lowest right
        input_df.loc[input_df[input_col] == lowest_left,
                     input_col] = lowest_right
        intervals = pd.Series(
            list(reclassify_def.values()),
            index=pd.IntervalIndex.from_tuples([*reclassify_def])
        )
        output_sr = input_df[input_col].map(intervals)
    elif key_type == {int} or key_type == {str} or key_type == {float}:
        output_sr = input_df[input_col].map(reclassify_def)
    else:
        raise ValueError("Keys of the reclassify dictionary must be "
                         "exclusively of string, number, or tuple of two "
                         "numbers.")
    if output_sr.isna().values.any() and nodata:
        output_sr.fillna(nodata, inplace=True)

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

    Examples
    --------
    Linearlly rescale the enrollment column of the schools GeoDataFrame.

    >>> pylusat.rescale.linear(schools_gdf, "ENROLLMENT", "ENROLL_CLS")
                                            NAME    ENROLL_CLS
    0               COUNTRYSIDE CHRISTIAN SCHOOL    1.384930
    1     TRILOGY SCHOOL OF LEARNING ALTERNATIVE    1.305039
    2               MILLHOPPER MONTESSORI SCHOOL    1.784385
    3              ST MICHAEL'S EPISCOPAL SCHOOL    1.000000
    4                     BNAI ISRAEL DAY SCHOOL    1.079891
    ...
    116     PERSIMMON EARLY LEARNING ACADEMY LLC    1.000000
    117 BUSY BEE AND BUTTERFLY CHRISTIAN ACADEMY    1.000000
    118                       THE PHENOM ACADEMY    1.000000
    119     ALACHUA LEARNING CENTER, INC. MIDDLE    1.221516
    120                FLORIDA SCHOOL OF MASSAGE    1.000000
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
