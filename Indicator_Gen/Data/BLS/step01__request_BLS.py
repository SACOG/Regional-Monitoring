



## Preparing Workspace ===============================================================



## Packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import os
import re
from tqdm import tqdm
from datetime import date
from datetime import datetime
import requests
import ast
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import time
import functools as ft
from IPython.display import display
# import pdb; pdb.set_trace()


## File paths ---

rerun=False
export=True

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


## User defined functions ---

path_func = path_config0 / 'Functions.py'
path_func_census = path_config / 'bls_functions.py'

with path_func.open("r") as f:
    exec(f.read())

with path_func_census.open("r") as f:
    exec(f.read())
        

## API key ---

# Obtain API Key from the following source
# https://api.census.gov/data/key_signup.html
# Copy retrieved API key to .txt file for safe keeping
exec(open(os.path.join(path_config, 'api_key.txt')).read())
api_key = dict_api[user]





## Prepare API Request ===========================================================================



# Execute script to prepare API request inputs
path_1a = path_code / 'supplemental_scripts' / 'step01a__prepare_api_request_inputs.py'
with path_1a.open("r") as f:
    exec(f.read())





## Sending API Requests ===========================================================================


# Version 2 (registered API key) allows us to pull:  50 Series ID's per request, 20 years of data per request, 500 requests per day



# Execute script to send API requests
path_1b = path_code / 'supplemental_scripts' / 'step01b__run_API_requests.py'
with path_1b.open("r") as f:
    exec(f.read())




## Exporting ===============================================================================



if export:
    export_title = '_'.join([indicator, geography, 'BLS']) + '_ChamberStudy2026_raw.csv'
    print("Exporting " + export_title + " to the following location: ")
    print(path_raw)
    
    file_out = path_raw / export_title
    df_bls_raw.to_csv(file_out, index=False)
    
    print()
    print('Successfully exported!')





# Processing (optional) ------------------------------------------------------------------------



if indicator == 'Jobs_1':
    df_bls = df_bls_raw.copy()

    df_bls = pd.melt(df_bls, id_vars = ['year', 'periodName'], var_name='seriesID', value_name='value')
    df_bls['date_'] = df_bls['year'].astype('str') + '-' + df_bls['periodName'].astype('str')
    df_bls['date_'] = pd.to_datetime(df_bls['date_'])
    df_bls['value'] = df_bls['value'].astype('float32').apply(lambda x: x*1000)
    df_bls = df_bls.merge(df_series_area, on='seriesID')
    df_bls = df_bls.drop_duplicates()
    df_bls = df_bls.reset_index(drop=True)

    display(df_bls)


