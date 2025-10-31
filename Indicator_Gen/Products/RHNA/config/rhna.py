

def print2(): print();print()
def print3(): print();print();print()




EXPORT=False



import pandas as pd
from pathlib import Path
import os
import requests
import gzip
import io
from tqdm import tqdm
from datetime import datetime
import re
import yaml
from IPython.display import display

import openpyxl
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
# from openpyxl.styles import numbers
from openpyxl.styles import Border, Side
border_thin = Side(style='thin')
# pip install kaleido==0.1.0.post1



PATH_DATA    = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected'
PATH_GIT     = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
PATH_CENSUS  = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'  / 'Data' / 'Census'
PATH_CONFIG0 = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'  / 'config'
PATH_PROD    = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA'
PATH_CONFIG  = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
PATH_PY      = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'python'
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'General' / 'RHNA' / 'Final Products'
PATH_GEO = Path(r'I:\Projects\Josh\Geospatial Data')
PATH_LODES = Path(r'I:\Projects\Josh\Regional Monitoring')

FILE_YAML = PATH_CONFIG / 'rhna.yaml'



def load_yaml():
    try:
        with open(PATH_CONFIG / 'rhna.yaml', 'r', encoding='utf-8') as yaml_file:
            yaml_rhna = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {PATH_CONFIG} does not exist.")
    
    return yaml_rhna


def split_notes(indicator):
    notes = FILE_YAML[indicator.replace('RHNA_', '')]['Notes']
    
    lines = notes.split('\\n')
    rows_new = [{'Indicator': 'Notes' if i == 0 else '', indicator: line} for i, line in enumerate(lines) if line]
    
    df_notes = pd.DataFrame(rows_new)
    
    return df_notes



def import_gz_from_url(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for non-200 status codes

    compressed_file = io.BytesIO(response.content)
    decompressed_file = gzip.GzipFile(fileobj=compressed_file)

    # Read the decompressed data
    data = decompressed_file.read()

    return data



def dof_import(indicator):
    
    workbooks = os.listdir(PATH_DATA)
    workbooks = [workbook for workbook in workbooks if indicator in workbook]
    print(); print()
    print('Workbooks to import: ', workbooks)     

    path_places   = PATH_DATA / f'{indicator} Places DOF.xlsx'  
    path_counties = PATH_DATA / f'{indicator} Counties DOF.xlsx'
    path_mpo      = PATH_DATA / f'{indicator} MPO DOF.xlsx'     
    
    df_places   = pd.read_excel(path_places  , sheet_name='Places'  )
    df_counties = pd.read_excel(path_counties, sheet_name='Counties')
    df_mpo      = pd.read_excel(path_mpo     , sheet_name='MPO'     )

    return df_places, df_counties, df_mpo


def dof_clean(df_places, df_counties, df_mpo):

    df_places   = df_places  [df_places  ['MPO'] == 'SACOG']
    df_counties = df_counties[df_counties['MPO'] == 'SACOG']
    df_mpo      = df_mpo[     df_mpo     ['MPO'] == 'SACOG']
    df_mpo['MPO'] = df_mpo['MPO'] + ' Region'

    df_places   = df_places  [[          'County', 'Jurisdiction', 'Year', 'Population']]
    df_counties = df_counties[[          'County',                 'Year', 'Population']]
    df_mpo      = df_mpo     [['MPO'   ,                           'Year', 'Population']]

    df_places   = df_places  .rename(columns={'Jurisdiction':'Geography'})
    df_counties = df_counties.rename(columns={'County'      :'Geography'})
    df_mpo      = df_mpo     .rename(columns={'MPO'         :'Geography'})

    df_places   = df_places  .reset_index(drop=True)
    df_counties = df_counties.reset_index(drop=True)
    df_mpo      = df_mpo     .reset_index(drop=True)

    return df_places, df_counties, df_mpo


def dof_sub(df_places, df_counties, county):
    
    df_counties_sub = df_counties[df_counties['Geography'] == county]
    df_places_sub   = df_places  [df_places  ['County'   ] == county]
        
    df_places_sub   = df_places_sub  .reset_index(drop=True)
    df_counties_sub = df_counties_sub.reset_index(drop=True)

    return df_places_sub, df_counties_sub

def dof_index(df_places_sub, df_counties_sub, df_mpo, jurisdiction):

    df_plot1 = df_places_sub.copy()
    df_plot2 = df_counties_sub.copy()
    df_plot3 = df_mpo.copy()

    df_plot1 = df_plot1[df_plot1['Geography'] == jurisdiction]
    df_plot1 = df_plot1[df_plot1['Population'] > 0]
    base_year = df_plot1['Year'].min()
    df_year = df_plot1[df_plot1['Year'] == base_year]
    df_year = df_year.rename(columns={'Population':'base_year'})
    df_year = df_year.drop('Year', axis=1)
    df_plot1 = df_plot1.merge(df_year, on=['County', 'Geography'], how='left')
    df_plot1['growth'] = round(df_plot1['Population']/df_plot1['base_year']*100-100)
    df_plot1 = df_plot1.drop('base_year', axis=1)

    df_plot2 = df_plot2[df_plot2['Year'] >= base_year]
    df_year = df_plot2[df_plot2['Year'] == base_year]
    df_year = df_year.rename(columns={'Population':'base_year'})
    df_year = df_year.drop('Year', axis=1)
    df_plot2 = df_plot2.merge(df_year, on=['Geography'], how='left')
    df_plot2['growth'] = round(df_plot2['Population']/df_plot2['base_year']*100-100)
    df_plot2 = df_plot2.drop('base_year', axis=1)

    df_plot3 = df_plot3[df_plot3['Year'] >= base_year]
    df_year = df_plot3[df_plot3['Year'] == base_year]
    df_year = df_year.rename(columns={'Population':'base_year'})
    df_year = df_year.drop('Year', axis=1)
    df_plot3 = df_plot3.merge(df_year, on=['Geography'], how='left')
    df_plot3['growth'] = round(df_plot3['Population']/df_plot3['base_year']*100-100)
    df_plot3 = df_plot3.drop(['base_year'], axis=1)

    return df_plot1, df_plot2, df_plot3


def dof_pivot(indicator, df_places_sub, county, jurisdiction, df_counties_sub=None, df_mpo=None):

    if indicator.replace('RHNA_', '') in ['POPEMP_1']:

        df_counties_sub = df_counties_sub.rename(columns = {'Population': f'{county} County', 'growth': f'Percent Difference from 2000: {county} County'})
        df_counties_sub = df_counties_sub.drop('Geography', axis=1)

        df_mpo = df_mpo.rename(columns={'Population': 'SACOG', 'growth': f'Percent Difference from 2000: SACOG Region'})
        df_mpo = df_mpo.drop('Geography', axis=1)

        df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        
        df_prod = df_prod.drop(['County', 'Geography'], axis=1)
        df_prod = df_prod.rename(columns = {'Population': jurisdiction, 'growth': f'Percent Difference from 2000: {jurisdiction}'})
        df_prod = df_prod.merge(df_counties_sub, on='Year')
        df_prod = df_prod.merge(df_mpo         , on='Year')
        df_prod = df_prod[['Year', jurisdiction, f'{county} County', 'SACOG', f'Percent Difference from 2000: {jurisdiction}', f'Percent Difference from 2000: {county} County', 'Percent Difference from 2000: SACOG Region']]
        df_prod = df_prod.sort_values('Year', ascending=True).reset_index(drop=True)

    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod



def acs_import(indicator):
    
    workbooks = os.listdir(PATH_DATA)
    workbooks = [workbook for workbook in workbooks if indicator in workbook]
    print(); print()
    print('Workbooks to import: ', workbooks)

    if indicator == 'RHNA_ELI_4':
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

    return df_places, df_counties, df_mpo



def acs_clean(df_places, df_counties, df_mpo, columns, values):
    
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
    
    df_places   = df_places  [['County Name', 'Geography', columns, values, 'Percentage']]
    df_counties = df_counties[[               'Geography', columns, values, 'Percentage']]
    df_mpo      = df_mpo     [[               'Geography', columns, values, 'Percentage']]

    df_places   = df_places  .reset_index(drop=True)
    df_counties = df_counties.reset_index(drop=True)
    df_mpo      = df_mpo     .reset_index(drop=True)

    return df_places, df_counties, df_mpo


def acs_sub(df_places, df_counties, county):
    
    df_counties_sub = df_counties[df_counties['Geography'  ] == county                       ]
    df_places_sub   = df_places  [df_places  ['County Name'] == county.replace(' County', '')]

    df_places_sub = df_places_sub.drop('County Name', axis=1)
    df_places_sub   = df_places_sub  .reset_index(drop=True)
    df_counties_sub = df_counties_sub.reset_index(drop=True)

    return df_places_sub, df_counties_sub


def acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub=None, df_mpo=None):

    indicator_name = indicator.replace('RHNA_', '')

    if indicator_name in ['POPEMP_10', 'POPEMP_18', 'POPEMP_19', 'POPEMP_20', 'POPEMP_21', 'POPEMP_22', 'POPEMP_25', 'HSG_1', 'HSG_5', 'HSG_6'
                        , 'OVER_4', 'OVER_5', 'OVER_6', 'OVER_8', 'OVER_9', 'FARM_2', 'LGFEM_1', 'LGFEM_3', 'LGFEM_4', 'LGFEM_5'
                        , 'SEN_1', 'SEN_2', 'SEN_3', 'DISAB_3', 'HOMELS_1', 'HOMELS_2', 'HOMELS_3', 'HOMELS_4', 'ELI_2', 'ELI_3', 'AFFH_1', 'AFFH_2']:

        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_prod = df_plot.pivot_table(index=['Geography', 'Variable'], columns=columns, values=values).reset_index()

        if indicator_name == 'POPEMP_10':
            vars_to_sort = ['Less than $10k', '$10k to $25k', '$25k to $50k', '$50k to $75k', '$75k or more']
        if indicator_name == 'POPEMP_18':
            vars_to_sort = ['Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-59', 'Age 60-64', 'Age 65-74', 'Age 75-84', 'Age 85+']
        if indicator_name == 'POPEMP_19':
            vars_to_sort = ['Moved in 1999 or earlier', 'Moved in 2000 to 2009', 'Moved in 2010 to 2017', 'Moved in 2018 to 2020', 'Moved in 2021 or later']
        if indicator_name in ['POPEMP_20', 'ELI_3']:
            vars_to_sort = ['American Indian or Alaska Native', 'Asian', 'Black or African American', 'Native Hawaiian or other Pacific Islander', 'Hispanic or Latino', 'Some other race', 'Two or more races', 'White (NH)']
        if indicator_name == 'POPEMP_22':
            vars_to_sort = ['Detached single-family homes', 'Attached single-family homes', 'Multi-family housing', 'Mobile homes', 'Boat, RV, van, or other']
        if indicator_name == 'HSG_5':
            vars_to_sort = ['0 bedrooms', '1 bedroom', '2 bedrooms', '3-4 bedrooms', '5 or more bedrooms']
        if indicator_name == 'HSG_6':
            vars_to_sort = ['Lacking kitchen facilities', 'Lacking plumbing facilities']
        if indicator_name == 'OVER_6':
            vars_to_sort = ['0%-30% of income used for housing', '30%-50% of income used for housing', '50% or more of income used for housing', 'Not computed']
        if indicator_name == 'LGFEM_1':
            vars_to_sort = ['1 person household', '2 person household', '3 person household', '4 person household', '5 or more person household']
        if indicator_name == 'LGFEM_4':
            vars_to_sort = ['Married-couple family', 'Female-headed family household', 'Male-headed family household', 'Householders living alone', 'Other non-family households']
        if indicator_name == 'LGFEM_5':
            vars_to_sort = ['Female-headed households without children', 'Female-headed households with children']
        if indicator_name == 'SEN_2':
            vars_to_sort = ['Age 0-17', 'Age 18-64', 'Age 65+']
        if indicator_name == 'DISAB_3':
            vars_to_sort = ['With a disability', 'No disability']



        df_prod['Sort'] = pd.Categorical(df_prod['Variable'], vars_to_sort)
        df_prod = df_prod.sort_values(['Sort'])
        df_prod = df_prod.drop(['Geography', 'Sort'], axis=1)
        df_pct = df_plot.pivot_table(index=['Geography', 'Variable'], columns=columns, values='Percentage').reset_index()
        df_pct['Sort'] = pd.Categorical(df_pct['Variable'], vars_to_sort)
        df_pct = df_pct.sort_values(['Sort'])
        df_pct = df_pct.drop(['Geography', 'Sort'], axis=1)
    
    elif indicator_name in ['HSG_4', 'HSG_11', 'OVER_1', 'SEN_4', 'DISAB_1', 'DISAB_4', 'DISAB_5', 'ELI_3']:
        pass
    elif indicator_name in ['POPEMP_19']:
        pass
        
    else:

        df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        if 'Percentage' in df_places_sub.columns:
            df_prod = df_prod.drop('Percentage', axis=1)
        df_prod = df_prod.pivot_table(index='Geography', columns=columns, values=values).reset_index()
        df_prod['Sort'] = pd.Categorical(df_prod['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_prod = df_prod.sort_values(['Sort'])
        df_prod = df_prod.drop(['Sort'], axis=1)
        if indicator_name == 'HSG_7':
            df_prod = df_prod[['Geography', 'Units valued less than 250k', 'Units valued 250k-500k', 'Units valued 500k-750k', 'Units valued 750k-1M', 'Units valued 1M-1.5M', 'Units valued 1.5M-2M', 'Units valued 2M+']]
            df_prod = df_prod.rename(columns = {  'Units valued less than 250k': 'Units valued less than $250k'
                                                , 'Units valued 250k-500k': 'Units valued $250k-$500k'
                                                , 'Units valued 500k-750k': 'Units valued $500k-$750k'
                                                , 'Units valued 750k-1M': 'Units valued $750k-$1M'
                                                , 'Units valued 1M-1.5M': 'Units valued $1M-$1.5M'
                                                , 'Units valued 1.5M-2M': 'Units valued $1.5M-$2M'
                                                , 'Units valued 2M+': 'Units valued $2M+'
                                                })
        if indicator_name == 'HSG_9':
            df_prod = df_prod[['Geography', 'Rent less than 500', 'Rent 500-1,000', 'Rent 1,000-1,500', 'Rent 1,500-2,000', 'Rent 2,000-2,500', 'Rent 2,500-3,000', 'Rent 3,000 or more']]
            df_prod = df_prod.rename(columns = {'Rent less than 500': 'Rent less than $500'
                                            , 'Rent 500-1,000': 'Rent $500-$1,000'
                                            , 'Rent 1,000-1,500': 'Rent $1,000-$1,500'
                                            , 'Rent 1,500-2,000': 'Rent $1,500-$2,000'
                                            , 'Rent 2,000-2,500': 'Rent $2,000-$2,500'
                                            , 'Rent 2,500-3,000': 'Rent $2,500-$3,000'
                                            , 'Rent 3,000 or more': 'Rent $3,000 or more'
                                            })

        if 'Percentage' in df_places_sub.columns:
            df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.drop(values, axis=1)
            
            df_pct = df_pct.pivot_table(index='Geography', columns=columns, values='Percentage').reset_index()
            df_pct['Sort'] = pd.Categorical(df_pct['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_pct = df_pct.sort_values(['Sort'])
            df_pct = df_pct.drop(['Sort'], axis=1)
            if indicator_name == 'HSG_7':
                df_pct = df_pct[['Geography', 'Units valued less than 250k', 'Units valued 250k-500k', 'Units valued 500k-750k', 'Units valued 750k-1M', 'Units valued 1M-1.5M', 'Units valued 1.5M-2M', 'Units valued 2M+']]
                df_pct = df_pct.rename(columns = {'Units valued less than 250k': 'Units valued less than $250k'
                                                , 'Units valued 250k-500k': 'Units valued $250k-$500k'
                                                , 'Units valued 500k-750k': 'Units valued $500k-$750k'
                                                , 'Units valued 750k-1M': 'Units valued $750k-$1M'
                                                , 'Units valued 1M-1.5M': 'Units valued $1M-$1.5M'
                                                , 'Units valued 1.5M-2M': 'Units valued $1.5M-$2M'
                                                , 'Units valued 2M+': 'Units valued $2M+'
                                                })
            if indicator_name == 'HSG_9':
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



def chas_import(PATH_DATA, indicator):
    
    workbooks = os.listdir(PATH_DATA)
    workbooks = [workbook for workbook in workbooks if indicator in workbook]
    print(); print()
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
    
    df_places   = df_places  [['County Name', 'Geography', columns, values, 'Percentage']]
    df_counties = df_counties[[               'Geography', columns, values, 'Percentage']]
    df_mpo      = df_mpo     [[               'Geography', columns, values, 'Percentage']]

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

    if indicator.replace('RHNA_', '') in ['POPEMP_10', 'POPEMP_19', 'POPEMP_20', 'POPEMP_21', 'POPEMP_22', 'POPEMP_25', 'HSG_1', 'HSG_5', 'HSG_6'
                        , 'OVER_4', 'OVER_5', 'OVER_6', 'OVER_8', 'OVER_9', 'FARM_2', 'LGFEM_1', 'LGFEM_3', 'LGFEM_4', 'LGFEM_5'
                        , 'SEN_1', 'SEN_2', 'SEN_3', 'DISAB_3', 'HOMELS_1', 'HOMELS_2', 'HOMELS_3', 'HOMELS_4', 'ELI_2', 'AFFH_1', 'AFFH_2']:

        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_prod = df_plot.pivot_table(index=['Geography', 'Variable'], columns=columns, values=values).reset_index()

        if indicator.replace('RHNA_', '') == 'POPEMP_10':
            vars_to_sort = ['75k or more', '50k to 75k', ' 25k to 50k', '10k to 25k', 'Less than 10k']
        if indicator.replace('RHNA_', '') == 'POPEMP_19':
            vars_to_sort = ['Moved in 2021 or later', 'Moved in 2018 to 2020', 'Moved in 2010 to 2017', 'Moved in 2000 to 2009', 'Moved in 1999 or earlier']

        df_prod['Sort'] = pd.Categorical(df_prod['Variable'], vars_to_sort)
        df_prod = df_prod.sort_values(['Sort'], ascending=[False])
        df_prod = df_prod.drop(['Geography', 'Sort'], axis=1)
        df_pct = df_plot.pivot_table(index=['Geography', 'Variable'], columns=columns, values='Percentage').reset_index()
        df_pct['Sort'] = pd.Categorical(df_prod['Variable'], vars_to_sort)
        df_pct = df_pct.sort_values(['Sort'], ascending=[False])
        df_pct = df_pct.drop(['Geography', 'Sort'], axis=1)
    
    elif indicator.replace('RHNA_', '') in ['HSG_4', 'HSG_11', 'OVER_1', 'OVER_3', 'SEN_4', 'DISAB_1', 'DISAB_4', 'DISAB_5', 'ELI_3']:
        pass
    elif indicator.replace('RHNA_', '') in ['POPEMP_19']:
        pass
        
    else:
        df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        if 'Percentage' in df_places_sub.columns:
            df_prod = df_prod.drop('Percentage', axis=1)
        df_prod = df_prod.pivot_table(index='Geography', columns=columns, values=values).reset_index()
        df_prod['Sort'] = pd.Categorical(df_prod['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_prod = df_prod.sort_values(['Sort'])
        df_prod = df_prod.drop(['Sort'], axis=1)

        if 'Percentage' in df_places_sub.columns:
            df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.drop(values, axis=1)
            
            df_pct = df_pct.pivot_table(index='Geography', columns=columns, values='Percentage').reset_index()
            df_pct['Sort'] = pd.Categorical(df_pct['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_pct = df_pct.sort_values(['Sort'])
            df_pct = df_pct.drop(['Sort'], axis=1)
        
    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod, df_pct
        


def hmda_import(years, counties, dtypes):
    '''
    Years can only be from 2018, to 2024. County codes can be found by using the online tool: https://ffiec.cfpb.gov/data-browser/data/2023?category=counties. 
    '''
    print(''); print('Importing data from HDMA...'); print('')

    list_df = []

    for year in tqdm(years):
        if int(year) < 2018 or int(year) > int(datetime.now().year - 1): 
            print(f"Error: the year {year} does not have accessible data.") 
            continue

        url = 'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?counties=' + ','.join(counties) + '&years=' + str(year)
        
        df = pd.read_csv(url, dtype=dtypes)

        list_df.append(df)
    
    df = pd.concat(list_df, ignore_index=True)

    return df




def chp_sub(df_places, df_counties, county):
    
    df_counties_sub = df_counties[df_counties['Geography'  ] == county]
    df_places_sub   = df_places  [df_places  ['County'     ] == county]

    df_places_sub = df_places_sub.drop('County', axis=1)
    df_places_sub   = df_places_sub  .reset_index(drop=True)
    df_counties_sub = df_counties_sub.reset_index(drop=True)

    return df_places_sub, df_counties_sub


def chp_clean(df_chp):

    df_chp['MPO'] = 'SACOG Region'
    df_chp.loc[df_chp['Risk Level'] == 'HIgh', 'Risk Level'] = 'High'
    df_chp['County'] = df_chp['County'] + ' County'

    df_mpo      = df_chp.groupby(['MPO'           , 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'MPO':'Geography'})
    df_counties = df_chp.groupby(['County'        , 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'County':'Geography'})
    df_places   = df_chp.groupby(['County', 'City', 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'City':'Geography'})

    df_mpo2      = df_chp.groupby(['MPO'           ], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'MPO':'Geography'})
    df_counties2 = df_chp.groupby(['County'        ], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'County':'Geography'})
    df_places2   = df_chp.groupby(['County', 'City'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'City':'Geography'})

    df_mpo2     ['Risk Level'] = 'Total Assisted Units in Database'
    df_counties2['Risk Level'] = 'Total Assisted Units in Database'
    df_places2  ['Risk Level'] = 'Total Assisted Units in Database'

    df_mpo      = pd.concat([df_mpo     , df_mpo2     ])
    df_counties = pd.concat([df_counties, df_counties2])
    df_places   = pd.concat([df_places  , df_places2  ])

    df_mpo      = df_mpo     .merge(df_mpo2     .drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=[          'Geography'], how='left')
    df_counties = df_counties.merge(df_counties2.drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=[          'Geography'], how='left')
    df_places   = df_places  .merge(df_places2  .drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=['County', 'Geography'], how='left')

    df_mpo     ['Percentage'] = df_mpo     ['affordable_units']/df_mpo     ['total_affordable_units']
    df_counties['Percentage'] = df_counties['affordable_units']/df_counties['total_affordable_units']
    df_places  ['Percentage'] = df_places  ['affordable_units']/df_places  ['total_affordable_units']

    df_mpo      = df_mpo     .drop('total_affordable_units', axis=1)
    df_counties = df_counties.drop('total_affordable_units', axis=1)
    df_places   = df_places  .drop('total_affordable_units', axis=1)

    df_mpo     ['Sort'] = pd.Categorical(df_mpo     ['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
    df_counties['Sort'] = pd.Categorical(df_counties['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
    df_places  ['Sort'] = pd.Categorical(df_places  ['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])

    df_mpo      = df_mpo     .sort_values(['Geography', 'Sort']).reset_index(drop=True).drop('Sort', axis=1)
    df_counties = df_counties.sort_values(['Geography', 'Sort']).reset_index(drop=True).drop('Sort', axis=1)
    df_places   = df_places  .sort_values(['Geography', 'Sort']).reset_index(drop=True).drop('Sort', axis=1)

    return df_places, df_counties, df_mpo



def chp_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub=None, df_mpo=None):

    indicator = indicator.replace('RHNA_', '')

    df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
    if 'Percentage' in df_places_sub.columns:
        df_prod = df_prod.drop('Percentage', axis=1)
    df_prod = df_prod.pivot_table(index='Geography', columns=columns, values=values).reset_index()
    df_prod['Sort'] = pd.Categorical(df_prod['Geography'], [jurisdiction, county, 'SACOG Region'])
    df_prod = df_prod.sort_values(['Sort'])
    df_prod = df_prod.drop(['Sort'], axis=1)

    if 'Percentage' in df_places_sub.columns:
        df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_pct = df_pct.drop(values, axis=1)
        
        df_pct = df_pct.pivot_table(index='Geography', columns=columns, values='Percentage').reset_index()
        df_pct['Sort'] = pd.Categorical(df_pct['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_pct = df_pct.sort_values(['Sort'])
        df_pct = df_pct.drop(['Sort'], axis=1)

    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod, df_pct





def plot_rhna(fig, county, jurisdiction, indicator, title):

    path_plots = PATH_OUT / county.replace(' County', '') / jurisdiction / 'plots'

    font_family = 'Microsoft YaHei'
    template = 'plotly_white'
    config={'modeBarButtonsToRemove': ['select', 'lasso', 'toImage'], 'displaylogo': False}

    fig.update_layout(
        legend_title=None
        , title=title # Where does title come from?
        , template=template
        , font_family=font_family
        , xaxis_title=None
        , yaxis_title=None
        , yaxis=dict(tickfont=dict(size=14))
        , xaxis=dict(tickfont=dict(size=14))
        )
    if indicator == 'RHNA_POPEMP_21':
        fig.update_layout(yaxis_title="Households")
    
    if jurisdiction == 'Sacramento':
        fig.show(config=config)
    
    if EXPORT:
        file_html = path_plots / f'{indicator}_.html'
        file_png  = path_plots / f'{indicator}_.png'
        try:
            fig.write_html( file=file_html, config=config)
            fig.write_image(file=file_png , engine='kaleido', scale=1, width=1000, height=500)
        except: pass




def export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct=None):

    if EXPORT:

        path_plots  = PATH_OUT / county.replace(' County', '') / jurisdiction / 'plots'
        path_tables = PATH_OUT / county.replace(' County', '') / jurisdiction / 'tables'

        path_plots .mkdir(parents=True, exist_ok=True)
        path_tables.mkdir(parents=True, exist_ok=True)

        try:
            indicator2 = indicator.replace('RHNA_', '')
            
            try:
                path_plot = path_plots / f'{indicator}_.png'
                img = Image(path_plot)
            except:
                pass
            
            path_juris = PATH_OUT / county.replace(' County', '') / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

            if os.path.isfile(path_juris):
                wb = openpyxl.load_workbook(path_juris)
            else:
                wb = openpyxl.Workbook()
            if indicator2 not in wb.sheetnames:
                wb.create_sheet(indicator2)
            if indicator2 in wb.sheetnames:
                sheet_index = wb.sheetnames.index(indicator2)
                wb.remove(wb[indicator2])
                wb.create_sheet(indicator2, sheet_index)
            ws = wb[indicator2]


            df_prod.to_csv(path_tables / f'{indicator2}_prod.csv', index=False)
            if df_pct is not None:
                df_pct.to_csv(path_tables / f'{indicator2}_pct.csv', index=False)

            df_prod2 = df_prod.reset_index().T.reset_index().T
            df_prod2 = df_prod2.drop(0, axis=1)
            if df_pct is not None:
                df_pct2 = df_pct.reset_index().T.reset_index().T
                df_pct2 = df_pct2.drop(0, axis=1)
            df_title = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_title.iloc[0, 0] = f'{indicator2}: {title}'
            df_subtitle1 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            if indicator2 in ['FARM_2']:
                df_subtitle1.iloc[0, 0] = f'Total: {county} County'
            else:
                df_subtitle1.iloc[0, 0] = 'Total'
            if df_pct is not None:
                df_subtitle2 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
                df_subtitle2.iloc[0, 0] = 'Percentage'

            df_space1 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_space2 = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])

            df_source = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_source.iloc[0, 0] = 'Source'
            df_source.iloc[0, 1] = FILE_YAML[indicator2]['Source'][0]

            df_years = pd.DataFrame([['' for _ in range(len(df_prod2.columns))]])
            df_years.iloc[0, 0] = 'Year(s)'
            df_years.iloc[0, 1] = FILE_YAML[indicator2]['Year(s)'][0]

            df_notes = split_notes(FILE_YAML[indicator2]['Notes'])

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
                df_out = pd.concat([df_title, df_subtitle1, df_prod2,                        df_space1, df_space2, df_source, df_years, df_notes])
            
            for r in dataframe_to_rows(df_out, index=False, header=False):
                ws.append(r)
                
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
            formet_dollars = '$#,##0'
            
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
                            if int(cell_num) > row_num or indicator2 in ['POPEMP_15']:# or (indicator2 in ['HSG_4'] and column == 'C'): # trying to get Percentage column to show up properly
                                cell.value = float(cell.value)
                                cell.number_format = format_percent
                            else:
                                if indicator2 in ['POPEMP_13', 'POPEMP_14']:
                                    cell.number_format = format_ratio
                                else:
                                    cell.value = int(cell.value)
                                    cell.number_format = format_numbers
                        except: pass
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except: pass
                adjusted_width = (max_length + 1) * 1.1
                if column in ['A', 'B']:
                    if column == 'A':
                        ws.column_dimensions[column].width = 20
                    else:
                        ws.column_dimensions[column].width = 35
                else:
                    ws.column_dimensions[column].width = adjusted_width

            try:
                row_num = df_out.shape[0] + 4
                ws.add_image(img, f'B{row_num}') # 21 (style 1)
            except: pass
            wb.save(path_juris)
        except:
            pass






def export_rhna_temp(county, jurisdiction, indicator):

    if EXPORT:

        indicator2 = indicator.replace('RHNA_', '')

        path_juris = PATH_OUT / county.replace(' County', '') / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

        if os.path.isfile(path_juris):
            wb = openpyxl.load_workbook(path_juris)
        else:
            wb = openpyxl.Workbook()
        if indicator2 not in wb.sheetnames:
            wb.create_sheet(indicator2)
        if indicator2 in wb.sheetnames:
            sheet_index = wb.sheetnames.index(indicator2)
            wb.remove(wb[indicator2])
            wb.create_sheet(indicator2, sheet_index)
        ws = wb[indicator2]

        if indicator2 == 'POPEMP_25':
            df_out = pd.DataFrame({'Test': ['Households by Displacement Risk and Tenure', 'This indicator is still a work in progress']})
        if indicator2 == 'RISK_1':
            df_out = pd.DataFrame({'Test': ['Assisted Units at Risk of Conversion', 'This indicator is still a work in progress']})


        for r in dataframe_to_rows(df_out, index=False, header=False):
            ws.append(r)
        ws['A1'].font = Font(bold=True, size=14)


        wb.save(path_juris)
