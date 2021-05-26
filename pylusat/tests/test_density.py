import geopandas as gpd
from pylusat.density import of_point, of_line
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def acs2016_gdf():
    return gpd.read_file(get_path("acs2016"))


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


@pytest.fixture
def highway_gdf():
    return gpd.read_file(get_path("highway"))


def test_of_point_no_search(acs2016_gdf, schools_gdf):
    result = of_point(acs2016_gdf, schools_gdf, area_unit='square mile')
    assert round(result[0], 4) == 2.3894


def test_of_point_search(acs2016_gdf, schools_gdf):
    result = of_point(acs2016_gdf, schools_gdf,
                      "ENROLLMENT", '1 mile', 'square mile')
    assert round(result[1], 4) == 0.0003


def test_of_line(acs2016_gdf, highway_gdf):
    result = of_line(acs2016_gdf, highway_gdf,
                     search_radius='1 mile',
                     area_unit='square mile')
    assert round(result[0], 4) == 0.0004
