

## Preparing Workspace -----------------------------------------------------------------------------------------------------------


## Importing packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
from tqdm import tqdm
import re
from datetime import date
import requests
import ast
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import time
import functools as ft
from IPython.display import display
import urllib.request, json



# pd.options.display.float_format = '{:.0f}'.format


## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'Census'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'Census'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'
path_csv = path_config / 'step0' / 'csv'


## User defined functions ---

path_func = path_config0 / 'Functions.py'
path_func_census = path_config / 'census_functions.py'

with path_func.open("r") as f:
    exec(f.read())

with path_func_census.open("r") as f:
    exec(f.read())
        


## Setting API key ---

# Obtain API Key from the following source 
# https://api.census.gov/data/key_signup.html
file_api = path_config / 'api_key.txt'
with open(file_api, 'r') as file:
    api_key = file.read()



ACS=False
PUMS=True
DEC=False
LEHD=False
CPS=False
SUBJECT=False
DP=False



export=True




if ACS:

    print()
    print('ACS ------------------------------------------------------------------------------------------------------------------------')
    print()

    ## ACS5 ---
    ## Organize list of all variables from all years into one nice table
    # Set which years to import
    # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
    # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

    years_to_import = sequence(2020, 2020, 1)
    list_df = []

    for year in tqdm(years_to_import):
        with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/variables.json") as url:
            dict_acs = json.load(url)
        
        df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
        df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
        df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
        df_vars['Year'] = year

        list_df.append(df_vars)

    df_acs5 = pd.concat(list_df)
    df_acs5 = df_acs5.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
    df_acs5 = df_acs5.reset_index(drop=True)



    ## ACS1 ---
    ## Organize list of all variables from all years into one nice table
    # Set which years to import
    # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
    # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

    years_to_import = sequence(2005, 2023, 1)
    # years_to_import = sequence(2019, 2021, 1)
    years_to_import.remove(2020)
    list_df = []

    for year in tqdm(years_to_import):
        with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/variables.json") as url:
            dict_acs = json.load(url)
        
        df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
        df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
        df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
        df_vars['Year'] = year

        list_df.append(df_vars)

    df_acs1 = pd.concat(list_df)
    df_acs1 = df_acs1.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
    df_acs1 = df_acs1.reset_index(drop=True)


    ## Combine all ACS variables
    df_acs1 = df_acs1[df_acs1['Year'] != 2020]
    df_acs5 = df_acs5[df_acs5['Year'] == 2020]

    df_acs = pd.concat([df_acs1, df_acs5])
    df_acs = df_acs.sort_values(['Table', 'Year', 'ID'], ascending = [True, False, True])
    df_acs = df_acs.rename(columns={'attributes':'Attributes', 'label':'Label', 'concept':'Table Name'})
    df_acs = df_acs.reset_index(drop=True)

    df_acs['ID_Attributes'] = df_acs['ID'] + ',' + df_acs['Attributes']
    df_acs['ID_Attributes'] = df_acs['ID_Attributes'].apply(ME_split)

    display(df_acs.head())


    file_acs = path_config / 'census_configuration_file2.xlsx'; sheet_name='ACS'
    df_config = pd.read_excel(file_acs, sheet_name=sheet_name)
    df_config = df_config[['Year', 'ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes2', 'ID2']]

    df_acs1 = df_acs[df_acs['Year'] == df_acs['Year'].max()]
    df_acs2 = df_acs[df_acs['Year']  < df_acs['Year'].max()]

    df_acs1 = df_acs1.merge(df_config[df_config['Year'] == df_config['Year'].max()].drop('Year', axis=1), on=['ID'], how='left')
    df_acs2 = df_acs2.merge(df_config, on=['Year', 'ID'], how='left')

    df_acs = pd.concat([df_acs1, df_acs2])

    df_acs = df_acs[['Table', 'ID', 'Attributes', 'Label', 'Table Name', 'Year', 'Indicator Name', 'Include', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes', 'ID_Attributes2', 'ID2']]
    df_acs = df_acs.drop_duplicates()
    df_acs = df_acs.sort_values(['Table', 'Indicator Name', 'Year', 'ID'], ascending = [True, True, False, True])
    df_acs = df_acs.reset_index(drop=True)

    display(df_acs.head())


    ## Exporting to Git ---

    if export:
        file_out = path_csv / 'ACS.csv'
        df_acs.to_csv(file_out, index=False)





if PUMS:

    print()
    print('PUMS ------------------------------------------------------------------------------------------------------------------------')
    print()


    ## PUMS1 ---
    # initialize empty list to store data frames
    # iterate through each year
        # pull PUMS variables list from json file found on ACS website
        # convert to dictionary
        # convert to pandas data frame
        # apply year tag
        # append to list
    # concatenate all data frames together

    print(); print()
    print('Importing PUMS variables tables by year...'); print()

    years = sequence(2005, 2023, 1)
    years.remove(2020)
    list_df_pums = []


    for year in tqdm(years):

        try:
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/pums/variables.json") as url:
        
                dict_pums = json.load(url)
        
                df_pums = pd.DataFrame.from_dict(dict_pums['variables']).T.reset_index().rename(columns = {'index':'ID'})
                df_pums['Year'] = year
                list_df_pums.append(df_pums)
        except Exception as e: print(e)
        
    df_pums = pd.concat(list_df_pums)
    df_pums = df_pums.dropna(subset=["values"]).reset_index(drop=True)
    print(df_pums.shape)
    display(df_pums.head())



    # create empty list to store data frames
    # iterate through each year
        # create empty list to store data frames
        # subset all variables to year
            # create empty list to store data frames
                # subset pums variables to one ID at a time
                # iterate through all key/value combinations in dictionaries that represent the value mappings to make pandas data frames 
                # store them in list of data frames
            # concatenate specific ID variable mappings together
            # add some labels, clean column names
        # apply year tag
        # convert to pandas data frame
        # store in list of data frames

    # concatenate all data frames together

    print(); print()
    print('Cleaned PUMS variables table:'); print()

    list_df_years = []

    for year in tqdm(years):
        try:
            df_pums_vars = df_pums[df_pums['Year'] == year]
            
            list_df = []
            
            for ID in df_pums_vars['ID'].values:
                
                df_ID = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop = True)
                
                for key in list(df_ID['values'][0].keys()):

                    if key == 'item':
                        dict_values = {
                                        'Value1'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                    , 'Value2'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                    , 'Description': list(list(df_ID['values'].values)[0]['item'].values())
                                    }
                        df_vars = pd.DataFrame(dict_values)
                        
                    if key == 'range':
                        
                        list_range = []
            
                        for value in df_ID['values'][0]['range']:
                            dict_values = {
                                            'Value1'     : [value['min']]
                                        , 'Value2'     : [value['max']]
                                        , 'Description': [value['description']]
                                        }
                            
                            list_range.append(pd.DataFrame(dict_values))
                            
                        df_vars = pd.concat(list_range)
                        
                    df_vars['ID'] = ID
                    df_vars['Label'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop = True)['label'].values[0]
                    df_vars['Suggested Weight'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop = True)['suggested-weight'].values[0]
            
                    df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]
            
                list_df.append(df_vars)
            
            df_pums_vars = pd.concat(list_df)
            df_pums_vars['Year'] = year
            
            list_df_years.append(df_pums_vars)
        except Exception as e: print(e)

    df_pums1 = pd.concat(list_df_years)
    df_pums1 = df_pums1.sort_values(['ID', 'Value1', 'Year'], ascending = [True, True, False])
    df_pums1 = df_pums1.reset_index(drop=True)
    display(df_pums1.head())



    ## PUMS5 ---
    # initialize empty list to store data frames
    # iterate through each year
        # pull PUMS variables list from json file found on ACS website
        # convert to dictionary
        # convert to pandas data frame
        # apply year tag
        # append to list
    # concatenate all data frames together

    print(); print()
    print('Importing PUMS variables tables by year...'); print()

    years = sequence(2020, 2020, 1)
    list_df_pums = []

    for year in tqdm(years):

        try:
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/pums/variables.json") as url:
        
                dict_pums = json.load(url)
        
                df_pums = pd.DataFrame.from_dict(dict_pums['variables']).T.reset_index().rename(columns = {'index':'ID'})
                df_pums['Year'] = year
                list_df_pums.append(df_pums)
        except Exception as e: print(e)
        
    df_pums = pd.concat(list_df_pums)
    df_pums = df_pums.dropna(subset=["values"]).reset_index(drop=True)
    print(df_pums.shape)
    display(df_pums.head())



    # create empty list to store data frames
    # iterate through each year
        # create empty list to store data frames
        # subset all variables to year
            # create empty list to store data frames
                # subset pums variables to one ID at a time
                # iterate through all key/value combinations in dictionaries that represent the value mappings to make pandas data frames 
                # store them in list of data frames
            # concatenate specific ID variable mappings together
            # add some labels, clean column names
        # apply year tag
        # convert to pandas data frame
        # store in list of data frames

    # concatenate all data frames together

    print(); print()
    print('Cleaned PUMS variables table:'); print()

    list_df_years = []

    for year in tqdm(years):
        try:
            df_pums_vars = df_pums[df_pums['Year'] == year]
            
            list_df = []
            
            for ID in df_pums_vars['ID'].values:
                
                df_ID = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop = True)
                
                for key in list(df_ID['values'][0].keys()):

                    if key == 'item':
                        dict_values = {
                                        'Value1'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                    , 'Value2'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                    , 'Description': list(list(df_ID['values'].values)[0]['item'].values())
                                    }
                        df_vars = pd.DataFrame(dict_values)
                        
                    if key == 'range':
                        
                        list_range = []
            
                        for value in df_ID['values'][0]['range']:
                            dict_values = {
                                            'Value1'   : [value['min']]
                                        , 'Value2'     : [value['max']]
                                        , 'Description': [value['description']]
                                        }
                            
                            list_range.append(pd.DataFrame(dict_values))
                            
                        df_vars = pd.concat(list_range)
                        
                    df_vars['ID'] = ID
                    df_vars['Label'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop = True)['label'].values[0]
                    df_vars['Suggested Weight'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop = True)['suggested-weight'].values[0]
            
                    df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]
            
                list_df.append(df_vars)
            
            df_pums_vars = pd.concat(list_df)
            df_pums_vars['Year'] = year
            
            list_df_years.append(df_pums_vars)
        except Exception as e: print(e)

    df_pums5 = pd.concat(list_df_years)
    df_pums5 = df_pums5.sort_values(['ID', 'Value1', 'Year'], ascending = [True, True, False])
    df_pums5 = df_pums5.reset_index(drop=True)



    ## Combining ---

    df_pums1 = df_pums1[df_pums1['Year'] != 2020]
    df_pums5 = df_pums5[df_pums5['Year'] == 2020]

    df_pums = pd.concat([df_pums1, df_pums5])
    df_pums = df_pums.drop_duplicates()
    df_pums['Value1'] = df_pums['Value1'].astype('str')
    df_pums = df_pums.sort_values(['Year', 'ID', 'Value1'], ascending = [False, True, True])
    df_pums = df_pums.reset_index(drop=True)


    file_config = path_config / 'census_configuration_file2.xlsx'; sheet_name='PUMS'
    df_config = pd.read_excel(file_config, sheet_name=sheet_name, dtype={'Value1':'str'})
    df_config = df_config[['ID', 'Value1', 'Indicator Name', 'Include', 'ID2', 'Description2', 'Data Type', 'Table Type']]

    df_pums = df_pums.merge(df_config, on=['ID', 'Value1'], how='left')
    df_pums = df_pums.drop_duplicates()
    df_pums = df_pums.set_index('Year').reset_index()
    display(df_pums.head())


    ## Exporting to Git ---
    if export:
        file_out = path_csv / 'PUMS.csv'
        df_pums.to_csv(file_out, index=False)




if DEC:

    print()
    print('DEC ------------------------------------------------------------------------------------------------------------------------')
    print()



    ## Importing ---

    with urllib.request.urlopen("https://api.census.gov/data/2000/dec/sf1/variables.json") as url:
        dict_dec_2000 = json.load(url)
    df_dec_2000 = pd.DataFrame.from_dict(dict_dec_2000['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df_dec_2000 = df_dec_2000[['ID', 'label', 'concept', 'predicateType', 'group']]
    df_dec_2000['Year'] = 2000
    df_dec_2000['estimate'] = 'sf1'
    df_dec_2000 = df_dec_2000.sort_values(['ID'])
    display(df_dec_2000.head())


    with urllib.request.urlopen("https://api.census.gov/data/2010/dec/sf1/variables.json") as url:
        dict_dec_2010 = json.load(url)
    df_dec_2010 = pd.DataFrame.from_dict(dict_dec_2010['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df_dec_2010 = df_dec_2010[['ID', 'label', 'concept', 'predicateType', 'group']]
    df_dec_2010['Year'] = 2010
    df_dec_2010['estimate'] = 'sf1'
    df_dec_2010 = df_dec_2010.sort_values(['ID'])
    display(df_dec_2010.head())


    with urllib.request.urlopen("https://api.census.gov/data/2020/dec/dp/variables.json") as url:
        dict_dec_2020 = json.load(url)
    df_dec_2020 = pd.DataFrame.from_dict(dict_dec_2020['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df_dec_2020 = df_dec_2020[['ID', 'label', 'concept', 'predicateType', 'group']]
    df_dec_2020['Year'] = 2020
    df_dec_2020['estimate'] = 'dp'
    df_dec_2020 = df_dec_2020.sort_values(['ID'])
    display(df_dec_2020.head())


    with urllib.request.urlopen("https://api.census.gov/data/2020/dec/dhc/variables.json") as url:
        dict_dhc_2020 = json.load(url)
    df_dhc_2020 = pd.DataFrame.from_dict(dict_dhc_2020['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df_dhc_2020 = df_dhc_2020[['ID', 'label', 'concept', 'predicateType', 'group']]
    df_dhc_2020['Year'] = 2020
    df_dhc_2020['estimate'] = 'dhc'
    df_dhc_2020 = df_dhc_2020.sort_values(['ID'])
    display(df_dhc_2020.head())



    ## Combining ---

    df_dec = pd.concat([df_dec_2000, df_dec_2010, df_dec_2020, df_dhc_2020])
    df_dec['Label_clean'] = df_dec['label'].str.replace('Estimate!!', '')
    df_dec['Label_clean'] = df_dec['Label_clean'].str.replace('!!', ' ')
    df_dec['Label_clean'] = df_dec['Label_clean'].str.replace(':', '')

    file_config = path_config / 'census_configuration_file2.xlsx'; sheet_name='DEC'
    df_config = pd.read_excel(file_config, sheet_name=sheet_name)
    df_config = df_config[['ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity']]

    df_dec = df_dec.merge(df_config, on=['ID'], how='left')
    df_dec = df_dec.rename(columns={'label':'Label', 'concept':'Table Name', 'group':'Table'})
    df_dec = df_dec[['Year', 'Table', 'ID', 'Label', 'Table Name', 'predicateType', 'Indicator Name', 'Include', 'estimate', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity']]


    ## Exporting to Git ---
    if export:
        file_out = path_csv / 'DEC.csv'
        df_dec.to_csv(file_out, index=False)



if LEHD:

    print()
    print('LEHD ------------------------------------------------------------------------------------------------------------------------')
    print()

    ## Importing ---

    with urllib.request.urlopen("https://api.census.gov/data/timeseries/qwi/rh/variables.json") as url:
        dict_lehd_rh = json.load(url)

    with urllib.request.urlopen("https://api.census.gov/data/timeseries/qwi/sa/variables.json") as url:
        dict_lehd_sa = json.load(url)

    with urllib.request.urlopen("https://api.census.gov/data/timeseries/qwi/se/variables.json") as url:
        dict_lehd_se = json.load(url)


    df_vars_rh = pd.DataFrame.from_dict(dict_lehd_rh['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df_vars_sa = pd.DataFrame.from_dict(dict_lehd_sa['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df_vars_se = pd.DataFrame.from_dict(dict_lehd_se['variables']).T.reset_index().rename(columns = {'index':'ID'})

    df_vars_rh['Table'] = 'Race by Ethnicity'
    df_vars_sa['Table'] = 'Sex by Age'
    df_vars_se['Table'] = 'Sex by Education'

    df_vars = pd.concat([df_vars_rh, df_vars_sa, df_vars_se])
    df_vars = df_vars.set_index('Table').reset_index()

    print(df_vars.shape)
    display(df_vars.head())



    ## Combining ---

    file_config = path_config / 'census_configuration_file2.xlsx'
    sheet_name='LEHD'
    df_config = pd.read_excel(file_config, sheet_name=sheet_name)
    df_config = df_config[['Table', 'ID', 'Indicator Name', 'Include', 'Sample']]

    df_vars = df_vars.merge(df_config, on=['Table', 'ID'], how='left')
    df_vars.head()


    ## Exporting to Git ---

    if export:
        file_out = path_csv / 'LEHD.csv'
        df_vars.to_csv(file_out, index=False)




if CPS:

    print()
    print('CPS ------------------------------------------------------------------------------------------------------------------------')
    print()

    ## Importing ---

    ## CPS ---
    # initialize empty list to store data frames
    # iterate through each year
        # pull PUMS variables list from json file found on ACS website
        # convert to dictionary
        # convert to pandas data frame
        # apply year tag
        # append to list
    # concatenate all data frames together

    print(); print()
    print('Importing CPS variables tables by year...'); print()

    year_start = 2009
    year_end   = 2023
    years = range(year_start, year_end+1)

    list_df_cps = []

    for year in tqdm(years):
        try:
            if year in [1995, 1997, 1999]:
                url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/apr/variables.json"
            if year in [1998]:
                url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/aug/variables.json"
            if year in [2000]:
                url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/sep/variables.json"
            if year in sequence(2001, 2023, 1):
                url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/dec/variables.json"
                
            with urllib.request.urlopen(url_to_import) as url:
        
                dict_cps = json.load(url)
                df_cps = pd.DataFrame.from_dict(dict_cps['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
                df_cps['Year'] = year
                list_df_cps.append(df_cps)
        except Exception as e: print(e)
        
    df_cps = pd.concat(list_df_cps)
    df_cps = df_cps.reset_index(drop=True)
    print(df_cps.shape)
    display(df_cps.head())


    # create empty list to store data frames
    # iterate through each year
        # create empty list to store data frames
        # subset all variables to year
            # create empty list to store data frames
                # subset pums variables to one ID at a time
                # iterate through all key/value combinations in dictionaries that represent the value mappings to make pandas data frames 
                # store them in list of data frames
            # concatenate specific ID variable mappings together
            # add some labels, clean column names
        # apply year tag
        # convert to pandas data frame
        # store in list of data frames

    # concatenate all data frames together


    print(); print()
    print('Cleaned CPS variables table:'); print()

    list_df_years = []

    for year in tqdm(years):
        df_cps_vars = df_cps[df_cps['Year'] == year]
        
        list_df = []
        
        for ID in df_cps_vars['ID'].values:
            
            df_ID = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop = True)

            if df_ID['values'][0] is np.nan:
                df_vars = pd.DataFrame()
                df_vars['Value1'] = np.nan
                df_vars['Value2'] = np.nan
                df_vars['Description'] = np.nan
                df_vars['ID'] = ID
                df_vars['Label'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['label'].values[0]
                df_vars['Suggested Weight'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['suggested-weight'].values[0]
                df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]

            else:
            
                for key in list(df_ID['values'][0].keys()):
                    
                    if key == 'item':
                        dict_values = {
                                        'Value1'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                    , 'Value2'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                    , 'Description': list(list(df_ID['values'].values)[0]['item'].values())
                                    }
                        df_vars = pd.DataFrame(dict_values)
                        
        
                    if key == 'range':
                        
                        list_range = []
            
                        for value in df_ID['values'][0]['range']:
                            dict_values = {
                                            'Value1'     : [value['min']]
                                        , 'Value2'     : [value['max']]
                                        , 'Description': [value['description']]
                                        }
                            
                            list_range.append(pd.DataFrame(dict_values))
                            
                        df_vars = pd.concat(list_range)
                        
                    df_vars['ID'] = ID
                    df_vars['Label'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['label'].values[0]
                    df_vars['Suggested Weight'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['suggested-weight'].values[0]
            
                    df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]
            
            list_df.append(df_vars)
        
        
        df_cps_vars = pd.concat(list_df)
        df_cps_vars['Year'] = year
        
        list_df_years.append(df_cps_vars)

    df_cps = pd.concat(list_df_years)
    df_cps = df_cps.sort_values(['Year', 'ID', 'Value1'], ascending = [False, True, True])
    df_cps = df_cps.reset_index(drop=True)
    display(df_cps.head())


    ## Combining ---


    file_config = path_config / 'census_configuration_file2.xlsx'
    sheet_name='FOODSEC'
    df_config = pd.read_excel(file_config, sheet_name=sheet_name)
    df_config = df_config[['ID', 'Indicator Name', 'Include', 'ID2', 'Description2', 'Data Type', 'Table Type']]

    df_cps = df_cps.merge(df_config, on=['ID'], how='left')
    df_cps.head()



    ## Exporting to Git ---
    if export:
        file_out = path_csv / 'CPS.csv'
        df_cps.to_csv(file_out, index=False)






if SUBJECT:
        
    print()
    print('SUBJECT ------------------------------------------------------------------------------------------------------------------------')
    print()

    ## ACS5 ---
    ## Organize list of all variables from all years into one nice table
    # Set which years to import
    # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
    # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

    years_to_import = sequence(2020, 2020, 1)
    list_df = []

    for year in tqdm(years_to_import):
        with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/subject/variables.json") as url:
            dict_acs = json.load(url)
        
        df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
        df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
        df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
        df_vars['Year'] = year

        list_df.append(df_vars)

    df_acs5 = pd.concat(list_df)
    df_acs5 = df_acs5.sort_values(['Year', 'ID'], ascending = [False, True])
    df_acs5 = df_acs5.reset_index(drop=True)
    print(df_acs5.shape)
    display(df_acs5.head())



    ## ACS1 ---
    ## Organize list of all variables from all years into one nice table
    # Set which years to import
    # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
    # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

    years_to_import = sequence(2010, 2023, 1)
    years_to_import.remove(2020)
    list_df = []

    for year in tqdm(years_to_import):
        with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/subject/variables.json") as url:
            dict_acs = json.load(url)
        
        df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
        df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
        df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
        df_vars['Year'] = year

        list_df.append(df_vars)

    df_acs1 = pd.concat(list_df)
    df_acs1 = df_acs1.sort_values(['Year', 'ID'], ascending = [False, True])
    df_acs1 = df_acs1.reset_index(drop=True)
    print(df_acs1.shape)
    display(df_acs1.head())



    ## Combining ---

    df_acs1 = df_acs1[df_acs1['Year'] != 2020]
    df_acs5 = df_acs5[df_acs5['Year'] == 2020]

    df_acs = pd.concat([df_acs1, df_acs5])
    df_acs = df_acs.sort_values(['Year', 'ID'], ascending = [False, True])
    df_acs = df_acs.rename(columns={'attributes':'Attributes', 'label':'Label', 'concept':'Table Name'})
    df_acs = df_acs.reset_index(drop=True)

    df_acs['ID_Attributes'] = df_acs['ID'] + ',' + df_acs['Attributes']
    df_acs['ID_Attributes'] = df_acs['ID_Attributes'].apply(ME_split)

    display(df_acs.head())

    file_config = path_config / 'census_configuration_file2.xlsx'; sheet_name='SUBJECT'
    df_config = pd.read_excel(file_config, sheet_name=sheet_name)
    df_config = df_config[['Year', 'ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes2', 'ID2']]

    df_acs1 = df_acs[df_acs['Year'] == df_acs['Year'].max()]
    df_acs2 = df_acs[df_acs['Year']  < df_acs['Year'].max()]

    df_acs1 = df_acs1.merge(df_config[df_config['Year'] == df_config['Year'].max()].drop('Year', axis=1), on=['ID'], how='left')
    df_acs2 = df_acs2.merge(df_config, on=['Year', 'ID'], how='left')

    df_acs = pd.concat([df_acs1, df_acs2])

    df_acs = df_acs[['Table', 'ID', 'Attributes', 'Label', 'Table Name', 'Year', 'Indicator Name', 'Include', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes']]
    df_acs = df_acs.drop_duplicates()
    df_acs = df_acs.sort_values(['Table', 'Year', 'ID'], ascending = [True, False, True])
    df_acs = df_acs.reset_index(drop=True)
    

    display(df_acs.head())



    ## Exporting to Git ---

    if export:
        file_out = path_csv / 'SUBJECT.csv'
        df_acs.to_csv(file_out, index=False)








if DP:

    print()
    print('DP ------------------------------------------------------------------------------------------------------------------------')
    print()

    ## ACS5 ---
    ## Organize list of all variables from all years into one nice table
    # Set which years to import
    # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
    # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

    years_to_import = sequence(2020, 2020, 1)
    list_df = []

    for year in tqdm(years_to_import):
        with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/profile/variables.json") as url:
            dict_acs = json.load(url)
        
        df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
        df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
        df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
        df_vars['Year'] = year

        list_df.append(df_vars)

    df_acs5 = pd.concat(list_df)
    df_acs5 = df_acs5.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
    df_acs5 = df_acs5.reset_index(drop=True)



    ## ACS1 ---
    ## Organize list of all variables from all years into one nice table
    # Set which years to import
    # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
    # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

    years_to_import = sequence(2005, 2023, 1)
    # years_to_import = sequence(2019, 2021, 1)
    years_to_import.remove(2020)
    list_df = []

    for year in tqdm(years_to_import):
        with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/profile/variables.json") as url:
            dict_acs = json.load(url)
        
        df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
        
        df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
        df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
        df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
        df_vars['Year'] = year

        list_df.append(df_vars)

    df_acs1 = pd.concat(list_df)
    df_acs1 = df_acs1.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
    df_acs1 = df_acs1.reset_index(drop=True)


    ## Combine all ACS variables
    df_acs1 = df_acs1[df_acs1['Year'] != 2020]
    df_acs5 = df_acs5[df_acs5['Year'] == 2020]

    df_acs = pd.concat([df_acs1, df_acs5])
    df_acs = df_acs.sort_values(['Table', 'Year', 'ID'], ascending = [True, False, True])
    df_acs = df_acs.rename(columns={'attributes':'Attributes', 'label':'Label', 'concept':'Table Name'})
    df_acs = df_acs.reset_index(drop=True)

    df_acs['ID_Attributes'] = df_acs['ID'] + ',' + df_acs['Attributes']
    df_acs['ID_Attributes'] = df_acs['ID_Attributes'].apply(ME_split)

    display(df_acs.head())


    file_acs = path_config / 'census_configuration_file2.xlsx'; sheet_name='ACS'
    df_config = pd.read_excel(file_acs, sheet_name=sheet_name)
    df_config = df_config[['Year', 'ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes2', 'ID2']]

    df_acs1 = df_acs[df_acs['Year'] == df_acs['Year'].max()]
    df_acs2 = df_acs[df_acs['Year']  < df_acs['Year'].max()]

    df_acs1 = df_acs1.merge(df_config[df_config['Year'] == df_config['Year'].max()].drop('Year', axis=1), on=['ID'], how='left')
    df_acs2 = df_acs2.merge(df_config, on=['Year', 'ID'], how='left')

    df_acs = pd.concat([df_acs1, df_acs2])

    df_acs = df_acs[['Table', 'ID', 'Attributes', 'Label', 'Table Name', 'Year', 'Indicator Name', 'Include', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes', 'ID_Attributes2', 'ID2']]
    df_acs = df_acs.drop_duplicates()
    df_acs = df_acs.sort_values(['Table', 'Indicator Name', 'Year', 'ID'], ascending = [True, True, False, True])
    df_acs = df_acs.reset_index(drop=True)

    display(df_acs.head())


    ## Exporting to Git ---

    if export:
        file_out = path_csv / 'DP.csv'
        df_acs.to_csv(file_out, index=False)


