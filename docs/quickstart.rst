PyLUSAT Quickstart
==================

Vector Example
--------------

This PyLUSAT Quickstart guide will walk through an example suitability
analysis, identifying what ACS2016 block group within 1 mile of I75 and
highest density of schools.

First, open the highway.shp as a GeoDataFrame. Create a 1 mile buffer using the
_buffer function. Convert that to a GeoDataFrame using **geometry =**.

.. code-block:: pycon

    >>> import geopandas
    >>> from geopandas import GeoDataFrame
    >>> from pylusat.density import _buffer
    >>> highway_gdf = geopandas.read_file(r"highway.shp")
    >>> highway_buffer = GeoDataFrame(geometry=_buffer(highway_gdf, '1 mi'))

Next, use the buffer to select ACS2016 blockgroups that it intersects.

.. code-block:: pycon
    
    >>> from pylusat.geotools import select_by_location
    >>> acs_gdf = geopandas.read_file(r"acs2016.shp")
    >>> acs_in_buffer = select_by_location(acs_gdf, highway_buffer)

Now calculate the distance between the blockgroups and the nearest school.

.. code-block:: pycon

    >>> from pylusat.distance import to_point
    >>> schools_gdf = geopandas.read_file(r"schools.shp")
    >>> dist_to_schools = to_point(acs_in_buffer, schools_gdf)
    >>> print(dist_to_schools.describe())
    count      146.000000
    mean      1842.447330
    std       1887.920963
    min         55.606597
    25%        701.410851
    50%       1195.888718
    75%       2312.297297
    max      11848.196125
    dtype: float64

Raster Example
--------------

This PyLUSAT Quickstart guide will walk through an example of combining 2
raster files. 

.. code-block:: pycon

    >>> from pylusat.base import RasterManager
    >>> rast = RasterManager.from_path('habitat.tif')
    >>> rast2 = RasterManager.from_path('habitat_shift.tif')

The first thing to do is to make sure that these raster files are able to be
combined, meaning that they have the same cell size and cover the same extent.

.. code-block:: pycon

    >>> matched_rast = rast.match_extent(rast2)
    >>> matched_rast2 = rast2.match_extent(rast)

The two rasters can now be combined using the combine function from
pylusat.geotools.

.. code-block:: pycon

    >>> from pylusat.geotools import combine
    >>> combined_rasters = combine(matched_rast, matched_rast2)