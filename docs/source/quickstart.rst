PyLUSAT Quickstart
==================

This PyLUSAT Quickstart guide will serve as a starting point for performing
geoprocessing functions using PyLUSAT.

RasterManager
-------------

To better work with raster data within PyLUSAT, the RasterManager class was
created. This class provides a variety of functions which can be found in the
`documentation <https://github.com/chjch/pylusat>`_. The RasterManager class
is based on rasterio and takes either a rasterio dataset or file path as an
argument.

Start by importing RasterManager from pylusat.base.

.. code-block:: pycon

    >>> from pylusat.base import RasterManager

Next, instantiate the class from a path

.. code-block:: pycon

    >>> rast = RasterManager('example.tif', nodata=None)

or from a rasterio dataset.

.. code-block:: pycon

    >>> rast = RasterManager(DatasetReader, nodata=None)

RasterManager Attributes
------------------------

RasterManager objects have a coordinate reference system

.. code-block:: pycon

    >>> rast.get_rio_crs()
    EPSG:32630

and an affine transformation.

.. code-block:: pycon

    >>> rast.get_affine()
    Affine(30.0, 0.0, 358485.0,
           0.0, -30.0, 4265115.0)

Rasterio functions can also be performed on RasterManager objects by referring
to their rasterio datasets.

.. code-block:: pycon

    >>> import rasterio
    >>> rast.rast_ds.count
    1

RasterManager Functions
-----------------------

RasterManager has built in functions as well. This example will walk through
the process of combining two raster files together. This will use `rast` from
above and another raster.

.. code-block:: pycon

    >>> rast2 = RasterManager('example2.tif')

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
