

'''
Accessibility analysis for SACOG requires population data across service area in raster format

This code:
(1) Imports processed ACS 5 year estimates for population (table B03002 - imported using the MnR data pipeline tools)
(2) Imports the latest block groups file throughout the 6 county SACOG planning area, feature class located on the SDE
(3) Joins block group population data with the block groups geometries
(4) Exports as shapefile so that we can manually upload shapefile to Conveyal and convert to tiff format

'''



# Setup ----------------------------------------------------------------------------------------------------------------------------------------------------------

from pathlib import Path
import pandas as pd
import geopandas as gpd
import os
import re
import urllib
from time import perf_counter as perf
import pyodbc
import sqlalchemy as sqla
from IPython.display import display
import warnings
warnings.filterwarnings('ignore')


## SQL stuff ---

DB='GISData'
SERVERNAME='SQL-SVR'
TRUSTEDCONN='yes'
ENCRYPT='yes'
TRUSTEDCERT='yes'


def sqlqry_to_gdf(query_str):

    def get_odbc_driver():
        
        # gets name of ODBC driver, with name "ODBC Driver <version> for SQL Server"
        drivers = [d for d in pyodbc.drivers() if 'ODBC Driver ' in d]

        if len(drivers) == 0:
            errmsg = f"ERROR. No usable ODBC Driver found for SQL Server." \
            f"drivers found include {drivers}. Check ODBC Administrator program" \
            "for more information."

            raise Exception (errmsg)
        else:
            d_versions = [re.findall('\d+', dv)[0] for dv in drivers] # [re.findall('\d+', dv)[0] for dv in drivers]
            latest_version = max([int(v) for v in d_versions])
            driver = f"ODBC Driver {latest_version} for SQL Server"

            return driver

    driver = get_odbc_driver()

    conn_str = f"DRIVER={driver};" \
        f"SERVER={SERVERNAME};" \
        f"DATABASE={DB};" \
        f"Trusted_Connection={TRUSTEDCONN};" \
        f"Encrypt={ENCRYPT};" \
        f"TrustServerCertificate={TRUSTEDCERT};"

    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    start_time = perf()

    print("\nExecuting query. Results loading into dataframe...")
    gdf = gpd.read_postgis(query_str, engine, geom_col="geometry")
    srid = int(gdf["srid"].iloc[0])
    gdf = gdf.set_crs(epsg=srid)
    gdf = gdf.drop('srid', axis=1)

    rowcnt = gdf.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")

    return gdf


## Dataframe stuff ---

def re_remove_post(x, exp = '.'):
    try:
        x.split(exp, 1)[0]
    except:
        pass
    return x

def clean_fips(df_acs):

    df_acs['Block Group ID'] = df_acs['Block Group ID'].fillna(0)
    df_acs['Block Group ID'] = df_acs['Block Group ID'].astype(str).apply(re_remove_post)

    df_acs['State FIPS'    ] = df_acs['State FIPS'    ].astype(str).apply('{:0>2}'.format)
    df_acs['County FIPS'   ] = df_acs['County FIPS'   ].astype(str).apply('{:0>3}'.format)
    df_acs['Tract ID'      ] = df_acs['Tract ID'      ].astype(str).apply('{:0>6}'.format)
    df_acs['Block Group ID'] = df_acs['Block Group ID'].astype(str)

    df_acs['Census Tract'] = df_acs['State FIPS'] + df_acs['County FIPS'] + df_acs['Tract ID']
    df_acs['GEOID'       ] = df_acs['State FIPS'] + df_acs['County FIPS'] + df_acs['Tract ID'] + df_acs['Block Group ID']
    df_acs['GEOID'] = df_acs['GEOID'].str[:-2].astype('int64')

    return df_acs

def reshape_acs_table(df_acs):
    df_acs = df_acs.sort_values(['GEOID', 'Year'], ascending=[True,False])
    df_acs = df_acs.drop_duplicates(['GEOID', 'Race/Ethnicity'])
    df_acs = df_acs[['GEOID', 'Race/Ethnicity', 'Population']]
    df_acs = df_acs.pivot_table(index='GEOID', columns='Race/Ethnicity', values='Population').reset_index()
    return df_acs

def import_acs_table(file_acs):
    print('\n\nImporting/processing excel or csv file to merge onto the geospatial layer...')
    df_acs = pd.read_excel(file_acs, sheet_name='Block Groups')
    df_acs = clean_fips(df_acs)
    df_acs = reshape_acs_table(df_acs)
    return df_acs

def combine_acs(df_acs, gdf_bg):

    print('Combining ACS data with the SACOG block groups...')
    gdf_bg_acs = gdf_bg.merge(df_acs, on='GEOID', how='left')

    gdf_bg_acs.columns = [x.lower() for x in gdf_bg_acs.columns]
    gdf_bg_acs.columns = [re.sub('[^\\w\\s]', '_', col.strip()) for col in gdf_bg_acs.columns]
    gdf_bg_acs.columns = [re.sub('[\s+]'    , '_', col.strip()) for col in gdf_bg_acs.columns]
    gdf_bg_acs.columns = [re.sub('\\?'      , '' , col.strip()) for col in gdf_bg_acs.columns]

    gdf_bg_acs = gdf_bg_acs[['all', 'asian__nh_', 'black_or_african_american__nh_', 'hispanic_or_latino', 'white__nh_', 'geometry']]
    gdf_bg_acs.columns = ['all', 'asian_nh', 'black_nh', 'hispanic', 'white_nh', 'geometry']
    gdf_bg_acs = gdf_bg_acs.fillna(0)

    print('\nFinal result:')
    display(gdf_bg_acs.head())

    return gdf_bg_acs

def export_shp(gdf_bg_acs, file_shp):
        print('\n\nExporting to shp...')
        os.makedirs(file_shp.parent, exist_ok=True)
        gdf_bg_acs.to_file(file_shp, engine='pyogrio')
        print('Successfully EXPORTed shp\n\n')



# Main --------------------------------------------------------------------------------------------------------------------------------------------------------------------



EXPORT=True
ACS_YEAR=2024
CRS=4326 # used by Conveyal

FILE_IN_ACS = Path(r'I:\Projects\Josh\Regional Monitoring\weights') / 'Total_Population Block Groups ACS5.xlsx'
if ACS_YEAR>=2020:
    SQL_BG = """
                SELECT
                    GEOCODE AS GEOID,
                    Shape.STAsBinary() AS geometry,
                    Shape.STSrid AS srid
                FROM gisowner.T2020_Census_Block_Groups_SACOG_Region
                """
else:
    SQL_BG = """
            SELECT
                GEOID10 AS GEOID,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.BlockGroups2010
            """
FILE_OUT_SHP = Path(r'I:\Projects\Josh\Conveyal\conveyal_inputs\shp\pop3') / f'pop3_bg_{ACS_YEAR}'



if __name__ == '__main__':

    df_acs = import_acs_table(FILE_IN_ACS)
    gdf_bg = sqlqry_to_gdf(SQL_BG)
    if gdf_bg.crs != CRS:
        gdf_bg = gdf_bg.to_crs(CRS)

    gdf_bg['GEOID'] = gdf_bg['GEOID'].astype('int64')
    gdf_bg_acs = combine_acs(df_acs, gdf_bg)

    if EXPORT:
        export_shp(gdf_bg_acs, FILE_OUT_SHP)

