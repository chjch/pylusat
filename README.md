# PyLUSAT

[![PyPI version](https://img.shields.io/pypi/v/pylusat?color=g)](https://pypi.org/project/pylusat/)
![PyPI - Python version](https://img.shields.io/pypi/pyversions/pylusat)
![pytest](https://github.com/chjch/pylusat/actions/workflows/tests_pylusat.yml/badge.svg)
![license](https://img.shields.io/pypi/l/pylusat)

Python Land-Use Suitability Analysis Toolkit

## Introduction
PyLUSAT intends to provide users with tools that can be used to conduct land-use 
suitability analysis.

**Please cite**:

Chen, C., Judge, J., Hulse, D. (2022). PyLUSAT: An open-source Python toolkit for GIS-based land use suitability analysis. _Environmental Modelling and Software_. doi: https://doi.org/10.1016/j.envsoft.2022.105362

## Available Geospatial Functions

- Distance (point, line, raster)
- Density (point, line)
- Reclassify
- Interpolation (inverse distance weighting)
- Spatial Join
- Zonal Statistics
- Analytic Hierarchy Process

## Install
PyLUSAT depends on the following packages.
- geopandas
- rasterio
- rasterstats
- scipy
