

'''

Accessibility analysis for Valley Vision requires population data across service area in raster format
This code:
(1) Imports processed ACS 5 year estimates for population (table B03002 - imported using the MnR data pipeline tools)
(2) Imports a cleaned tigerline geojson file of block groups throughout the 8 county Valley Vision service area
(3) Merges population data onto the block group geojson
(4) Exports as shapefile so that we can manually upload shapefile to Conveyal and convert to tiff format

Read in block group population table
Reshape table from long to wide so that there is only one row per block group and one column for each population by race/eth for the latest year
Read in block group shapefile
Merge on block group GEOID, the population table onto the block group shapefile
Export as shapefile
Export as filegdb


'''


# Workspace ----------------------------------------------------------------------------------------------------------------------------------------------------------

from pathlib import Path
import pandas as pd
import geopandas as gpd
import os
import re
from IPython.display import display
import warnings
warnings.filterwarnings('ignore')




def re_remove_post(x, exp = '.'):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[0]

def clean_fips(df_acs):

    df_acs['Block Group ID'] = df_acs['Block Group ID'].fillna(0)
    df_acs['Block Group ID'] = df_acs['Block Group ID'].astype(str).apply(re_remove_post)

    df_acs['State FIPS'    ] = df_acs['State FIPS'    ].astype(str).apply('{:0>2}'.format)
    df_acs['County FIPS'   ] = df_acs['County FIPS'   ].astype(str).apply('{:0>3}'.format)
    df_acs['Tract ID'      ] = df_acs['Tract ID'      ].astype(str).apply('{:0>6}'.format)
    df_acs['Block Group ID'] = df_acs['Block Group ID'].astype(str)

    df_acs['Census Tract'] = df_acs['State FIPS'] + df_acs['County FIPS'] + df_acs['Tract ID']
    df_acs['GEOID'       ] = df_acs['State FIPS'] + df_acs['County FIPS'] + df_acs['Tract ID'] + df_acs['Block Group ID']
    df_acs['GEOID'] = df_acs['GEOID'].astype('int64')

    return df_acs

def reshape_acs_table(df_acs):
    df_acs = df_acs.sort_values(['GEOID', 'Year'], ascending=[True,False])
    df_acs = df_acs.drop_duplicates(['GEOID', 'Race_Ethnicity'])
    df_acs = df_acs[['GEOID', 'Race_Ethnicity', 'Population']]
    df_acs = df_acs.pivot_table(index='GEOID', columns='Race_Ethnicity', values='Population').reset_index()
    return df_acs

def import_acs_table(file_acs):
    print('\n'*2)
    print('Importing/processing excel or csv file to merge onto the geospatial layer...')
    df_acs = pd.read_excel(file_acs, sheet_name='Block Groups')
    df_acs = clean_fips(df_acs)
    df_acs = reshape_acs_table(df_acs)
    return df_acs

def import_bg_vv(file_shp):
    print('Importing cleaned TIGER shapefile for ValleyVision service area...')
    gdf_bg = gpd.read_file(file_shp)
    gdf_bg = gdf_bg.to_crs("EPSG:4326")
    gdf_bg = gdf_bg[['GEOID', 'geometry']]
    return gdf_bg

def combine_acs_vv(df_acs, gdf_bg):

    print('Combining ACS data with the Valley Vision block groups...')
    gdf_bg_acs = gdf_bg.merge(df_acs, on='GEOID', how='left')

    gdf_bg_acs.columns = [x.lower() for x in gdf_bg_acs.columns]
    gdf_bg_acs.columns = [re.sub('[^\\w\\s]', '_', col.strip()) for col in gdf_bg_acs.columns]
    gdf_bg_acs.columns = [re.sub('[\s+]'    , '_', col.strip()) for col in gdf_bg_acs.columns]
    gdf_bg_acs.columns = [re.sub('\\?'      , '' , col.strip()) for col in gdf_bg_acs.columns]

    gdf_bg_acs = gdf_bg_acs[['all', 'asian__nh_', 'black_or_african_american__nh_', 'hispanic_or_latino', 'white__nh_', 'geometry']]
    gdf_bg_acs.columns = ['all', 'asian_nh', 'black_nh', 'hispanic', 'white_nh', 'geometry']
    gdf_bg_acs = gdf_bg_acs.fillna(0)

    print()
    print('Final result:')
    display(gdf_bg_acs.head())
    print()

    return gdf_bg_acs

def export_shp(gdf_bg_acs, file_shp):
        print('\n'*2)
        print('Exporting to shp...')
        os.makedirs(file_shp.parent, exist_ok=True)
        gdf_bg_acs.to_file(file_shp)
        print('Successfully EXPORTed shp')
        print('\n'*2)



# Main --------------------------------------------------------------------------------------------------------------------------------------------------------------------



EXPORT=False

FILE_IN_ACS = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Products\CERF\We Prosper Together\Population') / 'Pop_3 Block Groups ACS5_ValleyVision.xlsx'
FILE_IN_SHP = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\geojson') / 'tl_2020_valleyvision_bg.geojson'
FILE_OUT_SHP = Path(r'I:\Projects\Josh\Regional Monitoring\Accessibility\shp') / "pop3_bg_ValleyVision"


if __name__ == '__main__':

    df_acs = import_acs_table(FILE_IN_ACS)
    gdf_bg = import_bg_vv(FILE_IN_SHP)
    gdf_bg_acs = combine_acs_vv(df_acs, gdf_bg)

    if EXPORT:
        export_shp(gdf_bg_acs, FILE_OUT_SHP)



