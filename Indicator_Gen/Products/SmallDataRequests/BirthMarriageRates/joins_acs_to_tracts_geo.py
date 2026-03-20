

EXPORT=True
YEAR=2024

import numpy as np
import pandas as pd
from pathlib import Path
from IPython.display import display

PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' / 'Data'
PATH_POP6 = PATH_SP / 'Vibrant and Inclusive Places' / 'People and Community' / 'Pop and Demographics' / 'Pop_6 Birth Rates'
PATH_POP8 = PATH_SP / 'Vibrant and Inclusive Places' / 'People and Community' / 'Pop and Demographics' / 'Pop_8 Marriage Status'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")


import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent/'config'))
import functions as func
import help; help.print2()


def clean_pop6(df):

    if 'National' not in df.columns:
        df_nat = pd.read_excel(PATH_POP6 / 'Pop_6 National ACS5.xlsx', sheet_name='National')
        df_nat = df_nat[['Year', 'Birth Rate Per 1,000 People']].rename(columns={'Birth Rate Per 1,000 People':'National'})
        df = df.merge(df_nat, on='Year', how='left').drop_duplicates().reset_index(drop=True)

        conditions = [
            df['Birth Rate Per 1,000 People'] == df['National']
            , df['Birth Rate Per 1,000 People']  > df['National']
            , df['Birth Rate Per 1,000 People']  < df['National']
            , df['Birth Rate Per 1,000 People'].isna()
        ]
        choices = ['Equal to national birth rate', 'Higher than national birth rate', 'Lower than national birth rate', 'No Data']
        df['National Comparison'] = np.select(conditions, choices, default='missing conditions')
        df = df[df['Year'] == YEAR].reset_index(drop=True)
        df = help.clean_fips(df)
        df['GEOID'] = df['State FIPS'] + df['County FIPS'] + df['Tract ID']
        df = df.drop(['State FIPS', 'County FIPS', 'Tract ID', 'NAME', 'Race/Ethnicity', 'Variable', 'Year', 'County Name'], axis=1)
        for col in df.columns:
            if col != 'GEOID':
                df[f'{col}_br'] = df[col].copy()
                df = df.drop(col, axis=1)

    display(df['National Comparison_br'].value_counts())
    display(df.head())

    return df

def clean_pop8(df):

    if 'National' not in df.columns:
        df_nat = pd.read_excel(PATH_POP8 / 'Pop_8 National ACS5.xlsx', sheet_name='National')
        df_nat = df_nat[['Year', 'Variable', 'Percent']].rename(columns = {'Percent':'National'})
        df = df.merge(df_nat, on=['Year', 'Variable'], how='left').drop_duplicates().reset_index(drop=True)

        conditions = [
            df['Percent'] == df['National']
            , df['Percent']  > df['National']
            , df['Percent']  < df['National']
            , df['Percent'].isna()
        ]    
        choices = ['Equal to national marriage proportion', 'Higher than national marriage proportion', 'Lower than national marriage proportion', 'No Data']
        df['National Comparison'] = np.select(conditions, choices, default='missing conditions')
        df = df[df['Variable'] == 'Now married']
        df = df[df['Year'] == YEAR].reset_index(drop=True)
        df = help.clean_fips(df)
        df['GEOID'] = df['State FIPS'] + df['County FIPS'] + df['Tract ID']
        df = df.drop(['State FIPS', 'County FIPS', 'Tract ID', 'NAME', 'Race/Ethnicity', 'Variable', 'Year', 'County Name'], axis=1)
        for col in df.columns:
            if col != 'GEOID':
                df[f'{col}_mr'] = df[col].copy()
                df = df.drop(col, axis=1)

    display(df['National Comparison_mr'].value_counts())
    display(df.head())

    return df



if __name__ == '__main__':

    print('Importing/cleaning birth and marriage rates ACS data...');print()
    df_pop6 = pd.read_excel(PATH_POP6 / 'Pop_6 Tracts ACS5.xlsx', sheet_name='Tracts')
    df_pop8 = pd.read_excel(PATH_POP8 / 'Pop_8 Tracts ACS5.xlsx', sheet_name='Tracts')

    df_pop6 = clean_pop6(df_pop6)
    df_pop8 = clean_pop8(df_pop8)

    df_acs = df_pop6.merge(df_pop8, on='GEOID', how='left')

    help.print2(); print('Reading in Census Tracts file for SACOG region...'); print()
    DB = 'GISData'
    SQL_QUERY = """
                SELECT
                    GEOCODE, Countyname, NAMELSAD,
                    Shape.STAsBinary() AS geometry,
                    Shape.STSrid AS srid
                FROM gisowner.T2020_CENSUS_TRACTS_SACOG_REGION
                """
    gdf_tracts = func.sqlqry_to_gdf(SQL_QUERY, DB, servername='SQL-SVR', trustedconn='yes')
    gdf_tracts = gdf_tracts.rename(columns={'GEOCODE':'GEOID'})
    gdf_tracts = gdf_tracts.merge(df_acs, on='GEOID', how='left')

    breakpoint()



