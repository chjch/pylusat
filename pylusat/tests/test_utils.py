import geopandas as gpd
from pylusat.utils import gridify
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


def test_gridify(schools_gdf):
    result = gridify(schools_gdf, width=1000)
    assert len(result) == 2496
