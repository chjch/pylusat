# pylusat changelog

## 0.3.1

2021-03-28

### Updated

- `density.of_line` - when buffering around polygon `input_gdf` with a distance
  equal to the search radius, instead of using the original shapes, the tool
  now uses the centroids of the original polygons. This is in line with the
  ArcGIS `line density` function.
  
### Improved

- `geotools.spatial_join` - able to handle _spatial join_ of two layers with
  same column names by relying on the indices of the columns of `target_gdf`
  rather than their names

## 0.3.0

2021-02-07

### Added

- `utils.ahp` - Function added to perform AHP based on pre-defined reciprocal
  matrix.
  
### Updated

- `utils.random_ahp` - The previous `random_ahp_weight` is changed to
  `random_ahp` now. 

## 0.2.7

2021-02-01

### Improved

- `reclassify` - Loosened the requirement of ascending old value intervals. 
  Allow identical entries in new values. 

## 0.2.6

2021-01-26

### Improved

- `zonal_stats_raster` - Added `drop=True` to `reset_index`, so no pre-defined
  index name was used for the joined output of zone_gdf and zonal_stats output. 
  This will solve the problem caused by iterating zonal_stats multiple times. 

## 0.2.5

2021-01-25

### Updated

- `zonal stats` - the tool now allows users to specify a string as the prefix
  for the column name(s) of the generated statistics.

## 0.2.4

2021-01-18

### Fixed

- `select by location` - the tool now only output features met the specified
  spatial relationship.