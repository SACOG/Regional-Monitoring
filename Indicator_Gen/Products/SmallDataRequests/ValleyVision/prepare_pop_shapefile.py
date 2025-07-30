


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


export=False



if __name__ == '__main__':

    print(); print()
    print('Importing/processing excel or csv file to merge onto the geospatial layer...')
    path_in = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Products\CERF\We Prosper Together\Population')
    wkbook = 'Pop_3 Block Groups ACS5_ValleyVision.xlsx'
    sheet_name = 'Block Groups'
    file_in = path_in / wkbook
    df = pd.read_excel(file_in, sheet_name=sheet_name)

    df['Block Group ID'] = df['Block Group ID'].fillna(0)
    df['Block Group ID'] = df['Block Group ID'].astype(str).apply(re_remove_post)


    df['State FIPS'    ] = df['State FIPS'    ].astype(str).apply('{:0>2}'.format)
    df['County FIPS'   ] = df['County FIPS'   ].astype(str).apply('{:0>3}'.format)
    df['Tract ID'      ] = df['Tract ID'      ].astype(str).apply('{:0>6}'.format)
    df['Block Group ID'] = df['Block Group ID'].astype(str)

    df['Census Tract'] = df['State FIPS'] + df['County FIPS'] + df['Tract ID']
    df['GEOID'       ] = df['State FIPS'] + df['County FIPS'] + df['Tract ID'] + df['Block Group ID']
    df['GEOID'] = df['GEOID'].astype('int64')


    df = df.sort_values(['GEOID', 'Year'], ascending=[True,False])
    df = df.drop_duplicates(['GEOID', 'Race_Ethnicity'])
    df = df[['GEOID', 'Race_Ethnicity', 'Population']]

    df = df.pivot_table(index='GEOID', columns='Race_Ethnicity', values='Population').reset_index()


    print(); print()
    print('Importing/processing geospatial layer...')
    path_shp = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\geojson')
    shpname = 'tl_2020_valleyvision_bg.geojson'
    file_shp = path_shp / shpname
    gdf_bg = gpd.read_file(file_shp)
    gdf_bg = gdf_bg.to_crs("EPSG:4326")


    gdf_bg = gdf_bg[['GEOID', 'geometry']]

    gdf_bg = gdf_bg.merge(df, on='GEOID', how='left')

    gdf_bg.columns = [x.lower() for x in gdf_bg.columns]
    gdf_bg.columns = [re.sub('[^\\w\\s]', '_', col.strip()) for col in gdf_bg.columns]
    gdf_bg.columns = [re.sub('[\s+]'    , '_', col.strip()) for col in gdf_bg.columns]
    gdf_bg.columns = [re.sub('\\?'      , '' , col.strip()) for col in gdf_bg.columns]

    gdf_bg = gdf_bg[['all', 'asian__nh_', 'black_or_african_american__nh_', 'hispanic_or_latino', 'white__nh_', 'geometry']]
    gdf_bg.columns = ['all', 'asian_nh', 'black_nh', 'hispanic', 'white_nh', 'geometry']
    gdf_bg = gdf_bg.fillna(0)
    display(gdf_bg)



    if export:
        print(); print()
        print('Exporting to shp...')
        path_out = Path(r'I:\Projects\Josh\Regional Monitoring\Accessibility\shp')
        shp_out = "pop3_bg_ValleyVision"
        file_shp = path_out / shp_out
        os.makedirs(file_shp, exist_ok=True)
        file_shp_out = file_shp / f'{shp_out}.shp'
        gdf_bg.to_file(file_shp_out)
        print('Successfully exported shp')
        print();print()


