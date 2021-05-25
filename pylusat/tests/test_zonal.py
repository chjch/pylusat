import os
import geopandas as gpd
from pylusat.zonal import zonal_stats_raster
import unittest


class TestZonal(unittest.TestCase):

    acs2016 = "acs2016/acs2016.shp"     # polygon geometry
    habitat = "habitat/habitat.tif"     # raster data (tiff)
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    acs2016_shp = os.path.join(dataset_path, acs2016)
    habitat_tif = os.path.join(dataset_path, habitat)

    @classmethod
    def setUpClass(cls):
        cls.acs2016_gdf = gpd.read_file(cls.acs2016_shp)

    def test_zonal_stats_raster(self):
        zonal_stats_raster(self.acs2016_gdf, self.habitat_tif)


if __name__ == "__main__":
    unittest.main()
