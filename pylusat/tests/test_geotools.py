import os
import geopandas as gpd
from pylusat.geotools import spatial_join
import unittest


class TestGeoTools(unittest.TestCase):

    schools = "schools.shp"     # point geometry
    highway = "highway.shp"     # line geometry
    acs2016 = "acs2016.shp"     # polygon geometry
    habitat = "habitat.tif"     # raster data (tiff)
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    schools_shp = os.path.join(dataset_path, "schools", schools)
    highway_shp = os.path.join(dataset_path, "highway", highway)
    acs2016_shp = os.path.join(dataset_path, "acs2016", acs2016)
    habitat_tif = os.path.join(dataset_path, "habitat", habitat)

    @classmethod
    def setUpClass(cls):
        cls.schools_gdf = gpd.read_file(cls.schools_shp)
        cls.highway_gdf = gpd.read_file(cls.highway_shp)
        cls.acs2016_gdf = gpd.read_file(cls.acs2016_shp)

    def test_spatial_join(self):
        print(spatial_join(self.acs2016_gdf, self.schools_gdf))


if __name__ == "__main__":
    unittest.main()
