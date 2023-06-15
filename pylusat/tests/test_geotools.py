import geopandas as gpd
import rasterio as rio
from pylusat.geotools import spatial_join, select_by_location, combine, gridify
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def acs2016_gdf():
    return gpd.read_file(get_path("acs2016"))


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


@pytest.fixture
def habitat_tif():
    return get_path("habitat")


@pytest.fixture
def habitat_rio():
    return rio.open(get_path("habitat"))


def test_spatial_join(acs2016_gdf, schools_gdf):
    result = spatial_join(acs2016_gdf, schools_gdf,
                          cols_agg={'ENROLLMENT': ['sum']})
    assert result.iloc[2, -1] == 345


def test_select_by_location(acs2016_gdf, schools_gdf):
    result = select_by_location(acs2016_gdf, schools_gdf)
    assert len(result) == 75


def test_combine(habitat_tif):
    rast_obj, attr = combine(habitat_tif, habitat_tif)
    assert len(attr) == 29
    assert attr['count'][attr.value == 1][0] == 618688


def test_combine_rio_ds(habitat_rio):
    rast_obj, attr = combine(habitat_rio, habitat_rio)
    assert len(attr) == 29
    assert attr['count'][attr.value == 1][0] == 618688


def test_gridify(schools_gdf):
    cell_x = 1000
    result = gridify(schools_gdf, cell_x=cell_x)
    assert len(result) == 2544
    assert abs(result.total_bounds[0] - schools_gdf.total_bounds[0]) < cell_x
    assert result.total_bounds[0] % cell_x == 0
