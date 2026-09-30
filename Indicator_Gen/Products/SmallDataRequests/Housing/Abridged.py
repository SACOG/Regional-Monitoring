
'''

This python file copies the AffordableHousing layer from the SDE to excel export for a newspaper outlet (i think)


EMAIL:
Hi Josh and Craig,
Dov, Mia, and I met with a reporter from Abridged this morning to discuss regional housing production trends, particularly the increase in multifamily housing and the shift in where that growth is occurring
The reporter is working on a story that will feature SACOG housing data, and he is planning to develop some of his own graphics. He is also interested in more granular data, if available.
Could you please help with the following?

Jurisdiction-level data: Provide the source data behind the Regional Housing Permits dashboard in an Excel file with housing production data by jurisdiction, year, and housing product type. Ideally, this would be the same dataset used to populate the dashboard, including annual unit totals by product type.
Data definitions: Where is SACOG including ADUs? Dov and I discussed whether they are included in the single-family small-lot category or reported separately, but we would like to verify the current methodology.
Green Zone data: If you have access to the underlying Green Means Go housing production data, could you help verify the reported increase in housing permits within Green Zones over the past five years and the share of recent production that is attached housing? Dov referenced a 300% increase, but we would like to confirm the figures and reporting period.
Definitions: The reporter is comparing our data with Census and Colliers data, so we want to clearly explain any differences in methodology, such as permits issued vs. completed units.
Multifamily details: Do you have any sources on multifamily affordable versus market-rate housing breakdown?

We committed to providing him what we have available by next Wednesday. @Mia Lopez, did I miss or mischaracterize anything?
Thanks for your help.

Becky


NOTE:
SubsidizedHousing GIS data source
https://gis.hcd.ca.gov/arcgis/rest/services/Hosted/Subsidized_Housing_CHPC_2023/FeatureServer/2



'''


import geopandas as gpd
import re
import urllib
from time import perf_counter as perf

import geopandas as gpd
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


def get_coords_from_geometry(gdf):
    if gdf.crs != 4326:
        gdf = gdf.to_crs('EPSG:4326')
    gdf['Longitude'] = gdf.geometry.x
    gdf['Latitude' ] = gdf.geometry.y
    return gdf


def convert_sde_fc_to_xlsx(query_str, file_xlsx):

    '''
    Function to convert a feature class in a file geodatabase to a shapefile

    Parameters:
    query_str       - string = SQL query used to import data from SDE
    file_xlsx       - string = file path of where to export csv file
    crs             - string = desired CRS of output feature class
    '''

    print(f'\n\nImporting Affordable Housing feature class from the SDE...\n\n')
    gdf = sqlqry_to_gdf(query_str)

    if gdf.crs != 4326:
        gdf = gdf.to_crs(4326)

    gdf = get_coords_from_geometry(gdf)
    gdf = gdf.drop('geometry', axis=1)

    print(f'Exporting Subsidized Housing feature class to excel at: {str(file_xlsx)}...')
    gdf.to_excel(file_xlsx, sheet_name='SubsidizedHousing', index=False)
    print('Done!\n\n')



if __name__ == '__main__':


    sql_query_affordable = """
                SELECT
                    PROPERTY, COUNTY, ADDRESS, JURISDICTION, ZIP,
                    UNITS, SUBSIDIZED, PROGRAM_TYPE, FINANCING, SOURCE,
                    COMMENTS, TYPE, YR_BUILT, CONST_TYPE,
                    Shape.STAsBinary() AS geometry,
                    Shape.STSrid AS srid
                FROM gisowner.AffordableHousing
                """

    sql_query_subsidized = """
                SELECT
                    user_universal_id AS Universal_ID,
                    user_clean_address AS Street_Address,
                    user_city AS City,
                    user_zip AS Zip,
                    user_county AS County,
                    user_affordable_units AS Affordable_Units,
                    user_total_units AS Total_Units,
                    user_active_program_s_ AS Active_Programs,
                    affordability_end_year AS Estimated_Affordability_End_Date, 
                    user_risk_level AS Risk_Level,
                    user_notes AS Notes, user_name AS Name,
                    Shape.STAsBinary() AS geometry,
                    Shape.STSrid AS srid
                FROM gisowner.SubsidizedHousing
                """

    file_xlsx = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Products\Small Data Requests\2026\Abridged\SubsidizedHousing_Abridged.xlsx'

    convert_sde_fc_to_xlsx(sql_query_subsidized, file_xlsx)


