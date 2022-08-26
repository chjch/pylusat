from pylusat.datasets import get_path
from pylusat.base import RasterManager
import pytest
import math


@pytest.fixture
def habitat_tif():
    return get_path("habitat")


@pytest.fixture
def habitat_shift_tif():
    return get_path("habitat_shift")


def test_raster_manager(habitat_tif, habitat_shift_tif):
    rast_manager = RasterManager.from_path(habitat_tif)
    cell_size = 300
    rio_obj = rast_manager.rescale(cell_size)
    assert rast_manager.get_affine()[2] == rio_obj.transform[2]
    assert rast_manager.get_affine()[5] == rio_obj.transform[5]
    assert math.isclose(
        rio_obj.transform[0],
        cell_size,
        rel_tol=0.005
    )
    rast_manager_1 = RasterManager.from_path(habitat_tif)
    rast_manager_2 = RasterManager.from_path(habitat_shift_tif)
    rio_obj_match_1 = rast_manager_1.match_extent(rast_manager_2)
    rio_obj_match_2 = rast_manager_2.match_extent(rast_manager_1)
    assert rio_obj_match_1.transform[2] == rio_obj_match_2.transform[2]
    assert rio_obj_match_1.transform[5] == rio_obj_match_2.transform[5]
