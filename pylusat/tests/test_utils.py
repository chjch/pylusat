import os
import geopandas as gpd
from pylusat.utils import gridify
import unittest


class TestGeoTools(unittest.TestCase):

    schools = "schools/schools.shp"     # point geometry
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    schools_shp = os.path.join(dataset_path, schools)

    @classmethod
    def setUpClass(cls):
        cls.schools_gdf = gpd.read_file(cls.schools_shp)

    def test_gridify(self):
        gridify(self.schools_gdf, width=1000)


if __name__ == "__main__":
    unittest.main()
