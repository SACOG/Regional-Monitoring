



## Preparing workspace ---------------------------------------------------------------------------

# Importing packages
import pandas as pd
import numpy as np
import geopandas as gpd
import os
from IPython.display import display
# from shapely import wkb
# from lonboard import Map, PolygonLayer
# from lonboard.colormap import apply_categorical_cmap


# File path for importing SACOG region spatial layer
path_geo = r'I:/Projects/Josh/RHNA/Geospatial Data'
# Currently the data is located in the I drive, but you may not have access
# I moved it over to SP and sent you the SP location
# Replace that file path above with the SP file location on your OneDrive, like you've done for Monitoring and Reporting


## Convert Cragslist locations file to point layer -----------------------------------------------------

print(''); print('')
print('Converting/exporting Craigslist results to shapefile...')

df_craigslist_results = pd.read_csv(os.path.join(path_geo, 'Craigslist Listings V1.csv'))

df = df_craigslist_results.copy()

df = df[~df['latitude' ].isna()]
df = df[~df['longitude'].isna()]
df = df.reset_index(names = 'unique_id')

geometry = gpd.points_from_xy(df['longitude'], df['latitude'])
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326") # Note on EPSG:4326 - I'm assuming this is the coordinate reference system that Craiglist is using when providing coordinates
gdf = gdf.to_crs("EPSG:2226") # EPSG:2226 - the coordinate reference system that SACOG uses for all maps



## Subset Craiglist results to SACOG counties region --------------------------------------------------

print('Intersecting point layer with SACOG counties boundaries...')
print(''); print('')

gdf_counties = gpd.read_file(os.path.join(path_geo, 'tl_2022_us_county_SACOG.geojson'))
gdf_counties = gdf_counties[['COUNTYFP', 'NAME', 'geometry']]
gdf_counties = gdf_counties.to_crs(crs="EPSG:2226")


df_sub = df_craigslist_results.copy()

gdf_sub = gdf[['unique_id', 'geometry']]
gdf_int = gpd.overlay(gdf_sub, gdf_counties, how='intersection')

df  = df [df ['unique_id'].isin(gdf_int['unique_id'].values)]
gdf = gdf[gdf['unique_id'].isin(gdf_int['unique_id'].values)]

df  = df .reset_index(drop=True)
gdf = gdf.reset_index(drop=True)


## Final result ------------------------------------------------------------------------------------

## Final pandas dataframe and geopandas dataframe should only have Craigslist results for locations within the SACOG region
# The dataframe is probably all we need
# But let's keep the geopandas dataframe too incase we want to map this out (would be cool)
display(df .head())
display(gdf.head())



## TODO:

# (1) Write code to export the data
# This will involve appending/deduping weekly updates to two master files (the pandas dataframe [excel or csv] and the geopandas dataframe [geojson or shapefile])
# So we can keep track of this data over time

# (2) Research whether this process can also work with zillow.com, realtor.com, apartments.com, etc...
# Not sure if web-scraping will work for these other sites, they might not enjoy people taking their data for free
# If it is possible, let's adapt the code to work with them, starting with Zillow
