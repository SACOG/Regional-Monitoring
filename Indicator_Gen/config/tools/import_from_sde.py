

'''
Code to import GIS data directly from the SDE
User needs to adjust SQL Query as needed
User must specify all columns needed in select statement
User must specify the geometry column as WKB (Shape.STAsBinary() AS geometry, where "Shape" is the geometry column alias in the SDE table)
'''


DB = 'GISData'
SQL_QUERY = """
            SELECT
                JURIS, COUNTY,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.CITY_COUNTY
            """
## In the above example:
# "Shape" is the name of the geometry field
# "Shape.STSrid AS srid" ensures the CRS also gets imported into Python


import geopandas as gpd
import re
from time import perf_counter as perf
import pyodbc
import urllib
import sqlalchemy as sqla
from IPython.display import display

def get_odbc_driver():
    
    print()
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

def sqlqry_to_gdf(query_str, dbname, servername='SQL-SVR', trustedconn='yes'):

    print()
    driver = get_odbc_driver()  

    conn_str = f"DRIVER={driver};" \
        f"SERVER={servername};" \
        f"DATABASE={dbname};" \
        f"Trusted_Connection={trustedconn}"

    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    start_time = perf()

    print("Executing query. Results loading into dataframe...")
    gdf = gpd.read_postgis(query_str, engine, geom_col="geometry")
    srid = int(gdf["srid"].iloc[0])
    gdf = gdf.set_crs(epsg=srid)
    gdf = gdf.drop('srid', axis=1)

    rowcnt = gdf.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe."); print()
    display(gdf); print()

    return gdf



if __name__=='__main__':

    gdf = sqlqry_to_gdf(SQL_QUERY, DB, servername='SQL-SVR', trustedconn='yes')
