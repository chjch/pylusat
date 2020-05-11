import os
import geopandas as gpd
from distance import to_point, to_line, to_cell
import unittest


class TestDistance(unittest.TestCase):

    schools = "schools.shp"     # point geometry
    highway = "highway.shp"     # line geometry
    acs2016 = "acs2016.shp"     # polygon geometry
    habitat = "habitat.tif"     # raster data (tiff)
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    schools_shp = os.path.join(dataset_path, schools)
    highway_shp = os.path.join(dataset_path, highway)
    acs2016_shp = os.path.join(dataset_path, acs2016)
    habitat_tif = os.path.join(dataset_path, habitat)

    @classmethod
    def setUpClass(cls):
        cls.schools_gdf = gpd.read_file(cls.schools_shp)
        cls.highway_gdf = gpd.read_file(cls.highway_shp)
        cls.acs2016_gdf = gpd.read_file(cls.acs2016_shp)

    def test_to_point(self):
        to_point(self.acs2016_gdf, self.schools_gdf)

    def test_to_line(self):
        to_line(self.acs2016_gdf, self.highway_gdf)

    def test_to_cell(self):
        to_cell(self.acs2016_gdf, self.habitat_tif, 6)


if __name__ == "__main__":
    unittest.main()
