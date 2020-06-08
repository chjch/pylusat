import os
import geopandas as gpd
from pylusat.interpolate import idw
import unittest


class TestInterpolate(unittest.TestCase):

    schools = "schools"     # point geometry
    acs2016 = "acs2016"     # polygon geometry
    dataset_path = os.path.join(os.path.dirname(os.getcwd()), "datasets")

    schools_shp = os.path.join(dataset_path, schools, f'{schools}.shp')
    acs2016_shp = os.path.join(dataset_path, acs2016, f'{acs2016}.shp')

    @classmethod
    def setUpClass(cls):
        cls.schools_gdf = gpd.read_file(cls.schools_shp)
        cls.acs2016_gdf = gpd.read_file(cls.acs2016_shp)

    def test_idw(self):
        idw(self.acs2016_gdf, self.schools_gdf, 'ENROLLMENT',
            power=2.00, n_neighbor=12)


if __name__ == "__main__":
    unittest.main()
