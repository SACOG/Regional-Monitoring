#!/usr/bin/env python
# coding: utf-8




## Preparing Workspace =============================================================================================================



## Importing packages ---

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
exec(open(os.path.join(path_config, 'api_key.txt')).read())
api_key = dict_api[user]
url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'



## Export setting ---

rerun=True
export=True




# Execute script to prepare API request inputs
path_1a = path_code / 'supplemental_scripts' / 'step01a__prepare_api_request_inputs.py'
with path_1a.open("r") as f:
    exec(f.read())





## Processing =============================================================================================================



print('Display data imported from BLS: ')

end = f'{size_code}_{owner_code}_raw.csv'
# end = 'ChamberStudy2026_raw'


export_title = f"{indicator}_{geography}_BLS_{end}.csv"
file_raw = path_raw / export_title
df_bls = pd.read_csv(file_raw)

display(df_bls.head())




# Execute script to prepare data processing parameters
path_2b = path_code / 'supplemental_scripts' / 'step02b__processing.py'
with path_2b.open("r") as f:
    exec(f.read())
    



## Exporting =============================================================================================================



# Update overall about documentations workbook
estimate = 'BLS'
sample_type = survey
df_about = write_about(sample_type      = sample_type
                       , indicator      = indicator
                       , year_start     = year_start
                       , year_end       = year_end
                       , path_config0   = path_config0
                       , estimate       = estimate)
display(df_about)
# with pd.ExcelWriter(os.path.join(path_main, 'About Indicators.xlsx'), mode = 'a', engine = 'openpyxl', if_sheet_exists = 'replace') as writer:
#     df_about.to_excel(writer, index=False, sheet_name=indicator, header=False)




# Set file path for exporting
# paths = [path_main / export_loc / f'{indicator} {folder}', Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")]
paths = [path_main / export_loc / f'{indicator} {folder}']

end = f'{size_code}_{owner_code}.csv'
workbook_name = f"{indicator} {geography} BLS {survey}_{end}.xlsx"


estimate = 'BLS'
sample_type = survey
df_about = write_about(sample_type    = sample_type
                       , indicator    = indicator
                       , year_start   = year_start
                       , year_end     = year_end
                       , path_config0 = path_config0
                       , geography    = geography
                       , estimate     = estimate)
print("About documentation page:")
display(df_about)



if export:
    for path_ in paths:
        path_ = path_ / workbook_name
        
        print(f"Excel files exported here:  {path_}");print()
        print(f"Name of workbook:  {workbook_name}");print()
    
        if indicator == 'Jobs_1':
            if geography == 'MSA':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name='MSA'                )
            
            if geography == 'National':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name='National')
        
        if indicator == 'Jobs_2':
            if geography == 'MSA':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about  .to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls_msa.to_excel(writer, index=False, sheet_name='MSA')
                # workbook_name = f"{indicator} 'MPO' BLS {survey}.xlsx"
                # df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                # with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                #     df_about  .to_excel(writer, index=False, sheet_name='About', header=False)
                #     df_bls_mpo.to_excel(writer, index=False, sheet_name='MPO')
            if geography == 'National':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name='National')
        
        if indicator == 'Jobs_3':
            if geography == 'MSA':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about .to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1_1.to_excel(writer, index=False, sheet_name='Government and Private')
                    df_bls1_2.to_excel(writer, index=False, sheet_name='Goods and Services'    )
        
        if indicator == 'Labor_2':
            if geography == 'MSA':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name='MSA'                )
    
    print()
    print("Successfully exported")





