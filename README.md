# PyLUSAT

[![PyPI version](https://img.shields.io/pypi/v/pylusat?color=g)](https://pypi.org/project/pylusat/)
![PyPI - Python version](https://img.shields.io/pypi/pyversions/pylusat)
![pytest](https://github.com/chjch/pylusat/actions/workflows/tests_pylusat.yml/badge.svg)
![license](https://img.shields.io/pypi/l/pylusat)

Python Land-Use Suitability Analysis Toolkit

## Introduction
PyLUSAT intends to provide users with tools that can be used to conduct land-use 
suitability analysis.

Manuscript (currently under review) accessible:

Chen, C., Judge, J., & Hulse, D. (2021). PyLUSAT: An open-source Python toolkit for GIS-based land use suitability analysis. arXiv preprint arXiv:2107.01674.
https://arxiv.org/abs/2107.01674

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
