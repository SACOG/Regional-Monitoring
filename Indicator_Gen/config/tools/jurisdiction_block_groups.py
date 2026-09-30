
from pathlib import Path
import re
import urllib
from time import perf_counter as perf

import geopandas as gpd
import pandas as pd
import pyodbc
import sqlalchemy as sqla

DB='GISData'
SERVERNAME='SQL-SVR'
TRUSTEDCONN='yes'
ENCRYPT='yes'
TRUSTEDCERT='yes'

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


def sqlqry_to_gdf(query_str):

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


SQL_JURIS = """
            SELECT
                COUNTY, JURIS,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.City_County
            """

SQL_BG_2020 = """
            SELECT
                GEOCODE AS GEOID,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.T2020_Census_Block_Groups_SACOG_Region
            """


SQL_BG_2010 = """
            SELECT
                GEOID10 AS GEOID,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.BlockGroups2010
            """


path_out = r'I:\Projects\Josh\Geospatial Data\crosswalks'

if __name__=='__main__':

    gdf_juris = sqlqry_to_gdf(SQL_JURIS)
    gdf_bg_2020 = sqlqry_to_gdf(SQL_BG_2020)
    gdf_bg_2010 = sqlqry_to_gdf(SQL_BG_2010)

    gdf_juris_bg_2020 = gpd.overlay(gdf_juris, gdf_bg_2020)
    gdf_juris_bg_2010 = gpd.overlay(gdf_juris, gdf_bg_2010)


    df_juris_bg_2020 = gdf_juris_bg_2020.drop('geometry', axis=1)
    df_juris_bg_2010 = gdf_juris_bg_2010.drop('geometry', axis=1)


    df_juris_bg_2020 = df_juris_bg_2020.sort_values(['COUNTY', 'JURIS', 'GEOID'])
    df_juris_bg_2010 = df_juris_bg_2010.sort_values(['COUNTY', 'JURIS', 'GEOID'])


    with pd.ExcelWriter(Path(path_out) / 'jurisdictions_to_blockgroups.xlsx', engine='xlsxwriter') as writer:
        df_juris_bg_2020.to_excel(writer, index=False, sheet_name='2020')
        df_juris_bg_2010.to_excel(writer, index=False, sheet_name='2010')

