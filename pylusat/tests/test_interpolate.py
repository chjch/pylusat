import geopandas as gpd
from pylusat.interpolate import idw
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def acs2016_gdf():
    return gpd.read_file(get_path("acs2016"))


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


def test_idw(acs2016_gdf, schools_gdf):
    idw_result = idw(acs2016_gdf, schools_gdf, 'ENROLLMENT',
                     power=2.00, n_neighbor=12)
    assert round(idw_result[0], 4) == 26.4073
