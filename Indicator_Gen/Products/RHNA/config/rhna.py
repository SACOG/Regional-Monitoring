

import numpy as np
import pandas as pd
from pathlib import Path
import os
import requests
import gzip
import io
from tqdm import tqdm
import time
import re
import yaml
import traceback
import plotly.express as px
from IPython.display import display

import openpyxl
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
# from openpyxl.styles import numbers
from openpyxl.styles import Border, Side
from openpyxl import load_workbook
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
from openpyxl.utils import get_column_letter
border_thin = Side(style='thin')
# pip install kaleido==0.1.0.post1



EXPORT=True

PATH_DATA    = Path(r'I:\Projects\Josh\RHNA\Data')
PATH_CONFIG  = Path(__file__).parent.parent.parent.parent / 'Products' / 'RHNA' / 'config'
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
PATH_GEO = Path(r'I:\Projects\Josh\Geospatial Data')
PATH_LODES = Path(r'I:\Projects\Josh\Regional Monitoring')


def load_yaml():
    try:
        with open(PATH_CONFIG / 'rhna.yaml', 'r', encoding='utf-8') as yaml_file:
            yaml_rhna = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {PATH_CONFIG} does not exist.")
    return yaml_rhna


def split_notes(indicator):
    FILE_YAML = load_yaml()
    notes = FILE_YAML[indicator]['Notes']
    lines = notes.split('\\n')
    rows_new = [{'Indicator': 'Notes' if i == 0 else '', indicator: line} for i, line in enumerate(lines) if line]
    df_notes = pd.DataFrame(rows_new)
    return df_notes


def import_gz_from_url(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for non-200 status codes
    compressed_file = io.BytesIO(response.content)
    decompressed_file = gzip.GzipFile(fileobj=compressed_file)
    data = decompressed_file.read() # Read the decompressed data
    return data


def sort_categorical(df, col, sort_list):
    df['Sort'] = pd.Categorical(df[col], sort_list)
    df = df.sort_values('Sort').drop('Sort', axis=1)
    return df


def cols_geo_rename(df, cols, county, jurisdiction):
    if 'County' not in county:
        county = f'{county} County'
    cols = [col.replace('[county]', county) for col in cols]
    cols = [col.replace('[jurisdiction]', jurisdiction) for col in cols]
    df = df[cols]
    return df



## CHAS ---------------------------------------------------------------------------------------------------------------------------------------------


def chas_import(PATH_DATA, indicator):
    
    workbooks = os.listdir(PATH_DATA)
    workbooks = [workbook for workbook in workbooks if f'{indicator}' in workbook]
    print('\n'*2)
    print('Workbooks to import: ', workbooks)
    
    path_places   = PATH_DATA / f'{indicator} Places ACS5.xlsx'
    path_counties = PATH_DATA / f'{indicator} Counties ACS5.xlsx'
    path_mpo      = PATH_DATA / f'{indicator} MPO ACS5.xlsx'
    
    df_places   = pd.read_excel(path_places  , sheet_name='Places'  )
    df_counties = pd.read_excel(path_counties, sheet_name='Counties')
    df_mpo      = pd.read_excel(path_mpo     , sheet_name='MPO'     )

    return df_places, df_counties, df_mpo


def chas_clean(df_places, df_counties, df_mpo, columns, values):
    
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
    df_counties['NAME'] = df_counties['NAME'].str.replace(', California'     , '', regex=True)
    df_mpo['MPO'] = df_mpo['MPO'] + ' Region'
    
    df_places   = df_places  .rename(columns={'NAME':'Geography'})
    df_counties = df_counties.rename(columns={'NAME':'Geography'})
    df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography'})
    df_mpo = df_mpo.drop_duplicates()

    df_places   = df_places  [df_places  ['Year'] == df_places  ['Year'].max()]
    df_counties = df_counties[df_counties['Year'] == df_counties['Year'].max()]
    df_mpo      = df_mpo     [df_mpo     ['Year'] == df_mpo     ['Year'].max()]
    
    df_places   = df_places  [['County Name', 'Geography', columns, values, 'Percent']]
    df_counties = df_counties[[               'Geography', columns, values, 'Percent']]
    df_mpo      = df_mpo     [[               'Geography', columns, values, 'Percent']]

    df_places   = df_places  .reset_index(drop=True)
    df_counties = df_counties.reset_index(drop=True)
    df_mpo      = df_mpo     .reset_index(drop=True)

    return df_places, df_counties, df_mpo


def chas_sub(df_places, df_counties, county):
    
    df_counties_sub = df_counties[df_counties['Geography'  ] == county                       ]
    df_places_sub   = df_places  [df_places  ['County Name'] == county.replace(' County', '')]

    df_places_sub = df_places_sub.drop('County Name', axis=1)
    df_places_sub   = df_places_sub  .reset_index(drop=True)
    df_counties_sub = df_counties_sub.reset_index(drop=True)

    return df_places_sub, df_counties_sub


def chas_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub=None, df_mpo=None):

    if indicator in ['POPEMP_10', 'POPEMP_19', 'POPEMP_20', 'POPEMP_21', 'POPEMP_22', 'POPEMP_25', 'HSG_1', 'HSG_5', 'HSG_6'
                        , 'OVER_4', 'OVER_5', 'OVER_6', 'OVER_8', 'OVER_9', 'FARM_2', 'LGFEM_1', 'LGFEM_3', 'LGFEM_4', 'LGFEM_5'
                        , 'SEN_1', 'SEN_2', 'SEN_3', 'DISAB_3', 'HOMELS_1', 'HOMELS_2', 'HOMELS_3', 'HOMELS_4', 'ELI_2', 'AFFH_1', 'AFFH_2']:

        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_prod = df_plot.pivot_table(index=['Geography', 'Variable'], columns=columns, values=values).reset_index()

        if indicator == 'POPEMP_10':
            vars_to_sort = ['75k or more', '50k to 75k', ' 25k to 50k', '10k to 25k', 'Less than 10k']
        if indicator == 'POPEMP_19':
            vars_to_sort = ['Moved in 2021 or later', 'Moved in 2018 to 2020', 'Moved in 2010 to 2017', 'Moved in 2000 to 2009', 'Moved in 1999 or earlier']

        df_prod['Sort'] = pd.Categorical(df_prod['Variable'], vars_to_sort)
        df_prod = df_prod.sort_values(['Sort'], ascending=[False])
        df_prod = df_prod.drop(['Geography', 'Sort'], axis=1)
        df_pct = df_plot.pivot_table(index=['Geography', 'Variable'], columns=columns, values='Percent').reset_index()
        df_pct['Sort'] = pd.Categorical(df_prod['Variable'], vars_to_sort)
        df_pct = df_pct.sort_values(['Sort'], ascending=[False])
        df_pct = df_pct.drop(['Geography', 'Sort'], axis=1)
    
    elif indicator in ['HSG_4', 'HSG_11', 'OVER_1', 'OVER_3', 'SEN_4', 'DISAB_1', 'DISAB_4', 'DISAB_5', 'ELI_3']:
        pass
    elif indicator in ['POPEMP_19']:
        pass
        
    else:
        df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        if 'Percent' in df_places_sub.columns:
            df_prod = df_prod.drop('Percent', axis=1)
        df_prod = df_prod.pivot_table(index='Geography', columns=columns, values=values).reset_index()
        df_prod['Sort'] = pd.Categorical(df_prod['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_prod = df_prod.sort_values(['Sort'])
        df_prod = df_prod.drop(['Sort'], axis=1)

        if 'Percent' in df_places_sub.columns:
            df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.drop(values, axis=1)
            
            df_pct = df_pct.pivot_table(index='Geography', columns=columns, values='Percent').reset_index()
            df_pct['Sort'] = pd.Categorical(df_pct['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_pct = df_pct.sort_values(['Sort'])
            df_pct = df_pct.drop(['Sort'], axis=1)
        
    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod, df_pct






## ACS ---------------------------------------------------------------------------------------------------------------------------------------------



def acs_import(indicator):
    
    workbooks = os.listdir(PATH_DATA)
    workbooks = [workbook for workbook in workbooks if indicator in workbook]
    print('\n'*2)
    print('Workbooks to import: ', workbooks)

    if indicator == 'ELI_4':
        path_places   = PATH_DATA / f'{indicator} Places DP5.xlsx'
        path_counties = PATH_DATA / f'{indicator} Counties DP5.xlsx'
        path_mpo      = PATH_DATA / f'{indicator} MPO DP5.xlsx'
    else:
        path_places   = PATH_DATA / f'{indicator} Places ACS5.xlsx'  
        path_counties = PATH_DATA / f'{indicator} Counties ACS5.xlsx'
        path_mpo      = PATH_DATA / f'{indicator} MPO ACS5.xlsx'     
    
    df_places   = pd.read_excel(path_places  , sheet_name='Places'  )
    df_counties = pd.read_excel(path_counties, sheet_name='Counties')
    df_mpo      = pd.read_excel(path_mpo     , sheet_name='MPO'     )

    df_places   = df_places  .rename(columns={'Race_Ethnicity':'Race/Ethnicity', 'Percentage':'Percent'})
    df_counties = df_counties.rename(columns={'Race_Ethnicity':'Race/Ethnicity', 'Percentage':'Percent'})
    df_mpo      = df_mpo     .rename(columns={'Race_Ethnicity':'Race/Ethnicity', 'Percentage':'Percent'})

    if indicator == 'OVER_3':
        df_places   = df_places  [df_places  ['Variable']=='More than one occupant per room']
        df_counties = df_counties[df_counties['Variable']=='More than one occupant per room']
        df_mpo      = df_mpo     [df_mpo     ['Variable']=='More than one occupant per room']

    if indicator == 'ELI_3':
        df_places   = df_places  [df_places  ['Variable']=='Below poverty level']
        df_counties = df_counties[df_counties['Variable']=='Below poverty level']
        df_mpo      = df_mpo     [df_mpo     ['Variable']=='Below poverty level']

    if indicator == 'FARM_4':
        df_places   = df_places  [df_places  ['Variable']=='Agriculture & Natural Resources']
        df_counties = df_counties[df_counties['Variable']=='Agriculture & Natural Resources']
        df_mpo      = df_mpo     [df_mpo     ['Variable']=='Agriculture & Natural Resources']

    if len(df_places['Race/Ethnicity'].unique()) > 1:
        df_places   = df_places  [df_places  ['Race/Ethnicity'] != 'All']
        df_counties = df_counties[df_counties['Race/Ethnicity'] != 'All']
        df_mpo      = df_mpo     [df_mpo     ['Race/Ethnicity'] != 'All']

    return df_places, df_counties, df_mpo


def acs_clean(df_places, df_counties, df_mpo, params):

    params = params['prod']
    
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
    df_counties['NAME'] = df_counties['NAME'].str.replace(', California'     , '', regex=True)
    df_mpo['MPO'] = df_mpo['MPO'] + ' Region'
    
    df_places   = df_places  .rename(columns={'NAME':'Geography'})
    df_counties = df_counties.rename(columns={'NAME':'Geography'})
    df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography'})
    df_mpo = df_mpo.drop_duplicates()

    if 'Variable' in df_places.columns and params['var'] != 'Race/Ethnicity':
        df_places   = df_places  .rename(columns={'Variable':params['var']})
        df_counties = df_counties.rename(columns={'Variable':params['var']})
        df_mpo      = df_mpo     .rename(columns={'Variable':params['var']})
    
    df_places   = df_places  [df_places  ['Year'] == df_places  ['Year'].max()][['County Name', 'Geography', params['var'], params['value'], 'Percent']].reset_index(drop=True)
    df_counties = df_counties[df_counties['Year'] == df_counties['Year'].max()][[               'Geography', params['var'], params['value'], 'Percent']].reset_index(drop=True)
    df_mpo      = df_mpo     [df_mpo     ['Year'] == df_mpo     ['Year'].max()][[               'Geography', params['var'], params['value'], 'Percent']].reset_index(drop=True)

    if 'Race/Ethnicity' in df_places.columns:
        df_places  .loc[df_places  ['Race/Ethnicity'].isin(['Some other race (NH)', 'Two or more races (NH)']), 'Race/Ethnicity'] = 'Other race or multiple races (NH)'
        df_counties.loc[df_counties['Race/Ethnicity'].isin(['Some other race (NH)', 'Two or more races (NH)']), 'Race/Ethnicity'] = 'Other race or multiple races (NH)'
        df_mpo     .loc[df_mpo     ['Race/Ethnicity'].isin(['Some other race (NH)', 'Two or more races (NH)']), 'Race/Ethnicity'] = 'Other race or multiple races (NH)'

    
    return df_places, df_counties, df_mpo


def acs_sub(df_places, df_counties, county):
    
    df_counties_sub = df_counties[df_counties['Geography'  ] == county].reset_index(drop=True)
    df_places_sub   = df_places  [df_places  ['County Name'] == county.replace(' County', '')].drop('County Name', axis=1).reset_index(drop=True)

    return df_places_sub, df_counties_sub


def acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, variable=None, df_counties_sub=None, df_mpo=None):

    if indicator in ['POPEMP_10', 'POPEMP_18', 'POPEMP_19', 'POPEMP_20', 'POPEMP_21', 'POPEMP_22', 'POPEMP_25', 'HSG_1', 'HSG_5', 'HSG_6'
                        , 'OVER_4', 'OVER_5', 'OVER_6', 'OVER_8', 'OVER_9', 'FARM_2', 'LGFEM_1', 'LGFEM_3', 'LGFEM_4', 'LGFEM_5'
                        , 'SEN_1', 'SEN_2', 'SEN_3', 'DISAB_3', 'HOMELS_1', 'HOMELS_2', 'HOMELS_3', 'HOMELS_4', 'ELI_2', 'ELI_3', 'AFFH_1', 'AFFH_2']:

        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_prod = df_plot.pivot_table(index=['Geography', variable], columns=columns, values=values).reset_index()

        if indicator == 'POPEMP_10':
            vars_to_sort = ['Less than $10k', '$10k to $25k', '$25k to $50k', '$50k to $75k', '$75k or more']
        if indicator == 'POPEMP_18':
            vars_to_sort = ['Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-59', 'Age 60-64', 'Age 65-74', 'Age 75-84', 'Age 85+']
        if indicator == 'POPEMP_19':
            vars_to_sort = ['Moved in 1999 or earlier', 'Moved in 2000 to 2009', 'Moved in 2010 to 2017', 'Moved in 2018 to 2020', 'Moved in 2021 or later']
        if indicator == 'POPEMP_22':
            vars_to_sort = ['Detached single-family homes', 'Attached single-family homes', 'Multi-family housing', 'Mobile homes', 'Boat, RV, van, or other']
        if indicator == 'HSG_5':
            vars_to_sort = ['0 bedrooms', '1 bedroom', '2 bedrooms', '3-4 bedrooms', '5 or more bedrooms']
        if indicator == 'HSG_6':
            vars_to_sort = ['Lacking kitchen facilities', 'Lacking plumbing facilities']
        if indicator == 'OVER_6':
            vars_to_sort = ['0%-30% of income used for housing', '30%-50% of income used for housing', '50% or more of income used for housing', 'Not computed']
        if indicator == 'LGFEM_1':
            vars_to_sort = ['1 person household', '2 person household', '3 person household', '4 person household', '5 or more person household']
        if indicator == 'LGFEM_4':
            vars_to_sort = ['Married-couple family', 'Female-headed family household', 'Male-headed family household', 'Householders living alone', 'Other non-family households']
        if indicator == 'LGFEM_5':
            vars_to_sort = ['Female-headed households without children', 'Female-headed households with children']
        if indicator == 'SEN_2':
            vars_to_sort = ['Age 0-17', 'Age 18-64', 'Age 65+']
        if indicator == 'DISAB_3':
            vars_to_sort = ['With a disability', 'No disability']
        if indicator in ['POPEMP_20', 'ELI_3']:
            vars_to_sort = ['American Indian or Alaska Native', 'Asian', 'Black or African American', 'Native Hawaiian or other Pacific Islander', 'Hispanic or Latino', 'Some other race', 'Two or more races', 'White (NH)']

        df_prod['Sort'] = pd.Categorical(df_prod[variable], vars_to_sort)
        df_prod = df_prod.sort_values(['Sort']).drop(['Geography', 'Sort'], axis=1)

        df_pct = df_plot.pivot_table(index=['Geography', variable], columns=columns, values='Percent').reset_index()
        df_pct['Sort'] = pd.Categorical(df_pct[variable], vars_to_sort)
        df_pct = df_pct.sort_values(['Sort'])
        df_pct = df_pct.drop(['Geography', 'Sort'], axis=1)
    
    elif indicator in ['HSG_4', 'HSG_11', 'OVER_1', 'SEN_4', 'DISAB_1', 'DISAB_4', 'DISAB_5', 'ELI_3']:
        pass
    elif indicator in ['POPEMP_19']:
        pass
        
    else:

        df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        if 'Percent' in df_places_sub.columns:
            df_prod = df_prod.drop('Percent', axis=1)
        df_prod = df_prod.pivot_table(index='Geography', columns=columns, values=values).reset_index()
        df_prod['Sort'] = pd.Categorical(df_prod['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_prod = df_prod.sort_values(['Sort'])
        df_prod = df_prod.drop(['Sort'], axis=1)
        if indicator == 'HSG_7':
            df_prod = df_prod[['Geography', 'Units valued less than 250k', 'Units valued 250k-500k', 'Units valued 500k-750k', 'Units valued 750k-1M', 'Units valued 1M-1.5M', 'Units valued 1.5M-2M', 'Units valued 2M+']]
            df_prod = df_prod.rename(columns = {  'Units valued less than 250k': 'Units valued less than $250k'
                                                , 'Units valued 250k-500k': 'Units valued $250k-$500k'
                                                , 'Units valued 500k-750k': 'Units valued $500k-$750k'
                                                , 'Units valued 750k-1M': 'Units valued $750k-$1M'
                                                , 'Units valued 1M-1.5M': 'Units valued $1M-$1.5M'
                                                , 'Units valued 1.5M-2M': 'Units valued $1.5M-$2M'
                                                , 'Units valued 2M+': 'Units valued $2M+'
                                                })
        if indicator == 'HSG_9':
            df_prod = df_prod[['Geography', 'Rent less than 500', 'Rent 500-1,000', 'Rent 1,000-1,500', 'Rent 1,500-2,000', 'Rent 2,000-2,500', 'Rent 2,500-3,000', 'Rent 3,000 or more']]
            df_prod = df_prod.rename(columns = {'Rent less than 500': 'Rent less than $500'
                                            , 'Rent 500-1,000': 'Rent $500-$1,000'
                                            , 'Rent 1,000-1,500': 'Rent $1,000-$1,500'
                                            , 'Rent 1,500-2,000': 'Rent $1,500-$2,000'
                                            , 'Rent 2,000-2,500': 'Rent $2,000-$2,500'
                                            , 'Rent 2,500-3,000': 'Rent $2,500-$3,000'
                                            , 'Rent 3,000 or more': 'Rent $3,000 or more'
                                            })

        if 'Percent' in df_places_sub.columns:
            df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.drop(values, axis=1)
            
            df_pct = df_pct.pivot_table(index='Geography', columns=columns, values='Percent').reset_index()
            df_pct['Sort'] = pd.Categorical(df_pct['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_pct = df_pct.sort_values(['Sort'])
            df_pct = df_pct.drop(['Sort'], axis=1)
            if indicator == 'HSG_7':
                df_pct = df_pct[['Geography', 'Units valued less than 250k', 'Units valued 250k-500k', 'Units valued 500k-750k', 'Units valued 750k-1M', 'Units valued 1M-1.5M', 'Units valued 1.5M-2M', 'Units valued 2M+']]
                df_pct = df_pct.rename(columns = {'Units valued less than 250k': 'Units valued less than $250k'
                                                , 'Units valued 250k-500k': 'Units valued $250k-$500k'
                                                , 'Units valued 500k-750k': 'Units valued $500k-$750k'
                                                , 'Units valued 750k-1M': 'Units valued $750k-$1M'
                                                , 'Units valued 1M-1.5M': 'Units valued $1M-$1.5M'
                                                , 'Units valued 1.5M-2M': 'Units valued $1.5M-$2M'
                                                , 'Units valued 2M+': 'Units valued $2M+'
                                                })
            if indicator == 'HSG_9':
                df_pct = df_pct[['Geography', 'Rent less than 500', 'Rent 500-1,000', 'Rent 1,000-1,500', 'Rent 1,500-2,000', 'Rent 2,000-2,500', 'Rent 2,500-3,000', 'Rent 3,000 or more']]
                df_pct = df_pct.rename(columns = {'Rent less than 500': 'Rent less than $500'
                                                , 'Rent 500-1,000': 'Rent $500-$1,000'
                                                , 'Rent 1,000-1,500': 'Rent $1,000-$1,500'
                                                , 'Rent 1,500-2,000': 'Rent $1,500-$2,000'
                                                , 'Rent 2,000-2,500': 'Rent $2,000-$2,500'
                                                , 'Rent 2,500-3,000': 'Rent $2,500-$3,000'
                                                , 'Rent 3,000 or more': 'Rent $3,000 or more'
                                                })
        
    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod, df_pct


def main_acs(indicator, params):

    df_places, df_counties, df_mpo = acs_import(indicator)
    df_places, df_counties, df_mpo = acs_clean(df_places, df_counties, df_mpo, params)

    if indicator in ['POPEMP_3']:
        df_places   = df_places  .groupby(['County Name', 'Geography', 'Race/Ethnicity'], as_index=False)['Population'].sum()
        df_counties = df_counties.groupby([               'Geography', 'Race/Ethnicity'], as_index=False)['Population'].sum()
        df_mpo      = df_mpo     .groupby([               'Geography', 'Race/Ethnicity'], as_index=False)['Population'].sum()
        df_places  ['Percent'] = df_places  ['Population'] / df_places  .groupby(['County Name', 'Geography'])['Population'].transform('sum')
        df_counties['Percent'] = df_counties['Population'] / df_counties.groupby([               'Geography'])['Population'].transform('sum')
        df_mpo     ['Percent'] = df_mpo     ['Population'] / df_mpo     .groupby([               'Geography'])['Population'].transform('sum')

    if indicator in ['OVER_7']:
        df_places  .loc[df_places  ['Cost Burden']=='50% or more of income used for housing', 'Cost Burden'] = '50%+ of income used for housing'
        df_counties.loc[df_counties['Cost Burden']=='50% or more of income used for housing', 'Cost Burden'] = '50%+ of income used for housing'
        df_mpo     .loc[df_mpo     ['Cost Burden']=='50% or more of income used for housing', 'Cost Burden'] = '50%+ of income used for housing'



    counties = df_counties['Geography'].unique()

    for county in counties:

        print()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):
            
            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo]).pivot_table(index=params['prod']['index'], columns=params['prod']['pivot'], values=params['prod']['value']).reset_index()
            df_pct  = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo]).pivot_table(index=params['prod']['index'], columns=params['prod']['pivot'], values='Percent'              ).reset_index()
            
            df_prod = cols_geo_rename(df_prod, params['Columns'].split('<>'), county, jurisdiction)
            df_pct  = cols_geo_rename(df_pct , params['Columns'].split('<>'), county, jurisdiction)
            
            if indicator in ['HSG_7']:
                sort_list = ['Units valued less than 250k', 'Units valued 250k-500k', 'Units valued 500k-750k', 'Units valued 750k-1M', 'Units valued 1M-1.5M', 'Units valued 1.5M-2M', 'Units valued 2M+']
                df_prod = sort_categorical(df_prod, 'Home Value', sort_list)
                df_pct  = sort_categorical(df_pct , 'Home Value', sort_list)
            if indicator in ['HSG_9']:
                sort_list = ["Rent less than 500", "Rent 500-1,000", "Rent 1,000-1,500", "Rent 1,500-2,000", "Rent 2,000-2,500", "Rent 2,500-3,000", "Rent 3,000 or more"]
                df_prod = sort_categorical(df_prod, 'Rent Price', sort_list)
                df_pct  = sort_categorical(df_pct , 'Rent Price', sort_list)

            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            if indicator == 'FARM_4':
                df_plot['Share of Overall Workforce'] = round(df_plot['Percent']*100, 1)
            else:
                df_plot[f'Percent of {params['prod']['value']}'] = round(df_plot['Percent']*100, 1)
            df_plot['Sort'] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG Region'])
            if indicator == 'FARM_4':
                df_plot = df_plot.sort_values(['Sort', 'Share of Overall Workforce'], ascending=[True, False]).drop('Sort', axis=1)
            else:
                df_plot = df_plot.sort_values(['Sort', f'Percent of {params['prod']['value']}'], ascending=[True, False]).drop('Sort', axis=1)
            

            fig = make_fig(indicator, params, df_plot, county, jurisdiction)
            plot_rhna(fig, county, jurisdiction, indicator, params)
            export_rhna(county, jurisdiction, indicator, params, df_prod, df_pct)






## Plotting/Exporting ---------------------------------------------------------------------------------------------------------------------------------------------


def sort_plot(df_plot, indicator, county, jurisdiction):

    if indicator in ['POPEMP_21', 'POPEMP_23', 'POPEMP_24', 'HSG_2', 'HSG_7', 'HSG_9', 'HSG_11', 'OVER_3', 'OVER_4', 'OVER_5', 'OVER_7',
                     'OVER_8', 'LGFEM_1', 'LGFEM_2', 'LGFEM_3', 'LGFEM_4', 'LGFEM_5', 'SEN_1', 'SEN_3', 'SEN_4', 'DISAB_1', 'DISAB_5',
                     'HOMELS_1', 'HOMELS_2', 'ELI_2', 'ELI_3', 'ELI_4', 'AFFH_1', 'AFFH_3', 'POPEMP_25']:
        if indicator == 'POPEMP_23':
            df_plot['Household Type'] = df_plot['Household Type'].str.replace(' households', '')
        if indicator == 'POPEMP_24':
            var_map = {'Households with no children': 'No children'
                       , 'Households with 1 or more children under 18': "One or more children under 18"}
            df_plot['Household Type'] = df_plot['Household Type'].map(var_map)
        if indicator == 'HSG_2':
            var_map = {'Occupied housing units': 'Occupied'
                       , 'Vacant housing units': 'Vacant'}
            df_plot['Occupancy Status'] = df_plot['Occupancy Status'].map(var_map)
        if indicator == 'HSG_7':
            df_plot['sort_geo'] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_plot['Sort'] = pd.Categorical(df_plot['Home Value'], ['Units valued less than 250k', 'Units valued 250k-500k', 'Units valued 500k-750k', 'Units valued 750k-1M', 'Units valued 1M-1.5M', 'Units valued 1.5M-2M', 'Units valued 2M+'])
            df_plot = df_plot.sort_values(['sort_geo', 'Sort']).drop(['sort_geo', 'Sort'], axis=1)
            var_map = {'Units valued less than 250k': '&#36;0k-&#36;250k'
                        , 'Units valued 250k-500k': '&#36;250k-&#36;500k'
                        , 'Units valued 500k-750k': '&#36;500k-&#36;750k'
                        , 'Units valued 750k-1M': '&#36;750k-&#36;1M'
                        , 'Units valued 1M-1.5M': '&#36;1M-&#36;1.5M'
                        , 'Units valued 1.5M-2M': '&#36;1.5M-&#36;2M'
                        , 'Units valued 2M+': '&#36;2M+'}
            df_plot['Home Value'] = df_plot['Home Value'].map(var_map)
            df_plot['Share of Owner-Occupied Units'] = df_plot['Percent of Households'].copy()
        if indicator == 'HSG_9':
            df_plot['sort_geo'] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_plot['Sort'] = pd.Categorical(df_plot['Rent Price'], ["Rent less than 500", "Rent 500-1,000", "Rent 1,000-1,500", "Rent 1,500-2,000", "Rent 2,000-2,500", "Rent 2,500-3,000", "Rent 3,000 or more"])
            df_plot = df_plot.sort_values(['sort_geo', 'Sort']).drop(['sort_geo', 'Sort'], axis=1)
            var_map = {"Rent less than 500": "&#36;0-&#36;500"
                        , "Rent 500-1,000": "&#36;500-&#36;1,000"
                        , "Rent 1,000-1,500": "&#36;1,000-&#36;1,500"
                        , "Rent 1,500-2,000": "&#36;1,500-&#36;2,000"
                        , "Rent 2,000-2,500": "&#36;2,000-&#36;2,500"
                        , "Rent 2,500-3,000": "&#36;2,500-&#36;3,000"
                        , "Rent 3,000 or more": "&#36;3,000+"}
            df_plot['Rent Price'] = df_plot['Rent Price'].map(var_map)
            df_plot['Share of Renter-Occupied Units'] = df_plot['Percent of Households'].copy()
        if indicator == 'HSG_11':
            df_plot['Sort'] = pd.Categorical(df_plot['Income Group'], ["Very Low", "Low", "Moderate", "Above Moderate"])
            df_plot = df_plot.sort_values('Sort').drop('Sort', axis=1)
        if indicator in ['OVER_3', 'ELI_3']:
            var_map = {
                'American Indian or Alaska Native':'American Indian or<br>Alaska Native'
                , 'Asian':'Asian'
                , 'Black or African American':'Black or<br>African American'
                , 'Hispanic or Latino':'Hispanic or<br>Latino'
                , 'Native Hawaiian or other Pacific Islander':'Native Hawaiian or<br>other Pacific Islander'
                , 'Other race or multiple races':'Other race or<br>multiple races'
                , 'White (NH)': 'White (NH)'
            }
            df_plot['Race/Ethnicity'] = df_plot['Race/Ethnicity'].map(var_map)
            if indicator == 'OVER_3':
                df_plot = df_plot[df_plot['Geography']==jurisdiction]
        if indicator in ['POPEMP_21', 'OVER_4', 'OVER_5', 'LGFEM_3', 'SEN_1', 'SEN_3']:
            var_map = {
                '0%-30% of AMI':'Less than 30%'
                , '31%-50% of AMI':'31%-50%'
                , '51%-80% of AMI':'51%-80%'
                , '81%-100% of AMI':'81%-100%'
                , 'Greater than 100% of AMI':'Greater than 100%'
            }
            df_plot['Income Level (% of AMI)'] = df_plot['Income Level'].map(var_map)
        if indicator == 'LGFEM_1':
            var_map = {
                '1 person household': '1 Person<br>Household',
                '2 person household': '2 Person<br>Household',
                '3 person household': '3 Person<br>Household',
                '4 person household': '4 Person<br>Household',
                '5 or more person household': '5 or More Person<br>Household'
            }
            df_plot['Household Size'] = df_plot['Household Size'].map(var_map)
        if indicator == 'LGFEM_2':
            df_plot['Sort'] = pd.Categorical(df_plot['Household Size'], ["1 person households", "2 person households", "3-4 person households", "5 or more person households"])
            df_plot = df_plot.sort_values('Sort').drop('Sort', axis=1)
        if indicator == 'LGFEM_4':
            var_map = {
                'Married-couple family': 'Married-Couple<br>Family',
                'Female-headed family household': 'Female-Headed<br>Family',
                'Male-headed family household': 'Male-Headed<br>Family',
                'Householders living alone': 'Householders<br>Living Alone',
                'Other non-family households': 'Other Non-Family'
            }
            df_plot['Household Type'] = df_plot['Household Type'].map(var_map)
        if indicator == 'LGFEM_5':
            var_map = {
                'Female-headed households without children': 'Without Children',
                'Female-headed households with children': 'With Children'
            }
            df_plot['Family Status'] = df_plot['Family Status'].map(var_map)
        if indicator in ['SEN_4', 'DISAB_1']:
            var_map = {
                'With an ambulatory difficulty':'Ambulatory<br>Difficulty',
                'With an independent living difficulty':'Independent Living<br>Difficulty',
                'With a hearing difficulty':'Hearing<br>Difficulty',
                'With a self-care difficulty':'Self-Care<br>Difficulty',
                'With a cognitive difficulty':'Cognitive<br>Difficulty',
                'With a vision difficulty':'Vision<br>Difficulty'
            }
            df_plot['Disability Type'] = df_plot['Disability Type'].map(var_map)
        if indicator == 'DISAB_5':
            var_map = {
                'Home of Parent /Family /Guardian':'Home of<br>Parent/Family/Guardian'
                , 'Community Care Facility':'Community<br>Care<br>Facility'
                , 'Independent /Supported Living':'Independent/Supported<br>Living'
                , 'Foster /Family Home':'Foster/Family<br>Home'
                , 'Intermediate Care Facility':'Intermediate Care<br>Facility'
                , 'Other': 'Other'
            }
            df_plot['Residence Type'] = df_plot['Residence Type'].map(var_map)
        if indicator == 'HOMELS_1':
            var_map = {
                    'Persons in households with at least one adult and one child':'At Least One Adult<br>and One Child',
                    'Persons in households with only children':'Only Children',
                    'Persons in households without children':'Without Children',
                }
            df_plot['Household Type'] = df_plot['Household Type'].map(var_map)
        if indicator == 'HOMELS_2':
            var_map = {
                    'American Indian, Alaska Native, or Indigenous':'American Indian,<br>Alaska Native,<br>or Indigenous'
                    , 'Asian or Asian American':'Asian or<br>Asian American'
                    , 'Black, African American, or African':'Black,<br>African American,<br>or African'
                    , 'Hispanic/Latina/e/o Only':'Hispanic/Latina/e/o Only'
                    , 'Native Hawaiian or Other Pacific Islander':'Native Hawaiian or<br>Other Pacific Islander'
                    , 'Other race or multiple races':'Other Race or<br>Multiple Races'
                    , 'White': 'White'
                }
            df_plot['Race/Ethnicity'] = df_plot['Race/Ethnicity'].map(var_map)
            var_map = {
                    'Homeless Population (%)':'Share of homeless population'
                    , 'Overall Population (%)':'Share of overall population'
                }
            df_plot['Prop'] = df_plot['Prop'].map(var_map)
        if indicator == 'HOMELS_3':
            var_map = {
                    'Sheltered - Emergency Shelter':'Emergency Shelter'
                    , 'Sheltered - Transitional Housing':'Transitional Housing'
                    , 'Unsheltered':'Unsheltered'
                }
            df_plot['Shelter Status'] = df_plot['Shelter Status'].map(var_map)
        if indicator in ['OVER_8', 'ELI_2', 'AFFH_1']:
            var_map = {
                'American Indian or Alaska Native (NH)':'American Indian or<br>Alaska Native (NH)'
                , 'Asian (NH)':'Asian (NH)'
                , 'Black or African American (NH)':'Black or<br>African American (NH)'
                , 'Hispanic or Latino':'Hispanic or<br>Latino'
                , 'Native Hawaiian or other Pacific Islander (NH)':'Native Hawaiian or<br>other Pacific Islander (NH)'
                , 'Other race or multiple races (NH)':'Other race or<br>multiple races (NH)'
                , 'White (NH)': 'White (NH)'
            }
            df_plot['Race/Ethnicity'] = df_plot['Race/Ethnicity'].map(var_map)
        if indicator == 'ELI_4':
            var_map = {
                'Acutely low income': 'Acutely Low'
                , 'Extremely low income': 'Extremely Low'
                , 'Very low income': 'Very Low'
                , 'Lower income': 'Lower'
                , 'Moderate income': 'Moderate'
                , 'High income': 'High'
            }
            df_plot['Income Bracket'] = df_plot['Income Bracket'].map(var_map)
        if indicator == 'AFFH_3':
            var_map = {
                'Population 5 years and over who speak english "well" or "very well"': 'Speak english "well" or "very well"'
                , 'Population 5 years and over who speak english "not well" or "not at all"': 'Speak english "not well" or "not at all"'
            }
            df_plot['English Proficiency'] = df_plot['English Proficiency'].map(var_map)
        if indicator == 'POPEMP_25':
            var_map = {
                'At Risk of or Experiencing Exclusion': 'At Risk of or<br>Experiencing Exclusion'
                , 'Susceptible to or Experiencing Displacement':'Susceptible to or<br>Experiencing Displacement'
                , 'At Risk of or Experiencing Gentrification': 'At Risk of or<br>Experiencing Gentrification'
                , 'Stable Moderate/Mixed Income':'Stable Moderate/Mixed<br>Income'
                , 'Other':'Other'
            }
            df_plot['Typology'] = df_plot['Typology'].map(var_map)
        
        if 'Sort' in df_plot.columns:
            df_plot = df_plot.drop('Sort', axis=1)

    return df_plot



def make_fig(indicator, params, df_plot, county, jurisdiction):

    params = params['plot']

    if 'County' not in county:
        county = f'{county} County'

    color_discrete_map  = {
    
        'SACOG Region': '#E57149'
        , county: '#7EB460'
        , jurisdiction: '#27AAE1'

        , 'American Indian or Alaska Native (NH)': '#96D2E8'
        , 'American Indian or Alaska Native': '#96D2E8'
        , 'American Indian or<br>Alaska Native (NH)': '#96D2E8'
        , 'American Indian or<br>Alaska Native': '#96D2E8'
        , 'American Indian,<br>Alaska Native,<br>or Indigenous': '#96D2E8'
        , 'Native Hawaiian or other Pacific Islander (NH)': '#00A97D'
        , 'Native Hawaiian or other Pacific Islander': '#00A97D'
        , 'Native Hawaiian or<br>other Pacific Islander (NH)': '#00A97D'
        , 'Native Hawaiian or<br>other Pacific Islander': '#00A97D'
        , 'Native Hawaiian or<br>Other Pacific Islander': '#00A97D'
        , 'Some other race (NH)': '#55C8E8'
        , 'Some other race': '#55C8E8'
        , 'Two or more races (NH)': '#006883'
        , 'Two or more races': '#006883'
        , 'Other race or multiple races (NH)': '#6764A6'
        , 'Other race or multiple races': '#006883'
        , 'Other race or<br>multiple races (NH)': '#006883'
        , 'Other race or<br>multiple races': '#006883'
        , 'Other Race or<br>Multiple Races (NH)': '#006883'
        , 'Other Race or<br>Multiple Races': '#006883'
        , 'Asian (NH)': '#27AAE1'
        , 'Asian': '#27AAE1'
        , 'Asian or<br>Asian American': '#27AAE1'
        , 'Black or African American (NH)': '#7EB460'
        , 'Black or African American': '#7EB460'
        , 'Black or<br>African American (NH)': '#7EB460'
        , 'Black or<br>African American': '#7EB460'
        , 'Black,<br>African American,<br>or African': '#7EB460'
        , 'Black': '#7EB460'
        , 'Hispanic or Latino': "#E57149"
        , 'Hispanic or<br>Latino': "#E57149"
        , 'Hispanic/Latina/e/o Only': '#E57149'
        , 'Hispanic': "#E57149"
        , 'White (NH)': "#A24F82"
        , 'White': "#A24F82"

        , '2000': '#6764A6'
        , '2010': '#E57149'
        , '2020': '#27AAE1'
        , '2023': '#7EB460'
        , '2024': '#7EB460'
        , '2025': '#7EB460' # 00A97D

        , "2002":"#7EB460"
        , "2007":"#E57149"
        , "2012":"#27AAE1"
        , "2017":"#6764A6"
        , "2022":"#A24F82"

        , 'Same house': '#7EB460'
        , 'Same city or town': '#E57149'
        , 'Same county': '#27AAE1'
        , 'Elsewhere in CA': '#6764A6'
        , 'Elsewhere in U.S.': '#A24F82'
        , 'Abroad': '#00A97D'

        , 'Agriculture & Natural Resources': '#7EB460'
        , 'Construction': '#E57149'
        , 'Manufacturing, Wholesale, & Transportation': '#27AAE1'
        , 'Retail': '#6764A6'
        , 'Information': '#A24F82'
        , 'Finance & Professional Services': '#00A97D'
        , 'Health & Educational Services': '#006883'
        , 'Other': '#55C8E8'

        , 'Arts, Recreation, & Other': '#96D2E8'
        , 'Financial & Leasing': '#00A97D'
        , 'Government': "#7EB460"
        , 'Manufacturing & Wholesale': '#27AAE1'
        , 'Professional & Managerial Services': '#808285'
        , 'Transportation & Utilities': '#00A97D'

        , 'Management, Business, Science, and Arts occupations': '#7EB460'
        , 'Service occupations': '#E57149'
        , 'Sales and Office occupations': '#27AAE1'
        , 'Natural Resources, Construction, and Maintenance occupations': '#6764A6'
        , 'Production, Transportation, and Material Moving occupations': '#A24F82'

        , 'Private company workers': '#7EB460'
        , 'Self-employed workers': '#E57149'
        , 'Private not-for-profit workers': '#27AAE1'
        , 'Local and state government workers': '#6764A6'
        , 'Federal government workers': '#A24F82'
        , 'Unpaid family workers': '#00A97D'

        , 'Place of residence': '#E57149'
        , 'Place of work': '#27AAE1'

        , 'Earnings &#36;1,250/month or less': '#E57149'
        , 'Earnings &#36;1,251/month to &#36;3,333/month': '#27AAE1'
        , 'Earnings greater than &#36;3,333/month': '#7EB460'

        , 'Renter occupied': '#E57149'
        , 'Owner occupied': '#27AAE1'

        , 'Female-headed family': '#6764A6'
        , 'Male-headed family': '#27AAE1'
        , 'Married-couple family': '#E57149'
        , 'Other non-family': '#7EB460'
        , 'Single-person': '#A24F82'

        , 'No children': '#27AAE1'
        , 'One or more children under 18': '#E57149'

        , "Occupied":"#27AAE1"
        , "Vacant": "#E57149"

        , "For rent":"#E57149"
        , "For sale only":"#00A97D"
        , "For seasonal, recreational, or occasional use":"#27AAE1"
        , "Other vacant":"#7EB460"
        , "Rented, not occupied":"#006883"
        , "Sold, not occupied":"#A24F82"
        , "For migrant workers":"#6764A6"

        , "Less than &#36;250k":"#E57149"
        , "&#36;0k-&#36;250k":"#E57149"
        , "&#36;250k-&#36;500k":"#27AAE1"
        , "&#36;500k-&#36;750k":"#6764A6"
        , "&#36;750k-&#36;1M":"#A24F82"
        , "&#36;1M-&#36;1.5M":"#006883"
        , "&#36;1.5M-&#36;2M":"#00A97D"
        , "&#36;2M+":"#7EB460"

        , "Less than &#36;500":"#E57149"
        , "&#36;0-&#36;500":"#E57149"
        , "&#36;500-&#36;1,000":"#27AAE1"
        , "&#36;1,000-&#36;1,500":"#6764A6"
        , "&#36;1,500-&#36;2,000":"#A24F82"
        , "&#36;2,000-&#36;2,500":"#006883"
        , "&#36;2,500-&#36;3,000":"#00A97D"
        , "&#36;3,000 or more":"#7EB460"
        , "&#36;3,000+":"#7EB460"

        , 'Less than or equal to 1 person per room': '#7EB460'
        , '1.01 to 1.5 occupants per room': '#27AAE1'
        , 'More than 1.5 occupants per room': '#E57149'

        , 'Not computed': '#808285'
        , '0%-30% of income used for housing': '#27AAE1'
        , '30%-50% of income used for housing': '#7EB460'
        , '50%+ of income used for housing': '#E57149'

        , "1 person households":"#E57149"
        , "2 person households":"#27AAE1"
        , "3-4 person households":"#7EB460"
        , "5 or more person households":"#A24F82"

        , 'Less than 30%': '#E57149'
        , '31%-50%': '#27AAE1'
        , '51%-80%': '#7EB460'
        , '81%-100%': '#A24F82'
        , 'Greater than 100%': '#00A97D'

        , 'Above poverty level': '#27AAE1'
        , 'Below poverty level': '#E57149'

        , 'With a disability': '#E57149'
        , 'No disability': '#27AAE1'

        , 'Employed': '#27AAE1'
        , 'Unemployed': '#E57149'

        , "Sheltered - Emergency Shelter":"#E57149"
        , "Sheltered - Transitional Housing": "#27AAE1"
        , 'Unsheltered': "#7EB460"

        , "Emergency Shelter":"#E57149"
        , "Transitional Housing": "#27AAE1"

        , 'Share of homeless population': '#E57149'
        , 'Share of overall population': '#27AAE1'

        , 'Chronic Substance Abuse':"#E57149"
        , 'HIV/AIDS': "#27AAE1"
        , 'Severely Mentally Ill': "#7EB460"
        , 'Veterans': '#006883'
        , 'Victims of Domestic Violence': '#A24F82'

        , "2020-21":"#E57149"
        , "2021-22":"#27AAE1"
        , "2022-23":"#7EB460"
        , "2023-24":"#A24F82"
        , "2024-25":"#00A97D"

        , '0%-30% of AMI': '#E57149'
        , '31%-50% of AMI': '#27AAE1'
        , '51%-80% of AMI': '#7EB460'
        , '81%-100% of AMI': '#A24F82'
        , 'Greater than 100% of AMI': '#00A97D'

        , 'Loan originated':'#27AAE1'
        , 'Application approved but not accepted':'#E57149'
        , 'Application denied': '#7EB460'
        , 'Application withdrawn by applicant':'#808285'
        , 'File closed for incompleteness':'#96D2E8'
        , 'Purchased loan': '#A24F82'
        , 'Preapproval request denied':'#006883'
        , 'Preapproval request approved but not accepted':'#00A97D'

        , 'Speak english "well" or "very well"': '#27AAE1'
        , 'Speak english "not well" or "not at all"': '#E57149'

        , 'At Risk of or Experiencing Exclusion': '#E57149'
        , 'Susceptible to or Experiencing Displacement':'#27AAE1'
        , 'At Risk of or Experiencing Gentrification': '#6764A6'
        , 'Stable Moderate/Mixed Income':'#A24F82'

        , "1 bedroom":"#E57149"
        , "2 bedrooms":"#27AAE1"
        , "3 bedrooms":"#6764A6"
        , "4 bedrooms":"#A24F82"
        , "5+ bedrooms":"#7EB460"

        , 'Low': '#E57149'
        , 'Moderate': '#27AAE1'
        , 'High': '#7EB460'
        , 'Very High': '#A24F82'

        , 'Low Resource': '#E57149'
        , 'Moderate Resource': '#27AAE1'
        , 'High/Highest Resource': '#7EB460'
        , 'Unknown': '#A24F82'

        , "Spanish":"#E57149"
        , "Other Indo-European":"#27AAE1"
        , "Other Asian and Pacific Island":"#6764A6"
        , "Chinese (incl. Mandarin, Cantonese)":"#A24F82"
        , "Tagalog (incl. Filipino)":"#E57149"
        , "Russian, Polish, or other Slavic":"#00A97D"
        , "Vietnamese":"#7EB460"
        , "Other and unspecified":"#808285"
        , "Korean":"#149ABF"
        , 'German or other West Germanic': '#55C8E8'
        , 'French, Haitian, or Cajun': '#96D2E8'
        , 'Arabic': '#006883'

    }


    df_plot = sort_plot(df_plot, indicator, county, jurisdiction)

    if indicator in ['HSG_6', 'AFFH_5']:
        text_limit=0
    else:
        text_limit=4

    if params['text']:
        df_plot['text'] = np.where(df_plot[params['y']] >= text_limit, df_plot[params['y']].astype(str)+'%', '')


    # Line graphs
    if params['line']:
        if params['color']:
            fig = px.line(df_plot, x=params['x'], y=params['y'], color=params['color'], color_discrete_map=color_discrete_map, markers=True)
        else:
            fig = px.line(df_plot, x=params['x'], y=params['y'], markers=True)
            fig['data'][0]['line']['color']='#27AAE1'
        if indicator == 'POPEMP_1':
            range_min = df_plot[params['y']].min()-4
            range_max = df_plot[params['y']].max()+4
            range_diff = abs(range_max-range_min)
            if range_diff <= 10:
                dtick=1
            elif (range_diff > 10) & (range_diff <= 50):
                dtick=5
            elif (range_diff > 50) & (range_diff <= 100):
                dtick=10
            elif (range_diff > 100) & (range_diff <= 200):
                dtick=25
            else:
                dtick=50
            fig.update_yaxes(ticksuffix='%', dtick=dtick, range=[range_min, range_max])
        if indicator in ['POPEMP_13', 'POPEMP_14']:
            if df_plot[params['y']].max() > 2.2:
                fig.update_yaxes(dtick=1, range=[0, 3.25])
            else:
                fig.update_yaxes(dtick=0.5, range=[0, 2.25])
        if indicator == 'POPEMP_15':
            fig.update_yaxes(ticksuffix='%', dtick=5, range=[0, 21])
        if indicator != 'POPEMP_27':
            fig.update_xaxes(dtick=2, range=[df_plot[params['x']].min()-0.5, df_plot[params['x']].max()+0.5])

    # Bar graphs
    if params['bar']:
        if params['bar'] == 'stacked':
            if params['text']:
                fig = px.bar(df_plot, x=params['x'], y=params['y'], color=params['color'], color_discrete_map=color_discrete_map, text='text')
            else:
                fig = px.bar(df_plot, x=params['x'], y=params['y'], color=params['color'], color_discrete_map=color_discrete_map)
        if params['bar'] == 'group':
            if params['text']:
                fig = px.bar(df_plot, x=params['x'], y=params['y'], color=params['color'], color_discrete_map=color_discrete_map, barmode='group', text='text')
            else:
                fig = px.bar(df_plot, x=params['x'], y=params['y'], color=params['color'], color_discrete_map=color_discrete_map, barmode='group')
        if params['bar'] == 'simple':
            fig = px.bar(df_plot, x=params['x'], y=params['y'])
            fig.update_traces(marker_color='#27AAE1')

    if params['format'] == 'percent':
        if indicator in ['POPEMP_1', 'POPEMP_15', 'HSG_6', 'HSG_7', 'HSG_9', 'OVER_3', 'OVER_4', 'SEN_4', 'DISAB_1', 'HOMELS_2', 'ELI_3', 'ELI_4', 'FARM_4', 'AFFH_5']:
            fig.update_yaxes(ticksuffix='%')
        else:
            fig.update_yaxes(dtick=25, ticksuffix='%', range=[0,102])
        fig.update_traces(textfont_color='white')
    if params['format'] == 'dollar':
        fig.update_yaxes(tickprefix='$', tickformat = ',.0f')
    if params['format'] == 'count':
        fig.update_yaxes(tickformat=',.0f')

    if indicator == 'POPEMP_10':
        fig.update_xaxes(tickvals=[0, 1, 2, 3, 4], ticktext=['Less than &#36;10k', '&#36;10k to &#36;25k', '&#36;25k to &#36;50k', '&#36;50k to &#36;75k', '&#36;75k or more'])
    if indicator == 'HOMELS_4':
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.175,xanchor="right", x=0.75))

    if indicator not in ['POPEMP_1', 'POPEMP_10', 'POPEMP_13', 'POPEMP_15', 'POPEMP_27', 'HSG_8', 'HSG_10', 'HOMELS_2', 'HOMELS_4', 'ELI_4', 'AFFH_5']:
        fig.update_layout(legend={'traceorder': 'reversed'})

    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_traces(hovertemplate="%{y}")

    return fig



def plot_rhna(fig, county, jurisdiction, indicator, params):

    PLOTLY_FONT_FAMILY='Microsoft YaHei'
    PLOTLY_TEMPLATE='plotly_white'
    PLOTLY_CONFIG={'modeBarButtonsToRemove': ['select', 'lasso', 'toImage'], 'displaylogo': False}

    path_plots = PATH_OUT / county.replace(' County', '') / jurisdiction / 'plots'

    fig.update_layout(
        legend_title=None
        # , title=params['Title']
        , template=PLOTLY_TEMPLATE
        , font_family=PLOTLY_FONT_FAMILY
        , yaxis=dict(tickfont=dict(size=14))
        , xaxis=dict(tickfont=dict(size=14))
        , margin=dict(t=20, b=20)
        )

    if indicator in ['POPEMP_3', 'POPEMP_5', 'POPEMP_6', 'POPEMP_7', 'FARM_4',
                    'POPEMP_8', 'POPEMP_9', 'POPEMP_16', 'POPEMP_23', 'ELI_3',
                    'POPEMP_24', 'POPEMP_27', 'HSG_2', 'HSG_3', 'HSG_7', 'HSG_9',
                    'OVER_2', 'OVER_7', 'LGFEM_2', 'DISAB_2', 'HOMELS_4', 'AFFH_5',
                    'ELI_1', 'AFFH_3', 'FARM_2', 'LGFEM_1', 'SEN_2', 'RISK_1']:
        fig.update_layout(xaxis_title=None)
    
    if jurisdiction == 'Sacramento':
        fig.show(config=PLOTLY_CONFIG)
    
    if EXPORT:
        file_png = path_plots / f'{indicator}.png'
        try:
            fig.write_image(file=file_png, engine='kaleido', scale=1, width=1000, height=500)
        except Exception as e:
            e



def export_rhna_temp(county, jurisdiction, indicator):

    if EXPORT:

        FILE_YAML = load_yaml()

        path_juris = PATH_OUT / county.replace(' County', '') / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

        if os.path.isfile(path_juris):
            wb = openpyxl.load_workbook(path_juris)
        else:
            wb = openpyxl.Workbook()

        if indicator not in wb.sheetnames:
            wb.create_sheet(indicator)
        if indicator in wb.sheetnames:
            sheet_index = wb.sheetnames.index(indicator)
            wb.remove(wb[indicator])
            wb.create_sheet(indicator, sheet_index)
        ws = wb[indicator]

        df_out = pd.DataFrame({'Temp': [FILE_YAML[indicator]['Title'], 'The data used for this indicator is not available for this jurisdiction, likely due to small sample sizes']})

        for r in dataframe_to_rows(df_out, index=False, header=False):
            ws.append(r)
        ws['A1'].font = Font(bold=True, size=14)

        wb.save(path_juris)


def export_rhna(county, jurisdiction, indicator, params, df_prod, df_pct=None):

    if EXPORT:

        path_plots  = PATH_OUT / county.replace(' County', '') / jurisdiction / 'plots'
        path_tables = PATH_OUT / county.replace(' County', '') / jurisdiction / 'tables'
        path_plots .mkdir(parents=True, exist_ok=True)
        path_tables.mkdir(parents=True, exist_ok=True)

        try:

            try:
                path_plot = path_plots / f'{indicator}.png'
                img = Image(path_plot)
            except Exception as e:
                e
                pass
            
            path_juris = PATH_OUT / county.replace(' County', '') / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

            if os.path.isfile(path_juris):
                wb = openpyxl.load_workbook(path_juris)
            else:
                wb = openpyxl.Workbook()

            if indicator not in wb.sheetnames:
                wb.create_sheet(indicator)
            if indicator in wb.sheetnames:
                sheet_index = wb.sheetnames.index(indicator)
                wb.remove(wb[indicator])
                wb.create_sheet(indicator, sheet_index)
            ws = wb[indicator]

            # df_prod.columns = [col.title() for col in df_prod.columns if 'SACOG' not in col]
            # if df_pct is not None: df_pct.columns = [col.title() for col in df_pct.columns if 'SACOG' not in col]

            df_prod.to_csv(path_tables / f'{indicator}_prod.csv', index=False)
            if df_pct is not None:
                df_pct.to_csv(path_tables / f'{indicator}_pct.csv', index=False)

            df_prod2 = df_prod.reset_index().T.reset_index().T.drop(0, axis=1)
            if df_pct is not None:
                df_pct2 = df_pct.reset_index().T.reset_index().T.drop(0, axis=1)
            df_title = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_title.iloc[0, 0] = f'{indicator}: {params['Title']}'
            df_subtitle1 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            if indicator in ['FARM_2', 'HOMELS_1']:
                df_subtitle1.iloc[0, 0] = f'Total: {county} County'
            elif indicator in ['HSG_11', 'RISK_1', 'POPEMP_28']:
                df_subtitle1.iloc[0, 0] = f'Total: {jurisdiction}'
            elif 'Value' in params.keys():
                df_subtitle1.iloc[0, 0] = f'Total: {params['Value']}' # TODO: make sure this is working correctly, i.e. "Total: Households" or "Total: Population" (or should it be "Total: Individuals")
            else:
                df_subtitle1.iloc[0, 0] = 'Total'
            if df_pct is not None:
                df_subtitle2 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
                df_subtitle2.iloc[0, 0] = 'Percent'

            df_space1 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_space2 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])

            df_source = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_source.iloc[0, 0] = 'Source'
            df_source.iloc[0, 1] = params['Source']

            df_years = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_years.iloc[0, 0] = 'Year(s)'
            df_years.iloc[0, 1] = params['Year(s)']

            df_notes = split_notes(indicator)

            df_title    .columns = df_prod2.columns
            df_subtitle1.columns = df_prod2.columns
            df_space1   .columns = df_prod2.columns
            df_space2   .columns = df_prod2.columns
            df_source   .columns = df_prod2.columns
            df_years    .columns = df_prod2.columns
            df_notes    .columns = df_prod2.columns[:2]
            if df_pct is not None:
                df_subtitle2.columns = df_prod2.columns

            if df_pct is not None:
                df_out = pd.concat([df_title, df_subtitle1, df_prod2, df_subtitle2, df_pct2, df_space1, df_space2, df_source, df_years, df_notes])
            else:
                df_out = pd.concat([df_title, df_subtitle1, df_prod2, df_space1, df_space2, df_source, df_years, df_notes])
            
            for r in dataframe_to_rows(df_out, index=False, header=False): ws.append(r)
                
            ws['A1'].font = Font(bold=True, size=14)
            ws['A2'].font = Font(bold=True, size=12)
            row_num = 3 + df_prod.shape[0] + 1
            ws[f'A{row_num}'].font = Font(bold=True, size=12) # 7 (style 1)

            for col in ws.columns:
                col = col[0].column_letter
                ws[f'{col}3'].border = Border(top=border_thin, left=border_thin, right=border_thin, bottom=border_thin)
                if df_pct is not None:
                    row_num = 3 + df_prod.shape[0] + 2
                    ws[f'{col}{row_num}'].border = Border(top=border_thin, left=border_thin, right=border_thin, bottom=border_thin) # 8 (style 1)

            format_numbers = '#,##0'
            format_percent = '0.0%'
            format_ratio   = '0.00'
            format_age   = '0.0'
            format_dollars = '$#,##0'
            
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                if column == 'A':
                    pass
                else:
                    for cell in col:
                        try:
                            cell_num = re.search(r'.*?\.(.*)\>.*', str(cell))
                            cell_num = cell_num.group(1)
                            cell_num = cell_num[1:]
                            row_num = 3 + df_prod.shape[0]
                            if int(cell_num) > row_num or indicator in ['POPEMP_15'] or (indicator == 'POPEMP_1' and column in ['E', 'F', 'G']):# or (indicator in ['HSG_4'] and column == 'C'): # trying to get Percent column to show up properly
                                cell.value = float(cell.value)
                                cell.number_format = format_percent
                            else:
                                if indicator in ['POPEMP_13', 'POPEMP_14', 'POPEMP_27', 'HSG_8', 'HSG_10', 'HSG_12']:
                                    if indicator == 'POPEMP_27':
                                        cell.number_format = format_age
                                    elif indicator in ['HSG_8', 'HSG_10', 'HSG_12']:
                                        cell.number_format = format_dollars
                                    else:
                                        cell.number_format = format_ratio
                                else:
                                    cell.value = int(cell.value)
                                    cell.number_format = format_numbers
                        except Exception as e:
                            e
                            pass
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception as e:
                        e
                adjusted_width = (max_length + 1) * 1.1
                if column in ['A', 'B']:
                    if column == 'A':
                        ws.column_dimensions[column].width = 20
                    else:
                        ws.column_dimensions[column].width = 35
                else:
                    ws.column_dimensions[column].width = adjusted_width

            try:
                row_num = df_out.shape[0] + 3
                ws.add_image(img, f'B{row_num}') # 21 (style 1)
            except Exception as e:
                e
            wb.save(path_juris)
        except Exception as e:
                    print(e)
                    traceback.print_exc()
                    print()
                    export_rhna_temp(county, jurisdiction, indicator)



def write_sup_table(df, indicator, county, jurisdiction):
    """
    Write a pandas DataFrame into an *existing* Excel workbook at a specific cell,
    without modifying anything else in the workbook except the cells written.
    Then auto-fit ONLY the columns used by the written table.
    """

    try:
        if EXPORT:

            path_wb = PATH_OUT / county.replace(' County', '') / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

            if not path_wb.exists():
                raise FileNotFoundError(f"Workbook not found: {path_wb}")

            wb = load_workbook(path_wb)
            if indicator not in wb.sheetnames:
                raise ValueError(f"Sheet {indicator} not found. Available: {wb.sheetnames}")

            ws = wb[indicator]

            start_cell = "H1" # Subject to change depending on indicator
            col_letters, row = coordinate_from_string(start_cell)
            start_col = column_index_from_string(col_letters)
            start_row = row

            out_df = df.copy()

            values = []
            values.append(list(out_df.columns))
            values.extend(out_df.to_numpy().tolist())

            n_rows_written = len(values)              # header + data rows
            n_cols_written = len(values[0]) if values else 0

            for r_offset, row_values in enumerate(values):
                for c_offset, val in enumerate(row_values):
                    ws.cell(row=start_row + r_offset, column=start_col + c_offset).value = val

            min_width = 8.43   # Excel default
            max_width = 60     # prevent comically wide columns
            padding  = 1       # a little breathing room

            for c in range(start_col, start_col + n_cols_written):
                col_letter = get_column_letter(c)

                max_len = 0
                for r in range(start_row, start_row + n_rows_written):
                    v = ws.cell(row=r, column=c).value
                    if v is None:
                        continue
                    max_len = max(max_len, len(str(v)))

                new_width = max(min_width, min(max_width, max_len + padding))
                ws.column_dimensions[col_letter].width = new_width

            wb.save(path_wb)

    except Exception as e:
        print(e)
        traceback.print_exc()
        print()
        export_rhna_temp(county, jurisdiction, indicator)




# def write_risk1_table(
#     df: pd.DataFrame,
#     workbook_path: Union[str, Path],
#     sheet_name: str = "RISK_1",
#     start_cell: str = "H3",
#     *,
#     include_header: bool = True,
#     # include_index: bool = False,
#     # clear_output_range: bool = False,
#     # na_rep: Optional[str] = None,
#     # save_as: Optional[Union[str, Path]] = None,
# ) -> None:
#     """
#     Write a pandas DataFrame into an *existing* Excel workbook at a specific cell,
#     without modifying anything else in the workbook except the cells written.

#     Parameters
#     ----------
#     df : pd.DataFrame
#         The DataFrame to write.
#     workbook_path : str | Path
#         Path to the existing workbook (e.g., "RHNA_Folsom.xlsx").
#     sheet_name : str
#         Name of the worksheet to write into (default: "RISK_1").
#     start_cell : str
#         Excel cell (e.g., "H3") where the top-left of the output table begins.
#     include_header : bool
#         If True, write column headers at the first row of the output.
#     include_index : bool
#         If True, write the DataFrame index as the first column.
#     clear_output_range : bool
#         If True, clears the target rectangle (header + data area) before writing.
#         This prevents stale values if the new df is smaller than the old one.
#     na_rep : str | None
#         If provided, replaces NaN/None with this string.
#     save_as : str | Path | None
#         If provided, saves to a new file path instead of overwriting the original.

#     Returns
#     -------
#     None
#     """
#     workbook_path = Path(workbook_path)
#     if not workbook_path.exists():
#         raise FileNotFoundError(f"Workbook not found: {workbook_path}")

#     # Load workbook without destroying existing content
#     wb = load_workbook(workbook_path)
#     if sheet_name not in wb.sheetnames:
#         raise ValueError(f"Sheet '{sheet_name}' not found. Available: {wb.sheetnames}")

#     ws = wb[sheet_name]

#     # Parse start cell
#     col_letters, row = coordinate_from_string(start_cell)
#     start_col = column_index_from_string(col_letters)
#     start_row = row

#     # Build the 2D values matrix to write
#     out_df = df.copy()

#     # # if na_rep is not None:
#     #     out_df = out_df.where(out_df.notna(), na_rep)

#     # if include_index:
#     #     out_df = out_df.reset_index()

#     values = []
#     if include_header:
#         values.append(list(out_df.columns))
#     values.extend(out_df.to_numpy().tolist())


#     # # Optionally clear only the rectangle we will write into
#     # n_rows = len(values)
#     # n_cols = 0 if n_rows == 0 else max(len(r) for r in values)
#     # if clear_output_range and n_rows > 0 and n_cols > 0:
#     #     for r in range(start_row, start_row + n_rows):
#     #         for c in range(start_col, start_col + n_cols):
#     #             ws.cell(row=r, column=c).value = None

#     # Write values cell-by-cell (preserves everything else on the sheet)
#     for r_offset, row_values in enumerate(values):
#         for c_offset, val in enumerate(row_values):
#             ws.cell(row=start_row + r_offset, column=start_col + c_offset).value = val

#     # # Save (overwrite or save_as)
#     # out_path = Path(save_as) if save_as else workbook_path
#     wb.save(workbook_path)

