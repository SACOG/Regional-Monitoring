

## Packages ---

import pandas as pd
import geopandas as gpd
from arcgis.features import GeoAccessor, GeoSeriesAccessor
import getpass
from pathlib import Path
from tqdm import tqdm
from datetime import date
from IPython.display import display


## File paths ---

path_arcpro = Path(r"I:\Projects\Josh\Regional Monitoring\ArcPro_sup\Cap to Cap")



## Convert shp to feature class file geodatabase ---

# geos = ['place', 'tract', 'bg', 'block']

# for geo in tqdm(geos):
#     file_va = path_arcpro / '_data' / f'tl_2020_51_{geo}' / f'tl_2020_51_{geo}.shp'
#     gdf_va = gpd.read_file(file_va)
#     gdf_va = gdf_va.to_crs("EPSG:2284")

#     sdf_va=GeoAccessor.from_geodataframe(gdf_va, column_name="geometry")

#     file_featureclass = path_arcpro / 'CapToCap.gdb' / f'tiger_VA_{geo}'
#     sdf_va.spatial.to_featureclass(location=file_featureclass)


## Then in ArcPro:
# Selected CDPs of interest and exported to feature class
# Used new feature class to select blocks, block groups, and census tracts and exported to feature class
## Next:
# Use jupyter notebook file to import all cap feature classes and ACS data, then combine and summarize


## MSA's too, why not

file_msa = path_arcpro / '_data' / 'tl_2020_us_cbsa' / 'tl_2020_us_cbsa.shp'
gdf_msa = gpd.read_file(file_msa)
gdf_msa = gdf_msa.to_crs("EPSG:2284")

sdf_msa=GeoAccessor.from_geodataframe(gdf_msa, column_name="geometry")

file_featureclass = path_arcpro / 'CapToCap.gdb' / f'tiger_us_msa'
sdf_msa.spatial.to_featureclass(location=file_featureclass)