import geopandas as gpd
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


def test_gridify(schools_gdf):
    result = gridify(schools_gdf, width=1000)
    assert len(result) == 2496
