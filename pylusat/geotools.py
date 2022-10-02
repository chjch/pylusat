import numpy as np
import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
from typing import Dict
from shapely.geometry import Polygon
from rasterio.io import MemoryFile
from pylusat.base import RasterManager


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


def spatial_join(target_gdf, join_gdf, op="intersects",
                 cols_agg: Dict[str, list] = None,
                 join_type="one to one", keep_all=True):
    """
    Spatial join two GeoDataFrames.

    Parameters
    ----------
    target_gdf, join_gdf : GeoDataFrames
        The GeoDataFrame to join to the target GeoDataFrame.
    op : string, default 'intersects'
        Binary predicate, one of {'intersects', 'contains', 'within'}. See
        http://shapely.readthedocs.io/en/latest/manual.html#binary-predicates.
    cols_agg : dict, default None
        Dict of ``{column_name: a list of statistics}``, where the list of
        statistics is a list of strings containing the names of desired
        statistics for each column. Names of the statistics include:
        {'first', 'last', 'sum', 'mean', 'median', 'max', 'min',
        'std', 'var', 'count', 'size'}.
    join_type : string, default 'one to one'
        Binary predicate, one of {'one to one', 'one to many'}. The option
        'one to one' only returns one row for each target feature, whereas
        option 'one to many' return multiple rows for each match between
        target feature and join feature.
    keep_all : bool, default True
        Whether to keep all features from the target GeoDataFrame.
    Returns
    -------
    GeoDataFrame
        A GeoDataFrame contains all columns in the target GeoDataFrame and the
        specified columns from the join GeoDataFrame.
    
    Examples
    -------
    >>> pylusat.geotools.spatial_join(acs2016_gdf, schools_gdf, 
                                      cols_agg={'ENROLLMENT': ['sum]})
             GEOID10    ENROLLMENT_SUM
    0   120010006001               0.0
    1   120010006002               0.0
    2   120010006003             345.0
    3   120010007001              37.0
    4   120010007002            1420.0
    ...
    150 120010022191             113.0
    151 120010022192            1889.0
    152 120010022193             118.0
    153 120010022201               0.0
    154 120011108001             803.0
    
    """
    how = 'left' if keep_all else 'inner'
    gpd_sjoin = gpd.sjoin(target_gdf, join_gdf, how=how, op=op)

    if join_type.lower() == "one to one":
        sjoin_by_index = gpd_sjoin.groupby(gpd_sjoin.index)

        if cols_agg is None:
            cols_agg = {col: ['first'] for col in join_gdf.columns
                        if col != join_gdf.geometry.name}
            join_df = sjoin_by_index.agg(cols_agg)
            join_df.columns = cols_agg.keys()
        else:
            join_df = sjoin_by_index.agg(cols_agg)
            join_df.columns = [f"{key}_{v}"
                               for key, value in cols_agg.items()
                               for v in set(value)]

        # grab columns of target_gdf
        target_gdf_columns = gpd_sjoin.columns[:len(target_gdf.columns)]
        # remove duplicated rows generated by geopandas spatial join
        # based on columns of target_gdf
        target_df = gpd_sjoin[target_gdf_columns].drop_duplicates()
        return pd.concat([target_df, join_df], axis=1)
    elif join_type.lower() == "one to many":
        return gpd_sjoin
    else:
        raise ValueError("join_type must be either 'one to one' or "
                         "'one to many'")


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


def select_by_location(input_gdf, select_gdf,
                       op='intersects', within_dist=0):
    """
    Select part of the input GeoDataFrame based on its relationship with the
    selecting GeoDataFrame.

    Parameters
    ----------
    input_gdf : GeoDataFrame
        The input GeoDataFrame.
    select_gdf : GeoDataFrame
        The selecting GeoDataFrame.
    op : string, default 'intersection'
        Binary predicate, one of {'intersects', 'contains', 'within',
        'within a distance'}. See
        http://shapely.readthedocs.io/en/latest/manual.html#binary-predicates.
    within_dist : int, default 0
        Search distance around the select_gdf. This parameter is only
        useful when op is set to be "within a distance".
    Returns
    -------
    output : GeoDataFrame
        The selected features from the input GeoDataFrame.
    
    Examples
    --------
    >>> pylusat.geotools.select_by_location(acso2016_gdf, schools_gdf)
               GEOID    geometry
    0   120010006001    POLYGON ((564121.721 629847.127, 564127.038...))     
    2   120010006003    POLYGON ((565858.254 629636.152, 565695.479...))
    3   120010007001    POLYGON ((563316.398 627676.644, 563228.536...))
    4   120010007002    POLYGON ((563768.801 627680.962, 563770.869...))
    5   120010007003    POLYGON ((565229.514 624327.588, 564862.624...))
    
    """
    ops = ['intersects', 'contains', 'within', 'within a distance']
    assert op in ops, 'invalid op parameter,'
    if op == 'within a distance' and within_dist:
        select_gdf[select_gdf.geometry.name] = select_gdf.buffer(within_dist)
        op = 'within'
    output_gdf = input_gdf.loc[
                 input_gdf.index.to_series().isin(
                     gpd.sjoin(
                         input_gdf, select_gdf,
                         how='inner', op=op
                     ).index.values
                 ), :
                 ]
    output_gdf = output_gdf.rename_axis(None, axis=1)
    return output_gdf.copy()


def combine(rast1_path, rast2_path):
    """
    Combines input rasters by their unique value pairs. Assigns new values to
    each unique pair.
    Parameters
    ----------
    rast1_path : str
        File path to the first raster.
    rast2_path : str
        File path to the second raster.
    Returns
    -------
    Results : rasterio Dataset, DataFrame
        The combined raster files as a Rasterio Dataset.
        The output attribute table as a Pandas DataFrame.

    Examples
    --------
    >>> pylusat.geotools.combine(habitat_tif, habitati_tif)
    0   1   0   0   618688
    1   2   2   2   1
    2   3   3   3   1
    3   4   5   5   20539
    4   5   6   6   115

    """
    input_ras1 = RasterManager.from_path(rast1_path)
    input_ras2 = RasterManager.from_path(rast2_path)
    arr1 = input_ras1.to_array()
    arr2 = input_ras2.to_array()
    arr1_1d = np.reshape(arr1, arr1.size)
    arr2_1d = np.reshape(arr2, arr2.size)

    if arr1_1d.size != arr2_1d.size:
        raise ValueError('Match raster extents before combining.')

    geo_tform = input_ras1.get_affine()
    out_width = input_ras1.rast_ds.width
    out_height = input_ras1.rast_ds.height
    out_crs = input_ras1.get_rio_crs()
    out_count = input_ras1.rast_ds.count
    out_nd = input_ras1.rast_nodata

    df = (pd.DataFrame(np.column_stack([arr1_1d, arr2_1d]), columns=['a', 'b'])
          .reset_index()
          .rename({'index': 'position'}, axis=1))
    unique_grouping = df.groupby(['a', 'b'], as_index=False).size()
    unique_grouping.index += 1

    attr = (unique_grouping.reset_index()
            .rename({'index': 'value', 'size': 'count'}, axis=1))

    dfs = (df.set_index(['a', 'b'])
           .join(attr.set_index(['a', 'b'])['value'])
           .reset_index()
           .set_index('position')
           .sort_index()['value'].values)
    output_arr = np.reshape(dfs, arr1.shape)

    with MemoryFile() as memfile:
        rst = memfile.open(driver='GTiff', count=out_count, dtype='int32',
                           crs=out_crs, width=out_width, height=out_height,
                           transform=geo_tform, nodata=out_nd, tiled=False)
        rst.write(output_arr, indexes=1)
        rst.close()
        return memfile.open(driver="GTiff"), attr


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

    Examples
    --------
    >>> pylusat.geotools.gridify(schools_gdf, width=1000)
    0       POLYGON ((533359.960 611556.855, 534359.960...))
    1       POLYGON ((534359.960 611556.855, 535359.960...))
    2       POLYGON ((535359.960 611556.855, 536359.960...))
    3       POLYGON ((536359.960 611556.855, 537359.960...))
    4       POLYGON ((537359.960 611556.855, 538359.960...))
    ...
    2491    POLYGON ((580359.960 658556.855, 581359.960...))
    2492    POLYGON ((581359.960 658556.855, 582359.960...))
    2493    POLGYON ((582359.960 658556.855, 583359.960...))
    2494    POLYGON ((583359.960 658556.855, 584359.960...))
    2495    POLGYON ((584359.960 658556.855, 585359.960...))
    
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
