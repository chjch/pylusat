PyLUSAT Quickstart
==================

Example Suitability Analysis
----------------------------

This PyLUSAT Quickstart guide will walk through an example suitability
analysis. To set the scenario, say that Alachua County wants to expand its
existing schools due to increasing population density. They want to know what
areas within one mile of I75 have the high desnsities of student enrollment and
what areas have the greatest distance to the nearest school. To answer this,
the suitability analysis will be conducted in this order:

1. Create a one mile buffer around I75
2. Select by location the ACS2016 block groups within the buffer
3. Calculate the density of student enrollment in the block groups
4. Calculate the distance to the nearest school for the block groups

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

Now calculate the density of student enrollment for the block groups.

.. code-block:: pycon

    >>> from pylusat.density import of_point
    >>> schools_gdf = geopandas.read_file(r"schools.shp")
    >>> den_enrollment_schools = of_point(acs_in_buffer,
                                          schools_gdf,
                                          "ENROLLMENT")
    >>> print(den_enrollment_schools)
    0        0.000000
    1        0.000000
    2      147.881246
    3      184.072565
    4      885.718241
    ..            ...      
    149      0.000000
    150     74.663508
    152    114.202446
    153      0.000000
    154    305.284573
    Length: 146, dtype: float64


Before we can join the density of student enrollment to the ACS2016.gdf, the
series returned by of_pont() must be named.

.. code-block:: pycon

    >>> from pandas import Series
    >>> den_enrollment_schools_series = pandas.Series(den_enrollment_schools,
                                                      name="DENSITY")

Now the enrollment density can be joined to ACS2016.

.. code-block:: pycon

    >>> ACS2016_w_density = acs_in_buffer.join(den_enrollment_schools_series,
                                               how="left")
    >>> print(ACS2016_w_density)
              GEOID10      DENSITY
    0    120010006001     0.000000
    1    120010006002     0.000000
    2    120010006003   147.881246
    3    120010007001   184.072565
    4    120010007002   885.718241
    ..                         ...
    149  120010022182     0.000000
    150  120010022191    74.663508
    152  120010022193   114.202446
    153  120010022201     0.000000
    154  120011108001   305.284573

    [146 rows x 27 columns]

The next thing that we want to calculate is the distance from block groups to
the nearest school.

.. code-block:: pycon

    >>> from pyluysat.distance import to_point
    >>> school_dist = to_point(acs_gdf, schools_gdf, 'euclidean')
    >>> print(school_dist)
    0       197.284083
    1       721.557482
    2       529.379113
    3       293.479326
    4       186.180728
    ...            ...  
    150    1254.314693
    151     471.434822
    152     793.974181
    153    2279.119749
    154     500.748225
    ength: 155, dtype: float64

Alachua County has decided that the 5 block groups with the greatest distance
to the nearest school will each have a new school built in their block group.
To determine this, we can sort school_dist in descending order and get the 5
largest values.

.. code-block:: pycon

    >>> print(school_dist.sort_values(ascending=False).head())
    116    11848.196125
    109     9872.197894
    106     9137.634027
    114     8864.000625
    65      6885.861774
    dtype: float64
