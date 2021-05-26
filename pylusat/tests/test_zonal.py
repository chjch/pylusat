import geopandas as gpd
from pylusat.zonal import zonal_stats_raster
import pytest
from pylusat.datasets import get_path


@pytest.fixture
def acs2016_gdf():
    return gpd.read_file(get_path("acs2016"))


@pytest.fixture
def habitat_tif():
    return get_path("habitat")


def test_zonal_stats_raster(acs2016_gdf, habitat_tif):
    zonal_result = zonal_stats_raster(acs2016_gdf, habitat_tif)
    assert zonal_result.iloc[0, -1] == 1303
    assert round(zonal_result.iloc[0, -2], 4) == 32.4351
    assert zonal_result.iloc[0, -3] == 42
    assert zonal_result.iloc[0, -4] == 7
