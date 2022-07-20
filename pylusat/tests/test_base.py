from pylusat.datasets import get_path
from pylusat.base import RasterManager
import pytest
import math


@pytest.fixture
def habitat_tif():
    return get_path("habitat")


def test_raster_manager(habitat_tif):
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
