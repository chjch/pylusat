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
