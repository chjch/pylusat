import os
import geopandas as gpd
from pylusat.geotools import spatial_join, select_by_location
import unittest


class TestGeoTools(unittest.TestCase):

    schools = "schools/schools.shp"     # point geometry
    acs2016 = "acs2016/acs2016.shp"     # polygon geometry
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    schools_shp = os.path.join(dataset_path, schools)
    acs2016_shp = os.path.join(dataset_path, acs2016)

    @classmethod
    def setUpClass(cls):
        cls.schools_gdf = gpd.read_file(cls.schools_shp)
        cls.acs2016_gdf = gpd.read_file(cls.acs2016_shp)

    def test_spatial_join(self):
        print(spatial_join(self.acs2016_gdf, self.schools_gdf))

    def test_select_by_location(self):
        select_by_location(self.acs2016_gdf, self.schools_gdf)


if __name__ == "__main__":
    unittest.main()
