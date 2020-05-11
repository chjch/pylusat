import geopandas as gpd
from geopandas import GeoDataFrame


def erase(input_gdf, erase_gdf=None):
    """
    Erase erase_gdf from input_gdf.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        Input GeoDataFrame.
    erase_gdf : GeoDataFrame
        Erase GeoDataFrame containing the erase features.

    Returns
    -------
    output : GeoDataFrame
        The remaining features after erasure.
    """
    if erase_gdf is None:
        return input_gdf
    else:
        return gpd.overlay(
            input_gdf, gpd.GeoDataFrame({'geometry': erase_gdf.unary_union}),
            how='difference'
        )


def spatial_join(target_gdf, join_gdf, col_names=None, op="intersects"):
    """
    Spatial join two GeoDataFrames.

    Parameters
    ----------
    target_gdf, join_gdf : GeoDataFrames
        The GeoDataFrame to join to the target GeoDataFrame.
    col_names : list of strings, optional
        Specify the list of column names to join to the target GeoDataFrame.
    op : string, default 'intersects'
        Binary predicate, one of {'intersects', 'contains', 'within'}.
        See http://shapely.readthedocs.io/en/latest/manual.html#binary-predicates.
    Returns
    -------
    GeoDataFrame
        A GeoDataFrame contains all columns in the target GeoDataFrame and the
        specified columns from the join GeoDataFrame.
    """
    if col_names is None:
        return gpd.sjoin(target_gdf, join_gdf, how='left', op=op)
    else:
        col_names.append(join_gdf.geometry.name)
        return gpd.sjoin(target_gdf, join_gdf[col_names],
                         how='left', op=op)


def within_dist(input_gdf, input_id, distance,
                target_gdf=None, output_col=None):
    """
    For each object in the input, test if any object in the target set is
    within a specified distance.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        The input set.
    input_id : str
        The name of the column containing the unique id of the input set.
    distance : int or float
        Distance (in the same unit as the input GeoDataFrame).
    target_gdf : GeoDataFrame
        The target set.
    output_col : str
        The name of the output column.

    Returns
    -------
    output : GeoDataFrame
        The output value is 1 if there exists any target object within the
        specified distance of the input object and 0 otherwise.
    """
    if output_col is None:
        output_col = "within_" + str(distance)
    input_gdf[output_col] = 0
    if len(target_gdf) > 0:
        sjoin_result = gpd.sjoin(
            input_gdf, target_gdf.assign(geom=target_gdf.buffer(distance)),
            how='inner', op='intersects'
        )[input_id]
        input_gdf.loc[input_gdf[input_id].isin(sjoin_result), output_col] = 1
    return input_gdf


def select_by_location(input_gdf, select_gdf, how='inner',
                       op='intersects', buffer=0):
    """
    Select part of the input GeoDataFrame based on its relationship with the
    selection GeoDataFrame.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        The input GeoDataFrame.
    select_gdf : GeoDataFrame
        The selecting GeoDataFrame.
    how : string, default 'inner'
        The type of join:

        * 'left': use keys from left_df; retain only left_df geometry column
        * 'right': use keys from right_df; retain only right_df geometry column
        * 'inner': use intersection of keys from both dfs; retain only
          left_df geometry column
    op : string, default 'intersection'
        Binary predicate, one of {'intersects', 'contains', 'within'}.
        See http://shapely.readthedocs.io/en/latest/manual.html#binary-predicates.
    buffer : int, default 0
        Distance used to buffer the selection GeoDataFrame.
    Returns
    -------
    output : GeoDataFrame
        The selected features from the input GeoDataFrame.
    """
    if buffer != 0:
        select_gdf[select_gdf.geometry.name] = select_gdf.buffer(buffer)
    output_gdf = input_gdf.loc[input_gdf.index.to_series().isin(
        gpd.sjoin(input_gdf, select_gdf, how=how, op=op).index.values), :]
    del output_gdf.index.name
    return output_gdf.copy()
