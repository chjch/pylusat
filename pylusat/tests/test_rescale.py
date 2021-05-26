import geopandas as gpd
from pylusat.rescale import linear
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


def test_rescale(schools_gdf):
    result = linear(schools_gdf, "ENROLLMENT", "ENROLL_CLS")
    assert round(result.iloc[0, -1], 4) == 1.3849
