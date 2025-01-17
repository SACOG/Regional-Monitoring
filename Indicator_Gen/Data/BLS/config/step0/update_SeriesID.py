
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
# pd.options.display.float_format = '{:.0f}'.format


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
with open(file_api, 'r') as file:
    dict_api = file.read()
api_key = dict_api[user]








print()
print('National Employment Code Mappings -----------------------------------------------------------------------------------------------------')
print()

## Importing ---

# Set URL of .txt like file
# Set User-Agent as what the webpage is using (follow instructions/video listed/linked above
# Call webpage information using requests package
# Convert text from request from string to pandas data frame (the webpage was basically in table format already, looks to be imported as one big string)



# Industry codes
url = 'https://download.bls.gov/pub/time.series/ce/ce.industry'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers = headers)
str_table = response.text
str_table = StringIO(str_table)

df_industries = pd.read_csv(str_table, sep = '\t')
df_industries['industry_code'] = df_industries['industry_code'].astype(str).apply('{:0>8}'.format)
display(df_industries.head())

# Supersector codes
url = 'https://download.bls.gov/pub/time.series/ce/ce.supersector'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers = headers)
str_table = response.text
str_table = StringIO(str_table)

df_supersectors = pd.read_csv(str_table, sep = '\t')
df_supersectors['supersector_code'] = df_supersectors['supersector_code'].astype(str).apply('{:0>2}'.format)
display(df_supersectors.head())

# Data type codes
url = 'https://download.bls.gov/pub/time.series/ce/ce.datatype'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers = headers)
str_table = response.text
str_table = StringIO(str_table)

df_datatype = pd.read_csv(str_table, sep = '\t')
df_datatype['data_type_code'] = df_datatype['data_type_code'].astype(str).apply('{:0>2}'.format)
display(df_datatype.head())


## Exporting ---

# file_out = path_csv / 'bls_national_industries.csv'
# df_industries.to_csv(file_out)
# file_out = path_csv / 'bls_national_supersectors.csv'
# df_supersectors.to_csv(file_out)
# file_out = path_csv / 'bls_national_datatypes.csv'
# df_datatype.to_csv(file_out)





print()
print('State and Area Employment Code Mappings -----------------------------------------------------------------------------------------------------')
print()



## Importing ---


# Set URL of .txt like file
# Set User-Agent as what the webpage is using (follow instructions/video listed/linked above
# Call webpage information using requests package
# Convert text from request from string to pandas data frame (the webpage was basically in table format already, looks to be imported as one big string)




# Industry codes
url = 'https://download.bls.gov/pub/time.series/sm/sm.industry'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers = headers)
str_table = response.text
str_table = StringIO(str_table)

df_industries = pd.read_csv(str_table, sep = '\t')
df_industries['industry_code'] = df_industries['industry_code'].astype(str).apply('{:0>8}'.format)
display(df_industries.head())


# Supersector codes
url = 'https://download.bls.gov/pub/time.series/sm/sm.supersector'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers = headers)
str_table = response.text
str_table = StringIO(str_table)

df_supersectors = pd.read_csv(str_table, sep = '\t')
df_supersectors['supersector_code'] = df_supersectors['supersector_code'].astype(str).apply('{:0>2}'.format)
display(df_supersectors.head())


# Data type codes
url = 'https://download.bls.gov/pub/time.series/sm/sm.data_type'
 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
}

response = requests.get(url, headers = headers)
str_table = response.text
str_table = StringIO(str_table)

df_datatype = pd.read_csv(str_table, sep = '\t')
df_datatype['data_type_code'] = df_datatype['data_type_code'].astype(str).apply('{:0>2}'.format)
display(df_datatype.head())





## Exporting ---

# file_out = path_csv / 'bls_state_area_industries.csv'
# df_industries.to_csv(file_out)
# file_out = path_csv / 'bls_state_area_supersectors.csv'
# df_supersectors.to_csv(file_out)
# file_out = path_csv / 'bls_state_area_datatypes.csv'
# df_datatype.to_csv(file_out)


