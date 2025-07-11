
## Importing packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import os
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
from io import StringIO
from IPython.display import display


export=False


## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'BLS'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'BLS'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'

path_csv = path_config / 'step0' / 'csv'


## User defined functions ---

path_func = path_config0 / 'Functions.py'
path_func_census = path_config / 'bls_functions.py'

with path_func.open("r") as f:
    exec(f.read())

with path_func_census.open("r") as f:
    exec(f.read())



## Setting the API key ---

# Obtain API Key from the following source 
# https://api.census.gov/data/key_signup.html
# Copy retrieved API key to .txt file for safe keeping
file_api = path_config / 'api_key.txt'
# with open(file_api, 'r') as file:
#     dict_api = file.read()
# api_key = dict_api[user]

exec(open(os.path.join(path_config, 'api_key.txt')).read())
api_key = dict_api[user]




print()
print('National Employment, Hours, and Earnings -----------------------------------------------------------------------------------------------------')
print()

## Importing ---

# Set URL of .txt like file
# Set User-Agent as what the webpage is using (follow instructions/video listed/linked above
# Call webpage information using requests package
# Convert text from request from string to pandas data frame (the webpage was basically in table format already, looks to be imported as one big string)


survey = 'CES'
geography = 'national'



# Industry codes
url = 'https://download.bls.gov/pub/time.series/ce/ce.industry'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_industries = pd.read_csv(str_table, sep='\t')
df_industries['industry_code'] = df_industries['industry_code'].astype(str).apply('{:0>8}'.format)
df_industries = df_industries[['industry_code', 'industry_name']].drop_duplicates()

display(df_industries.head())



# Data type codes
url = 'https://download.bls.gov/pub/time.series/ce/ce.datatype'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_datatype = pd.read_csv(str_table, sep='\t')
df_datatype['data_type_code'] = df_datatype['data_type_code'].astype(str).apply('{:0>2}'.format)
display(df_datatype.head())



## Exporting ---

if export:
    file_out = path_csv / f'{survey}_{geography}_industries.csv'
    df_industries.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_{geography}_datatypes.csv'
    df_datatype.to_csv(file_out, index=False)





print()
print('State and Area Employment, Hours, and Earnings -----------------------------------------------------------------------------------------------------')
print()



## Importing ---


# Set URL of .txt like file
# Set User-Agent as what the webpage is using (follow instructions/video listed/linked above
# Call webpage information using requests package
# Convert text from request from string to pandas data frame (the webpage was basically in table format already, looks to be imported as one big string)



survey = 'CES'
geography = 'state_and_area'


# Industry codes
url = 'https://download.bls.gov/pub/time.series/sm/sm.industry'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_industries = pd.read_csv(str_table, sep='\t')
df_industries['industry_code'] = df_industries['industry_code'].astype(str).apply('{:0>8}'.format)
display(df_industries.head())


# Data type codes
url = 'https://download.bls.gov/pub/time.series/sm/sm.data_type'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_datatype = pd.read_csv(str_table, sep='\t')
df_datatype['data_type_code'] = df_datatype['data_type_code'].astype(str).apply('{:0>2}'.format)
display(df_datatype.head())




## Exporting ---

if export:
    file_out = path_csv / f'{survey}_{geography}_industries.csv'
    df_industries.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_{geography}_datatypes.csv'
    df_datatype.to_csv(file_out, index=False)






print()
print('Local Area Unemployment Statistics -----------------------------------------------------------------------------------------------------')
print()



## Importing ---


# Set URL of .txt like file
# Set User-Agent as what the webpage is using (follow instructions/video listed/linked above
# Call webpage information using requests package
# Convert text from request from string to pandas data frame (the webpage was basically in table format already, looks to be imported as one big string)


survey = 'LAUS'


# Area types
url = 'https://download.bls.gov/pub/time.series/la/la.area_type'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_areatypes = pd.read_csv(str_table, sep='\t')
display(df_areatypes.head())



# Areas
url = 'https://download.bls.gov/pub/time.series/la/la.area'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_areas = pd.read_csv(str_table, sep='\t')
display(df_areas.head())




# Measure codes
url = 'https://download.bls.gov/pub/time.series/la/la.measure'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_measures = pd.read_csv(str_table, sep='\t')
df_measures['measure_code'] = df_measures['measure_code'].astype(str).apply('{:0>2}'.format)
display(df_measures.head())





## Exporting ---

if export:
    file_out = path_csv / f'{survey}_areatypes.csv'
    df_areatypes.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_areas.csv'
    df_areas.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_measuretypes.csv'
    df_measures.to_csv(file_out, index=False)









print()
print('State and County Employment and Wages from Quarterly Census of Employment and Wages -----------------------------------------------------------------------------------------------------')
print()


def re_remove_pre(x, exp = ' '):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[1]


def re_remove_post(x, exp = ' '):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[0]



## Importing ---


# Set URL of .txt like file
# Set User-Agent as what the webpage is using (follow instructions/video listed/linked above
# Call webpage information using requests package
# Convert text from request from string to pandas data frame (the webpage was basically in table format already, looks to be imported as one big string)


survey = 'QCEW'


# Area types
url = 'https://www.bls.gov/cew/classifications/areas/area-titles-txt.txt'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_areas = pd.read_csv(str_table, sep='\t', names=['area_code', 'area'])


df_areas['area'     ] = df_areas['area_code'].apply(re_remove_pre)
df_areas['area_code'] = df_areas['area_code'].apply(re_remove_post)

display(df_areas.head())



# Areas
url = 'https://www.bls.gov/cew/classifications/datatype/datatype-titles-txt.txt'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_datatypes = pd.read_csv(str_table, names=['data_type_code'])


df_datatypes['data_type'     ] = df_datatypes['data_type_code'].apply(re_remove_pre )
df_datatypes['data_type_code'] = df_datatypes['data_type_code'].apply(re_remove_post)
df_datatypes['data_type'] = df_datatypes['data_type'].str.replace('\t', '')

display(df_datatypes.head())




# Size codes
url = 'https://www.bls.gov/cew/classifications/size/size-titles-text.txt'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_sizes = pd.read_csv(str_table, names=['size_code'])

df_sizes['size'     ] = df_sizes['size_code'].apply(re_remove_pre )
df_sizes['size_code'] = df_sizes['size_code'].apply(re_remove_post)

display(df_sizes.head())




# Ownership codes
url = 'https://www.bls.gov/cew/classifications/ownerships/ownership-titles-txt.txt'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_owner = pd.read_csv(str_table, names=['owner_code'])


df_owner['owner'     ] = df_owner['owner_code'].apply(re_remove_pre )
df_owner['owner_code'] = df_owner['owner_code'].apply(re_remove_post)
df_owner['owner'] = df_owner['owner'].str.replace('\t', '')


display(df_owner.head())



# Industry codes
url = 'https://www.bls.gov/cew/classifications/industry/industry-titles.txt'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers=headers)
str_table = response.text
str_table = StringIO(str_table)

df_industries = pd.read_csv(str_table, sep='\t', names=['industry_code'])


df_industries['industry_code'] = df_industries['industry_code'].str.replace('\s+', ' ')
df_industries['industry_code'] = df_industries['industry_code'].str.strip()

df_industries['industry'     ] = df_industries['industry_code'].apply(re_remove_pre )
df_industries['industry_code'] = df_industries['industry_code'].apply(re_remove_post)

df_industries['industry'] = df_industries['industry'].str.strip()
df_industries['industry'] = df_industries['industry'].apply(re_remove_pre )

display(df_industries.head())






## Exporting ---

if export:
    file_out = path_csv / f'{survey}_areas.csv'
    df_areas.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_datatypes.csv'
    df_datatypes.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_sizes.csv'
    df_sizes.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_ownerships.csv'
    df_owner.to_csv(file_out, index=False)
    file_out = path_csv / f'{survey}_industries.csv'
    df_industries.to_csv(file_out, index=False)


