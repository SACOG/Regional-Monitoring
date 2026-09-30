

'''
Code to import GIS data directly from the SDE
User needs to adjust SQL Query as needed
User must specify all columns needed in select statement
User must specify the geometry column as WKB (Shape.STAsBinary() AS geometry, where "Shape" is the geometry column alias in the SDE table)
'''



# Workspace --------------------------------------------------------------------------------------------------------------------------------------

import pandas as pd
from pathlib import Path
from time import perf_counter as perf
import urllib
import sqlalchemy as sqla
from sqlalchemy import text
from IPython.display import display

import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent/'config'))
import functions as func


PATH_I = Path(r'I:\Projects\Josh\Regional Monitoring\weights')
PATH_SERVER = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data')


def clean_fips(df):

    '''
    FIPS codes are often used across data sources but they don't always come in the same format, especially when using different file types (.csv, .xlsx, ...)
    This function standardizes the FIPS format for various FIPS codes
    '''
        
    df['Tract ID'   ] = df['Tract ID'   ].astype(str).apply('{:0>6}'.format)
    df['County FIPS'] = df['County FIPS'].astype(str).apply('{:0>3}'.format)
    df['State FIPS' ] = df['State FIPS' ].astype(str).apply('{:0>2}'.format)
    df['GEOCODE'] = df['State FIPS']+df['County FIPS']+df['Tract ID']
    
    return df


def organize_acs(path_i, path_server):

    print('Importing and organizing ACS data...')

    df_pop    = pd.read_excel(path_i / 'Total_Population Tracts ACS5.xlsx', sheet_name='Tracts')
    df_units  = pd.read_excel(path_i / 'Total_Households Tracts ACS5.xlsx', sheet_name='Tracts')
    df_br     = pd.read_excel(path_server / 'Pop_6 Tracts ACS5.xlsx', sheet_name='Tracts')
    df_ms     = pd.read_excel(path_server / 'Pop_8 Tracts ACS5.xlsx', sheet_name='Tracts')
    df_pop4   = pd.read_excel(path_server / 'Pop_4 Tracts ACS5.xlsx' , sheet_name='Tracts')
    df_cost3  = pd.read_excel(path_server / 'Cost_3 Tracts ACS5.xlsx', sheet_name='Tracts')

    df_pop    = df_pop   [df_pop   ['Year']==2024].reset_index(drop=True)
    df_units  = df_units [df_units ['Year']==2024].reset_index(drop=True)
    df_pop4   = df_pop4  [df_pop4  ['Year']==2024].reset_index(drop=True)
    df_cost3  = df_cost3 [df_cost3 ['Year']==2024].reset_index(drop=True)
    df_br     = df_br    [df_br    ['Year']==2024].reset_index(drop=True)
    df_ms     = df_ms    [df_ms    ['Year']==2024].reset_index(drop=True)

    df_pop   = clean_fips(df_pop  )
    df_units = clean_fips(df_units)
    df_pop4  = clean_fips(df_pop4 )
    df_cost3 = clean_fips(df_cost3)
    df_br    = clean_fips(df_br   )
    df_ms    = clean_fips(df_ms   )

    pop_cw = {
                'All': 'POP100'
                , 'American Indian or Alaska Native (NH)' : 'NH_Ind'
                , 'Asian (NH)': 'NH_Asn'
                , 'Black or African American (NH)': 'NH_Blk'
                , 'Hispanic or Latino': 'HispanicOrigin'
                , 'Native Hawaiian or other Pacific Islander (NH)': 'NH_Hwn'
                , 'Some other race (NH)': 'NH_Oth'
                , 'Two or more races (NH)': 'NH_2'
                , 'White (NH)': 'NH_Wht'
            }
    df_pop['Race/Ethnicity'] = df_pop['Race/Ethnicity'].map(pop_cw)
    df_pop = df_pop.pivot_table(index='GEOCODE', columns='Race/Ethnicity', values='Population').reset_index()
    df_pop['NotHispanic'] = df_pop['NH_2'].fillna(0) + df_pop['NH_Asn'].fillna(0) + df_pop['NH_Blk'].fillna(0) + df_pop['NH_Hwn'].fillna(0) + df_pop['NH_Ind'].fillna(0) + df_pop['NH_Oth'].fillna(0) + df_pop['NH_Wht'].fillna(0)
    df_pop['PopulationP1'] = df_pop['POP100'].copy()
    df_units = df_units[df_units['Race/Ethnicity']=='All'][['GEOCODE', 'Households']].rename(columns={'Households':'HU100'})
    
    df_pop4 = df_pop4[df_pop4['Variable'].isin(['18 to 64', '65+'])]
    pop4_cw = {
        '18 to 64': 'Population18_P3'
        , '65+': 'Population18_P3'
    }
    df_pop4['Variable'] = df_pop4['Variable'].map(pop4_cw)
    df_pop4 = df_pop4.groupby(['GEOCODE', 'Variable'], as_index=False)['Population'].sum()
    df_pop4 = df_pop4.pivot_table(index='GEOCODE', columns='Variable', values='Population').reset_index()   

    cost3_cw = {
        'Occupied': 'HU_Occupied'
        , 'Vacant': 'HU_Vacant'
        , 'Other (vacation, recreation, or occasional use homes)': 'HU_Vacant'
    }
    df_cost3['Variable'] = df_cost3['Variable'].map(cost3_cw)
    df_cost3 = df_cost3.pivot_table(index='GEOCODE', columns='Variable', values='Households').reset_index()
    df_cost3['Housing_Units'] = df_cost3['HU_Occupied'].fillna(0) + df_cost3['HU_Vacant'].fillna(0)

    df_br = df_br[['GEOCODE', 'Birth Rate Per 1,000 People']].rename(columns={'Birth Rate Per 1,000 People':'BR_per_1k_pop'})
    df_ms = df_ms[df_ms['Variable']=='Now married'][['GEOCODE', 'Percent']].rename(columns={'Percent':'MS_married'})
    df_ms['MS_married'] = df_ms['MS_married']*100

    df_update = df_pop   .merge(df_units, on='GEOCODE')
    df_update = df_update.merge(df_pop4 , on='GEOCODE')
    df_update = df_update.merge(df_cost3, on='GEOCODE')
    df_update = df_update.merge(df_br   , on='GEOCODE')
    df_update = df_update.merge(df_ms   , on='GEOCODE')

    print()

    return df_update


def sqlqry_send_to_sql(gdf, sql_query, dbname, servername='SQL-SVR', trustedconn='yes'):

    print()
    driver = func.get_odbc_driver()

    conn_str = f"DRIVER={driver};" \
        f"SERVER={servername};" \
        f"DATABASE={dbname};" \
        f"Trusted_Connection={trustedconn}"

    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    start_time = perf()

    print("Executing query. Exporting results to SDE...")
    gdf.to_sql(
                'stg_tract_updates',
                engine,
                schema="gisowner",
                if_exists="replace",
                index=False
            )

    with engine.begin() as conn:
        conn.execute(text(sql_query))
            
    rowcnt = gdf.shape[0]
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into the SDE.  Please check results on SDE.")






# Main -------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__=='__main__':

    # OBJECTID -> OBJECTID
    # FILEID -> File Identification
    # SUMLEV -> Summary Level
    # GEOCODE -> Geographic Code Identifier
    # STATE -> State (FIPS)
    # COUNTY -> County (FIPS)
    # COUNTYCC -> FIPS County Class Code
    # COUNTYNS -> County (NS)
    # PLACE -> Place (FIPS)
    # PLACECC -> FIPS Place Class Code
    # PLACENS -> Place (NS)
    # TRACT -> Census Tract
    # NAME -> Tract Name
    # NAMELSAD -> Tract Label
    # CBSA -> Metropolitan Statistical Area/Micropolitan Statistical Area
    # MEMI -> Metropolitan/Micropolitan Indicator
    # CSA -> Combined Statistical Area
    # PUMA -> Public Use Microdata Area
    # POP100 -> Population Count (100%)
    # HU100 -> Housing Unit Count (100%)
    # PopulationP1 -> Total Population
    # Population18_P3 -> Total population 18 years and over
    # HispanicOrigin -> Total__Hispanic or Latino
    # NotHispanic -> Total__Not Hispanic or Latino
    # NH_Wht -> Total__Not Hispanic or Latino__Population of one race__White alone
    # NH_Blk -> Total__Not Hispanic or Latino__Population of one race__Black or African American alone
    # NH_Ind -> Total__Not Hispanic or Latino__Population of one race__American Indian and Alaska Native alone
    # NH_Asn -> Total__Not Hispanic or Latino__Population of one race__Asian alone
    # NH_Hwn -> Total__Not Hispanic or Latino__Population of one race__Native Hawaiian and Other Pacific Islander alone
    # NH_Oth -> Total__Not Hispanic or Latino__Population of one race__Some Other Race Alone
    # NH_2 -> Total__Not Hispanic or Latino__Population of two or more races
    # Housing_Units -> Total__Housing Units
    # HU_Occupied -> Total__Occupied Housing Units
    # HU_Vacant -> Total__Vacant Housing Units
    # Countyname -> County Name
    # MPO -> MPO

    db = 'GISData'
    sql_query = """
                SELECT
                    OBJECTID,
                    FILEID,
                    SUMLEV,
                    GEOCODE,
                    STATE,
                    COUNTY,
                    COUNTYCC,
                    COUNTYNS,
                    PLACE,
                    PLACECC,
                    PLACENS,
                    TRACT,
                    NAME,
                    NAMELSAD,
                    CBSA,
                    MEMI,
                    CSA,
                    PUMA,
                    POP100,
                    HU100,
                    PopulationP1,
                    Population18_P3,
                    HispanicOrigin,
                    NotHispanic,
                    NH_Wht,
                    NH_Blk,
                    NH_Ind,
                    NH_Asn,
                    NH_Hwn,
                    NH_Oth,
                    NH_2,
                    Housing_Units,
                    HU_Occupied,
                    HU_Vacant,
                    BR_per_1k_pop,
                    MS_married,
                    Countyname,
                    MPO,
                    Shape.STAsBinary() AS geometry,
                    Shape.STSrid AS srid
                FROM gisowner.T2024_ACS5yr_Tracts_SACOG_Region
                """

    gdf = func.sqlqry_to_gdf(sql_query, db, servername='SQL-SVR', trustedconn='yes')
    display(gdf)

    df_update = organize_acs(PATH_I, PATH_SERVER)
    display(df_update)
    
    sql_query = """

    MERGE gisowner.T2024_ACS5yr_Tracts_SACOG_Region AS tgt
    USING gisowner.stg_tract_updates AS src
    ON tgt.GEOCODE = src.GEOCODE

    WHEN MATCHED THEN
    UPDATE SET
        tgt.POP100 = src.POP100,
        tgt.HU100 = src.HU100,
        tgt.PopulationP1 = src.PopulationP1,
        tgt.Population18_P3 = src.Population18_P3,
        tgt.HispanicOrigin = src.HispanicOrigin,
        tgt.NotHispanic = src.NotHispanic,
        tgt.NH_Wht = src.NH_Wht,
        tgt.NH_Blk = src.NH_Blk,
        tgt.NH_Ind = src.NH_Ind,
        tgt.NH_Asn = src.NH_Asn,
        tgt.NH_Hwn = src.NH_Hwn,
        tgt.NH_Oth = src.NH_Oth,
        tgt.NH_2 = src.NH_2,
        tgt.Housing_Units = src.Housing_Units,
        tgt.HU_Occupied = src.HU_Occupied,
        tgt.HU_Vacant = src.HU_Vacant,
        tgt.BR_per_1k_pop = src.BR_per_1k_pop,
        tgt.MS_married = src.MS_married;
    """

    sqlqry_send_to_sql(df_update, sql_query, db, servername='SQL-SVR', trustedconn='yes')



## 2020-2024 ACS 5-year estimate for national birth rate: 11.5993969100296
## 2020-2024 ACS 5-year estimate for national marriage status now married percent: 39.9736279135301%




# Code Graveyard -------------------------------------------------------------------------------------------------------------

# First used this SQL query to alter the table on the SDE to include missing columns:

    # sql_query_alter = """
    
    # IF COL_LENGTH('gisowner.T2024_ACS5yr_Tracts_SACOG_Region', 'BR_per_1k_pop') IS NULL
    # BEGIN
    #     ALTER TABLE gisowner.T2024_ACS5yr_Tracts_SACOG_Region
    #     ADD BR_per_1k_pop FLOAT;
    # END;

    # IF COL_LENGTH('gisowner.T2024_ACS5yr_Tracts_SACOG_Region', 'MS_married') IS NULL
    # BEGIN
    #     ALTER TABLE gisowner.T2024_ACS5yr_Tracts_SACOG_Region
    #     ADD MS_married FLOAT;
    # END;
    # """


    ## Code used for troubleshooting errors updating table on SDE --

    # def run_sql_query(sql_query, dbname, servername='SQL-SVR', trustedconn='yes'):
    
        # driver = func.get_odbc_driver()

        # conn_str = f"DRIVER={driver};" \
        #     f"SERVER={servername};" \
        #     f"DATABASE={dbname};" \
        #     f"Trusted_Connection={trustedconn}"

        # conn_str = urllib.parse.quote_plus(conn_str)
        # engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

        # with engine.begin() as conn:
        #     conn.execute(text(sql_query))

    # db = 'GISData'
    # sql_query = """
    #             SELECT
    #                 *
    #             FROM gisowner.stg_tract_updates
    #             """

    # df = func.sqlqry_to_df(sql_query, db, servername='SQL-SVR', trustedconn='yes')
    # display(df)
    # breakpoint()

    # db = 'GISData'
    # sql_query = """
    # SELECT TOP (25) src.GEOCODE
    # FROM gisowner.stg_tract_updates src
    # LEFT JOIN gisowner.T2024_ACS5yr_Tracts_SACOG_Region tgt
    # ON tgt.GEOCODE = src.GEOCODE
    # WHERE tgt.GEOCODE IS NULL
    # """
    # df = run_sql_query(sql_query, db, servername='SQL-SVR', trustedconn='yes')
    # display(df)
    # breakpoint()

    # db = 'GISData'
    # sql_query = """    
    # UPDATE tgt
    # SET
    #     tgt.POP100 = src.POP100
    # FROM gisowner.T2024_ACS5yr_Tracts_SACOG_Region tgt
    # JOIN gisowner.stg_tract_updates src
    # ON tgt.GEOCODE = src.GEOCODE
    # """
    # df = run_sql_query(sql_query, db, servername='SQL-SVR', trustedconn='yes')
    # display(df)
    # breakpoint()


    # db = 'GISData'
    # servername='SQL-SVR'
    # trustedconn='yes'

    # driver = func.get_odbc_driver()

    # conn_str = f"DRIVER={driver};" \
    #     f"SERVER={servername};" \
    #     f"DATABASE={db};" \
    #     f"Trusted_Connection={trustedconn}"

    # conn_str = urllib.parse.quote_plus(conn_str)
    # engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")
    
    # with engine.begin() as conn:
    #     result = conn.execute(text("""
    #         UPDATE tgt
    #         SET tgt.POP100 = src.POP100
    #         FROM gisowner.T2024_ACS5yr_Tracts_SACOG_Region tgt
    #         JOIN gisowner.stg_tract_updates src
    #         ON tgt.GEOCODE = src.GEOCODE
    #     """))

    #     print(result.rowcount)
    # breakpoint()


