




# Setup --------------------------------------------------------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import pandas as pd
import geopandas as gpd
import pyogrio
import re
from time import perf_counter as perf
import pyodbc
import urllib
import sqlalchemy as sqla



DB='GISData'
SERVERNAME='SQL-SVR'
TRUSTEDCONN='yes'
ENCRYPT='yes'
TRUSTEDCERT='yes'


sql_col = """
            SELECT
                CASE_ID, ACCIDENT_YEAR, COUNTY, CITY, DAC_EPC, ColSeverity, Freeway,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.Collision_SACOG_Region
            """

sql_epc = """
            SELECT
                Geographic_Code_Identifier, Population, KD_Trips,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.EquityPriorityCommunity
            """

sql_bg = """
            SELECT
                GEOCODE AS Geographic_Code_Identifier, COUNTY, POP100, EPCarea,
                Shape.STAsBinary() AS geometry,
                Shape.STSrid AS srid
            FROM gisowner.T2024_ACS5yr_Block_Groups_SACOG_Region
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

    print()
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

    print("Executing query. Results loading into dataframe...")
    gdf = gpd.read_postgis(query_str, engine, geom_col="geometry")
    srid = int(gdf["srid"].iloc[0])
    gdf = gdf.set_crs(epsg=srid)
    gdf = gdf.drop('srid', axis=1)

    rowcnt = gdf.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")

    return gdf


def rollup_pop_and_trips(df_epc):

    df_epc_counties = df_epc.groupby(['CountyName', 'Type'], as_index=False).agg(POP=('POP100', 'sum'))#, TRIPS=('KD_Trips', 'sum'))
    df_epc_region   = df_epc.groupby([              'Type'], as_index=False).agg(POP=('POP100', 'sum'))#, TRIPS=('KD_Trips', 'sum'))
    
    df_epc_counties['Pop_Percent'] = df_epc_counties['POP'] / df_epc_counties.groupby(['CountyName'])['POP'].transform('sum')
    df_epc_region  ['Pop_Percent'] = df_epc_region  ['POP'] / df_epc_region['POP'].sum()
    
    # df_epc_counties['Trips_Percent'] = df_epc_counties['TRIPS'] / df_epc_counties.groupby(['CountyName'])['TRIPS'].transform('sum')
    # df_epc_region  ['Trips_Percent'] = df_epc_region  ['TRIPS'] / df_epc_region['TRIPS'].sum()

    return df_epc_counties, df_epc_region


def rollup_collisions(gdf_col, groupby_cols):
    df_grouped = (
        gdf_col#[gdf_col['Freeway']=='No']
            .groupby(groupby_cols, as_index=False) \
            .agg(Collisions=('CASE_ID', 'count')) \
    )
    return df_grouped


def calc_normalized_collisions(df_col):

    df_col['Collisions_per_1k_persons'] = (df_col['Collisions'] / df_col['POP'  ]) * 1000
    # df_col['Collisions_per_1k_trips'  ] = (df_col['Collisions'] / df_col['TRIPS']) * 1000

    return df_col




# Main --------------------------------------------------------------------------------------------------------------------------------------------------------------------------


EXPORT=True

PATH_OUT = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Safe Equitable Resilient Infrastructure\Safety\Safety_3 EJarea'
PATH_SERVER = r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data'

if __name__ == '__main__':

    epc_map_bg = {
        'False': 'Non-EPC',
        'True': 'EPC'
    }
    epc_map_collisions = {
        '0': 'Non-EPC',
        '1': 'EPC'
    }
    counties_map = {
        17.0: 'El Dorado'
        , 61.0: 'Placer'
        , 67.0: 'Sacramento'
        , 101.0: 'Sutter'
        , 113.0: 'Yolo'
        , 115.0: 'Yuba'
    }

    gdf_col = sqlqry_to_gdf(sql_col)
    gdf_epc = sqlqry_to_gdf(sql_bg )
    df_epc = gdf_epc.drop('geometry', axis=1)
    df_epc['Type'      ] = df_epc['EPCarea'].map(epc_map_bg  )
    df_epc['CountyName'] = df_epc['COUNTY' ].map(counties_map)

    df_epc_counties, df_epc_region = rollup_pop_and_trips(df_epc)

    gdf_col['Type'] = gdf_col['DAC_EPC'].map(epc_map_collisions)
    gdf_col['CountyName'] = gdf_col['COUNTY'].str.title()

    df_county = rollup_collisions(gdf_col, ['CountyName', 'ACCIDENT_YEAR', 'ColSeverity', 'Type'])
    df_sev    = rollup_collisions(gdf_col, [              'ACCIDENT_YEAR', 'ColSeverity', 'Type'])
    df_total  = rollup_collisions(gdf_col, [              'ACCIDENT_YEAR',                'Type'])

    df_county = df_county.merge(df_epc_counties, on=['CountyName', 'Type'], how='left')
    df_sev    = df_sev   .merge(df_epc_region  , on=[              'Type'], how='left')
    df_total  = df_total .merge(df_epc_region  , on=[              'Type'], how='left')

    df_county = calc_normalized_collisions(df_county)
    df_sev    = calc_normalized_collisions(df_sev   )
    df_total  = calc_normalized_collisions(df_total )

    df_county['Collisions_Percent'] = df_county['Collisions'] / df_county.groupby(['CountyName', 'ACCIDENT_YEAR', 'ColSeverity'])['Collisions'].transform('sum')
    df_sev   ['Collisions_Percent'] = df_sev   ['Collisions'] / df_sev   .groupby([              'ACCIDENT_YEAR', 'ColSeverity'])['Collisions'].transform('sum')
    df_total ['Collisions_Percent'] = df_total ['Collisions'] / df_total .groupby([              'ACCIDENT_YEAR'               ])['Collisions'].transform('sum')

    df_total['ColSeverity'] = 'All Collisions'
    df_sev = pd.concat([df_sev, df_total])

    df_total  = df_total [df_total ['ACCIDENT_YEAR']<=2025]
    df_sev    = df_sev   [df_sev   ['ACCIDENT_YEAR']<=2025]
    df_county = df_county[df_county['ACCIDENT_YEAR']<=2025]

    if EXPORT:
        for path_ in [PATH_OUT, PATH_SERVER]:
            print(f'\n\nExported to {path_}')
            with pd.ExcelWriter(Path(path_)/'Safety_3 EPC.xlsx', engine='xlsxwriter') as writer:
                df_sev   .to_excel(writer, index=False, sheet_name='Region')
                df_county.to_excel(writer, index=False, sheet_name='County')
            print('\n'*3)






#### V2 --------------------------------------------------------------------------------------------------------------------------------------------------




# # Setup --------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# from pathlib import Path
# import pandas as pd
# import geopandas as gpd
# import pyogrio
# import re
# from time import perf_counter as perf
# import pyodbc
# import urllib
# import sqlalchemy as sqla



# DB='GISData'
# SERVERNAME='SQL-SVR'
# TRUSTEDCONN='yes'
# ENCRYPT='yes'
# TRUSTEDCERT='yes'


# sql_col = """
#             SELECT
#                 CASE_ID, ACCIDENT_YEAR, COUNTY, CITY, DAC_EPC, ColSeverity, Freeway,
#                 Shape.STAsBinary() AS geometry,
#                 Shape.STSrid AS srid
#             FROM gisowner.Collision_SACOG_Region
#             """

# sql_epc = """
#             SELECT
#                 Geographic_Code_Identifier, Population, KD_Trips,
#                 Shape.STAsBinary() AS geometry,
#                 Shape.STSrid AS srid
#             FROM gisowner.EquityPriorityCommunity
#             """

# sql_bg = """
#             SELECT
#                 GEOCODE AS Geographic_Code_Identifier, POP100, 'EPCarea,
#                 Shape.STAsBinary() AS geometry,
#                 Shape.STSrid AS srid
#             FROM gisowner.T2024_ACS5yr_Block_Groups_SACOG_Region
#             """
           

# def get_odbc_driver():
    
#     # gets name of ODBC driver, with name "ODBC Driver <version> for SQL Server"
#     drivers = [d for d in pyodbc.drivers() if 'ODBC Driver ' in d]

#     if len(drivers) == 0:
#         errmsg = f"ERROR. No usable ODBC Driver found for SQL Server." \
#         f"drivers found include {drivers}. Check ODBC Administrator program" \
#         "for more information."

#         raise Exception (errmsg)
#     else:
#         d_versions = [re.findall('\d+', dv)[0] for dv in drivers] # [re.findall('\d+', dv)[0] for dv in drivers]
#         latest_version = max([int(v) for v in d_versions])
#         driver = f"ODBC Driver {latest_version} for SQL Server"

#         return driver


# def sqlqry_to_gdf(query_str):

#     print()
#     driver = get_odbc_driver()

#     conn_str = f"DRIVER={driver};" \
#         f"SERVER={SERVERNAME};" \
#         f"DATABASE={DB};" \
#         f"Trusted_Connection={TRUSTEDCONN};" \
#         f"Encrypt={ENCRYPT};" \
#         f"TrustServerCertificate={TRUSTEDCERT};"

#     conn_str = urllib.parse.quote_plus(conn_str)
#     engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

#     start_time = perf()

#     print("Executing query. Results loading into dataframe...")
#     gdf = gpd.read_postgis(query_str, engine, geom_col="geometry")
#     srid = int(gdf["srid"].iloc[0])
#     gdf = gdf.set_crs(epsg=srid)
#     gdf = gdf.drop('srid', axis=1)

#     rowcnt = gdf.shape[0]
    
#     et_mins = round((perf() - start_time) / 60, 2)
#     print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")

#     return gdf


# def rollup_pop_and_trips(df_epc):

#     df_epc_counties = df_epc.groupby(['CountyName', 'Type'], as_index=False).agg(POP=('Population', 'sum'), TRIPS=('KD_Trips', 'sum'))
#     df_epc_region   = df_epc.groupby([              'Type'], as_index=False).agg(POP=('Population', 'sum'), TRIPS=('KD_Trips', 'sum'))
    
#     df_epc_counties['Pop_Percent'] = df_epc_counties['POP'] / df_epc_counties.groupby(['CountyName'])['POP'].transform('sum')
#     df_epc_region  ['Pop_Percent'] = df_epc_region  ['POP'] / df_epc_region['POP'].sum()
    
#     df_epc_counties['Trips_Percent'] = df_epc_counties['TRIPS'] / df_epc_counties.groupby(['CountyName'])['TRIPS'].transform('sum')
#     df_epc_region  ['Trips_Percent'] = df_epc_region  ['TRIPS'] / df_epc_region['TRIPS'].sum()

#     return df_epc_counties, df_epc_region


# def rollup_collisions(gdf_col, groupby_cols):
#     df_grouped = (
#         gdf_col[gdf_col['Freeway']=='No']
#             .groupby(groupby_cols, as_index=False) \
#             .agg(Collisions=('CASE_ID', 'count')) \
#     )
#     return df_grouped



# def calc_normalized_collisions(df_col):

#     df_col['Collisions_per_1k_persons'] = (df_col['Collisions'] / df_col['POP'  ]) * 1000
#     df_col['Collisions_per_1k_trips'  ] = (df_col['Collisions'] / df_col['TRIPS']) * 1000

#     return df_col



# # Main --------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# PATH_OUT = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Safe Equitable Resilient Infrastructure\Safety\Safety_3 EJarea'
# GDB_EPC = r'I:\DisadvantagedCommunities\EPCs_Data\EPC_BlockGroups.gdb'
# FILE_EPC = 'EPCs_summary'


# if __name__ == '__main__':

#     epc_map = {
#         '0': 'Non-EPC',
#         '1': 'EPC'
#     }

#     gdf_col = sqlqry_to_gdf(sql_col)
#     gdf_epc = gpd.read_file(GDB_EPC, layer=FILE_EPC, engine="pyogrio")
#     df_epc = gdf_epc[['Geographic_Code_Identifier', 'CountyName', 'Type', 'Population', 'KD_Trips']]
#     df_epc['Type'] = df_epc['Type'].fillna('Non-EPC')
#     df_epc.loc[df_epc['Type']=='KD', 'Type'] = 'EPC'

#     df_epc_counties, df_epc_region = rollup_pop_and_trips(df_epc)

#     gdf_col['Type'] = gdf_col['DAC_EPC'].map(epc_map)
#     gdf_col['CountyName'] = gdf_col['COUNTY'].str.title()

#     df_county = rollup_collisions(gdf_col, ['CountyName', 'ACCIDENT_YEAR', 'ColSeverity', 'Type'])
#     df_sev    = rollup_collisions(gdf_col, [              'ACCIDENT_YEAR', 'ColSeverity', 'Type'])
#     df_total  = rollup_collisions(gdf_col, [              'ACCIDENT_YEAR',                'Type'])

#     df_county = df_county.merge(df_epc_counties, on=['CountyName', 'Type'], how='left')
#     df_sev    = df_sev   .merge(df_epc_region  , on=[              'Type'], how='left')
#     df_total  = df_total .merge(df_epc_region  , on=[              'Type'], how='left')

#     df_county = calc_normalized_collisions(df_county)
#     df_sev    = calc_normalized_collisions(df_sev   )
#     df_total  = calc_normalized_collisions(df_total )

#     df_county['Collisions_Percent'] = df_county['Collisions'] / df_county.groupby(['CountyName', 'ACCIDENT_YEAR', 'ColSeverity'])['Collisions'].transform('sum')
#     df_sev   ['Collisions_Percent'] = df_sev   ['Collisions'] / df_sev   .groupby([              'ACCIDENT_YEAR', 'ColSeverity'])['Collisions'].transform('sum')
#     df_total ['Collisions_Percent'] = df_total ['Collisions'] / df_total .groupby([              'ACCIDENT_YEAR'               ])['Collisions'].transform('sum')

#     df_total['ColSeverity'] = 'All Collisions'
#     df_sev = pd.concat([df_sev, df_total])

#     print(f'\n\nExported to {PATH_OUT}')
#     with pd.ExcelWriter(Path(PATH_OUT)/'Safety_3 EPC.xlsx', engine='xlsxwriter') as writer:
#         df_sev   .to_excel(writer, index=False, sheet_name='Region')
#         df_county.to_excel(writer, index=False, sheet_name='County')
#     print('\n'*3)


#     breakpoint()








#### V1 --------------------------------------------------------------------------------------------------------------------------------------------------

# from pathlib import Path
# import pandas as pd
# import geopandas as gpd
# import re
# from time import perf_counter as perf
# import pyodbc
# import urllib
# import sqlalchemy as sqla


# BUFFER_FT = 40
# PATH_OUT = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Safe Equitable Resilient Infrastructure\Safety\Safety_3 EJarea'


# DB='GISData'
# SERVERNAME='SQL-SVR'
# TRUSTEDCONN='yes'
# ENCRYPT='yes'
# TRUSTEDCERT='yes'


# sql_col = """
#             SELECT
#                 CASE_ID, ACCIDENT_YEAR, COUNTY, CITY, DAC_EPC, ColSeverity, Freeway,
#                 Shape.STAsBinary() AS geometry,
#                 Shape.STSrid AS srid
#             FROM gisowner.Collision_SACOG_Region
#             """

# sql_epc = """
#             SELECT
#                 Geographic_Code_Identifier, Population, KD_Trips,
#                 Shape.STAsBinary() AS geometry,
#                 Shape.STSrid AS srid
#             FROM gisowner.EquityPriorityCommunity
#             """

# sql_bg = """
#             SELECT
#                 GEOCODE AS Geographic_Code_Identifier, POP100,
#                 Shape.STAsBinary() AS geometry,
#                 Shape.STSrid AS srid
#             FROM gisowner.T2022_ACS5yr_Block_Groups_SACOG_Region
#             """
           

# def get_odbc_driver():
    
#     # gets name of ODBC driver, with name "ODBC Driver <version> for SQL Server"
#     drivers = [d for d in pyodbc.drivers() if 'ODBC Driver ' in d]

#     if len(drivers) == 0:
#         errmsg = f"ERROR. No usable ODBC Driver found for SQL Server." \
#         f"drivers found include {drivers}. Check ODBC Administrator program" \
#         "for more information."

#         raise Exception (errmsg)
#     else:
#         d_versions = [re.findall('\d+', dv)[0] for dv in drivers] # [re.findall('\d+', dv)[0] for dv in drivers]
#         latest_version = max([int(v) for v in d_versions])
#         driver = f"ODBC Driver {latest_version} for SQL Server"

#         return driver


# def sqlqry_to_gdf(query_str):

#     print()
#     driver = get_odbc_driver()

#     conn_str = f"DRIVER={driver};" \
#         f"SERVER={SERVERNAME};" \
#         f"DATABASE={DB};" \
#         f"Trusted_Connection={TRUSTEDCONN};" \
#         f"Encrypt={ENCRYPT};" \
#         f"TrustServerCertificate={TRUSTEDCERT};"

#     conn_str = urllib.parse.quote_plus(conn_str)
#     engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

#     start_time = perf()

#     print("Executing query. Results loading into dataframe...")
#     gdf = gpd.read_postgis(query_str, engine, geom_col="geometry")
#     srid = int(gdf["srid"].iloc[0])
#     gdf = gdf.set_crs(epsg=srid)
#     gdf = gdf.drop('srid', axis=1)

#     rowcnt = gdf.shape[0]
    
#     et_mins = round((perf() - start_time) / 60, 2)
#     print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")

#     return gdf



# if __name__ == '__main__':

#     gdf_col = sqlqry_to_gdf(sql_col)
#     gdf_epc = sqlqry_to_gdf(sql_epc)

#     df_county = (
#         gdf_col[gdf_col['Freeway']=='No']
#             .groupby(['COUNTY', 'ACCIDENT_YEAR', 'ColSeverity', 'DAC_EPC'], as_index=False)['CASE_ID'] \
#             .count() \
#             .rename(columns={'CASE_ID':'Collisions'})
#     )

#     df_sev = (
#         gdf_col[gdf_col['Freeway']=='No']
#             .groupby(['ACCIDENT_YEAR', 'ColSeverity', 'DAC_EPC'], as_index=False)['CASE_ID'] \
#             .count() \
#             .rename(columns={'CASE_ID':'Collisions'})
#     )
    
#     df_total = (
#         gdf_col[gdf_col['Freeway']=='No']
#             .groupby(['ACCIDENT_YEAR', 'DAC_EPC'], as_index=False)['CASE_ID'] \
#             .count() \
#             .rename(columns={'CASE_ID':'Collisions'})
#     )
    
#     df_county['Percent'] = df_county['Collisions']/df_county.groupby(['COUNTY', 'ACCIDENT_YEAR', 'ColSeverity'])['Collisions'].transform('sum')
#     df_sev   ['Percent'] = df_sev   ['Collisions']/df_sev   .groupby([          'ACCIDENT_YEAR', 'ColSeverity'])['Collisions'].transform('sum')
#     df_total ['Percent'] = df_total ['Collisions']/df_total .groupby([          'ACCIDENT_YEAR'               ])['Collisions'].transform('sum')

#     df_county = (
#         df_county[df_county['DAC_EPC']=='1'] \
#             .drop(['DAC_EPC'], axis=1) \
#             .pivot_table(index=['COUNTY', 'ACCIDENT_YEAR'], columns='ColSeverity', values=['Collisions', 'Percent']) \
#             .reset_index()
#     )
#     df_sev = (
#         df_sev[df_sev['DAC_EPC']=='1'] \
#             .drop(['DAC_EPC'], axis=1) \
#             .pivot_table(index=['ACCIDENT_YEAR'], columns='ColSeverity', values=['Collisions', 'Percent']) \
#             .reset_index()
#     )

#     df_county.columns = [f'{col[1]}_{col[0]}' if col[0] not in ['ACCIDENT_YEAR', 'COUNTY'] else col[0] for col in df_county.columns]
#     df_sev   .columns = [f'{col[1]}_{col[0]}' if col[0] not in ['ACCIDENT_YEAR', 'COUNTY'] else col[0] for col in df_sev   .columns]

#     df_total = (
#         df_total[df_total['DAC_EPC']=='1'] \
#             .drop(['DAC_EPC'], axis=1)
#     )

#     df_sev = df_sev.merge(df_total)

#     print(f'\n\nExported to {PATH_OUT}')
#     with pd.ExcelWriter(Path(PATH_OUT)/f'Safety_3 EPC.xlsx', engine='xlsxwriter') as writer:
#         df_sev   .to_excel(writer, index=False, sheet_name='Region')
#         df_county.to_excel(writer, index=False, sheet_name='County')
#     print('\n'*3)


#     breakpoint()
