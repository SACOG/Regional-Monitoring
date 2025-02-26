

## Preparing Workspace ------------------------------------------------------------------------------------------------------

## Importing packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
from tqdm.auto import tqdm
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

def list_combine(l):
    return "/".join(l)

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




## Importing -------------------------------------------------------------------------------------------------------------------

with urllib.request.urlopen("https://api.census.gov/data.json") as url:
    dict_acs = json.load(url)



## Cleaning ---------------------------------------------------------------------------------------------------------------------

# Convert information from dictionary format to pandas dataframe
# Clean certain columns, fill na, ...
# Combine multiple columns to make one url field
# Import old URL mapping table and join old assignments

df_url2 = pd.DataFrame.from_dict(dict_acs['dataset'])
df_url2 = df_url2[['title', 'c_vintage', 'c_dataset']]
df_url2['c_dataset'] = df_url2['c_dataset'].apply(list_combine)
df_url2['c_vintage'] = df_url2['c_vintage'].fillna(0.0).astype(int).replace(0, pd.NA)
df_url2['c_url'] = 'https://api.census.gov/data' + '/' + df_url2['c_vintage'].astype(str) + '/' + df_url2['c_dataset']
df_url2 = df_url2.sort_values(['c_dataset', 'c_vintage'], ascending = [True, False])


file_config = path_config / 'census_configuration_file.xlsm'
df_url1 = pd.read_excel(file_config, sheet_name='URL')

df_url = df_url2.merge(df_url1, on = ['title', 'c_vintage', 'c_dataset', 'c_url'], how='left')




## Exporting -------------------------------------------------------------------------------------------------------------------

file_csv = path_config / 'step0' / 'csv' / 'census_url.csv'
df_url.to_csv(file_csv, index=False)