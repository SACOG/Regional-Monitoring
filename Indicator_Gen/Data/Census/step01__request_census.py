#!/usr/bin/env python
# coding: utf-8

# ***************************************************************************
# 
# Preparing Workspace
# 
# ***************************************************************************



## Importing packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import os
import re
from tqdm import tqdm
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


## Export setting ---
export=False



# ***************************************************************************
# 
# Preparing Import Parameters
# 
# ***************************************************************************



# Execute script to prepare API request inputs
path_1a = path_code / 'supplemental_scripts' / 'step01a__prepare_api_request_inputs.py'
with path_1a.open("r") as f:
    exec(f.read())



# ***************************************************************************
# 
# Importing
# 
# ***************************************************************************



# Execute script to send API requests
path_1b = path_code / 'supplemental_scripts' / 'step01b__run_API_requests.py'
with path_1b.open("r") as f:
    exec(f.read())


# ***************************************************************************
# 
# Exporting
# 
# ***************************************************************************



if export:

    if geography == 'PUMA':
        estimate = re.sub('ACS', 'PUMS', estimate)
    
    if margin_of_error == 'No':
        end = 'NoME_raw.csv'
    else:
        end = 'raw.csv'
    export_title = f"{indicator_name}_{geography}_{estimate}_{end}"
    
    print(); print()
    print(f"Exporting {export_title} to the following location: ")
    print(path_raw)
    
    file_out = path_raw / export_title
    df_census_raw.to_csv(file_out, index = False)
    
    print()
    print('Successfully exported!')


# ***************************************************************************
# 
# Processing (optional)
# 
# ***************************************************************************


# if geography == 'Counties':
#     mpo = 'No'
# if geography == 'Places':
#     unincorporated = 'No'


df_census = df_census_raw.copy()

if sample_type in ['ACS', 'SUBJECT']:
    df_census = acs_processing_1(df_census, df_vars, geography, margin_of_error)
    # df_census = acs_processing_2(df_census, df_vars, estimate, indicator_name, geography, margin_of_error, year_end, path_main, path_git)
    # df_census = acs_processing_3(df_census, geography)
    # if geography != 'Counties':
    #     df_census = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
    # if geography == 'Counties':
    #     if mpo == 'Yes':
    #         df_census, df_mpo = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars, df_fips)
    #     else:
    #         df_census = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
    display(df_census.head(3))


# if sample_type in ['PUMS', 'FOODSEC']:
#     df_census, groups = pums_processing_1(df_census, df_vars, sample_type, weight)
#     print('Groups: ' + ', '.join(groups))
#     display(df_census)

# ## LEHD processing steps are still a work in progress
# percentages = 'Yes'
# if estimate == 'LEHD':
#     if geography == 'Counties':
#         df_counties, df_mpo = lehd_processing(df_census, geography, indicator_name, percentages, df_fips)
#         display(df_counties)
#     if geography == 'MSA':
#         df_msa = lehd_processing(df_census, geography, indicator_name, percentages)
#         display(df_msa)



# if export:

#     if geography == 'PUMA':
#         estimate = re.sub('ACS', 'PUMS', estimate)
    
#     if margin_of_error == 'No':
#         end = 'NoME_raw.csv'
#     else:
#         end = 'raw.csv'
#     export_title = f"{indicator_name}_{geography}_{estimate}_{end}"
    
#     print(); print()
#     print(f"Exporting {export_title} to the following location: ")
#     print(path_raw)
    
#     file_out = path_raw / export_title
#     df_census.to_csv(file_out, index = False)
    
#     print()
#     print('Successfully exported!')

