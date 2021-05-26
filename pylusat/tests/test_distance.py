import geopandas as gpd
from pylusat.distance import to_point, to_line, to_cell
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


@pytest.fixture
def acs2016_gdf():
    return gpd.read_file(get_path("acs2016"))


@pytest.fixture
def highway_gdf():
    return gpd.read_file(get_path("highway"))


@pytest.fixture
def habitat_tif():
    return get_path("habitat")


def test_to_point(acs2016_gdf, schools_gdf):
    result = to_point(acs2016_gdf, schools_gdf)
    assert round(result[0], 4) == 197.2841


def test_to_line(acs2016_gdf, highway_gdf):
    result = to_line(acs2016_gdf, highway_gdf)
    assert round(result[0], 4) == 715.6116


def test_to_cell(acs2016_gdf, habitat_tif):
    result = to_cell(acs2016_gdf, habitat_tif, 6)
    assert round(result[0], 4) == 5825.4099
