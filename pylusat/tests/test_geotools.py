import geopandas as gpd
from pylusat.geotools import spatial_join, select_by_location
from pylusat.datasets import get_path
import pytest


@pytest.fixture
def acs2016_gdf():
    return gpd.read_file(get_path("acs2016"))


@pytest.fixture
def schools_gdf():
    return gpd.read_file(get_path("schools"))


def test_spatial_join(acs2016_gdf, schools_gdf):
    result = spatial_join(acs2016_gdf, schools_gdf,
                          cols_agg={'ENROLLMENT': ['sum']})
    assert result.iloc[2, -1] == 345


def test_select_by_location(acs2016_gdf, schools_gdf):
    result = select_by_location(acs2016_gdf, schools_gdf)
    assert len(result) == 75
