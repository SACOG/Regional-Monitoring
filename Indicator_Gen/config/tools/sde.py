
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


sql_sacog = """
            SELECT
                Name, Year, Type,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.SACOG_PlanningArea_Census2020
            """
sql_juris = """
            SELECT
                COUNTY, JURIS,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.City_County
            """
sql_county = """
            SELECT
                COUNTYFP, NAME,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.T2020_Census_County_Region
            """
sql_bg = """
            SELECT
                GEOCODE AS GEOID_BG,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.T2020_Census_Block_Groups_SACOG_Region
            """
sql_tract = """
            SELECT
                GEOCODE AS GEOID_tract,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.T2020_Census_Tracts_SACOG_Region
            """
sql_parcel = """
            SELECT
                UNIQUE_PAR_ID, Main_APN, Landuse_code, Main_address,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.Master_Parcel_Region
            """
sql_hospitals = """
            SELECT
                OBJECTID, AGENCY, ADDRESS,
                CITY, COUNTY, STATE, ZIP,
                EMP05, SOURCE, Lat, Long,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.Hospitals
            """
sql_collisions = """
            SELECT
                CASE_ID, ACCIDENT_YEAR, COUNTY, CITY,
                ColSeverity, BikePed, DAC_EPC, SACOG,
                NUMBER_KILLED, COUNT_SEVERE_INJ,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.Collision_SACOG_Region
            """


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


def sqlqry_to_df(query_str):   

    driver = get_odbc_driver()

    conn_str = f"DRIVER={driver};" \
        f"SERVER={SERVERNAME};" \
        f"DATABASE={DB};" \
        f"Trusted_Connection={TRUSTEDCONN}" \
        f"Encrypt={ENCRYPT};" \
        f"TrustServerCertificate={TRUSTEDCERT};"
        
    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")
       
    start_time = perf()

    # create SQL table from the dataframe
    print("\nExecuting query. Results loading into dataframe...")
    df = pd.read_sql_query(sql=query_str, con=engine)
    rowcnt = df.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")
    
    return df

