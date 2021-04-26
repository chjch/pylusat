import os
import geopandas as gpd
from pylusat.density import of_point, of_line
import unittest


class TestDensity(unittest.TestCase):

    schools = "schools/schools.shp"     # point geometry
    highway = "highway/highway.shp"     # line geometry
    acs2016 = "acs2016/acs2016.shp"     # polygon geometry
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    schools_shp = os.path.join(dataset_path, schools)
    highway_shp = os.path.join(dataset_path, highway)
    acs2016_shp = os.path.join(dataset_path, acs2016)
    habitat_tif = os.path.join(dataset_path, habitat)

    schools_enrollment = 'ENROLLMENT'

    @classmethod
    def setUpClass(cls):
        cls.schools_gdf = gpd.read_file(cls.schools_shp)
        cls.highway_gdf = gpd.read_file(cls.highway_shp)
        cls.acs2016_gdf = gpd.read_file(cls.acs2016_shp)

    def test_of_point_no_search(self):
        of_point(self.acs2016_gdf, self.schools_gdf)

    def test_of_point_search(self):
        of_point(self.acs2016_gdf, self.schools_gdf, '1 mile', 'acre',
                 self.schools_enrollment)

    def test_of_line(self):
        of_line(self.acs2016_gdf, self.highway_gdf, search_radius='1 mile')


if __name__ == "__main__":
    unittest.main()
