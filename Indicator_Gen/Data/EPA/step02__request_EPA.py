



export=True



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
import urllib.request, json
pd.set_option('display.max_columns', None)


## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'EPA'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'EPA'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'



## User defined functions ---

path_func = path_config0 / 'Functions.py'

with path_func.open("r") as f:
    exec(f.read())


## Setting the API key ---


# Obtain API Key from the following sources
# Air Quality Index (AQI): https://aqs.epa.gov/aqsweb/documents/data_api.html
# Clean Air Markets (CAM): https://www.epa.gov/power-sector/cam-api-portal#/
# Copy retrieved API key to .txt file for safe keeping

print("User input options:  'AQI', 'CAM', ...")
source = input('Which API source do you want to use? ')
file_api = path_config / 'api_key.txt'
exec(open(file_api).read())
api_key = dict_api[source]
print(api_key)




## Requesting ---


year_min = 1999
year_max = 2024

start_time = time.time()



if source == 'CAM':
    print('Data pipeline not ready yet')


if source == 'AQI':

    indicator_name = 'Health_3'
    root_   = 'https://aqs.epa.gov/data/api/'
    email_  = 'jfontes@sacog.org'
    key_ = api_key
    data_   = 'dailyData'#'annualData'
    geo_    = 'CBSA'
    params  = ['88101', '44201']
    years   = sequence(year_min, year_max, 1) # 1980 earliest year, 1999 better for AQI
    geos    = ['40900']#, '49700'] # Sac and Yuba City
    
    list_df_geos = []
    
    for geo in geos:
        
        print(); print('Importing MSA:', geo); print()
        list_df_params = []
        
        for param in params:
            
            print(); print('Importing parameter:', param)
            list_df_years = []
            
            for year in tqdm(years):
    
                time.sleep(6) # Sleeping for 6 seconds between requests to not upset the EPA overlords
                
                url_to_import = f"{root_}{data_}/by{geo_}?email={email_}&key={key_}&param={param}&bdate={year}0101&edate={year}1231&cbsa={geo}"
                
                with urllib.request.urlopen(url_to_import) as url:
                    dict_aqi = json.load(url)
                df_aqi = pd.DataFrame(dict_aqi['Data'])
                df_aqi['Year_Imported'] = year
                list_df_years.append(df_aqi)
                
            df_params = pd.concat(list_df_years)
            list_df_params.append(df_params)
            
        df_geo = pd.concat(list_df_params)
        list_df_geos.append(df_geo)
        print()
    
    df_epa = pd.concat(list_df_geos)
    df_epa = df_epa.reset_index(drop=True)
    
    print()
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
    print()
    

display(df_epa)



## Exporting ---

if export:
    geography='MSA'
    file_out = path_raw / f'{indicator_name}_{geography}_EPA_raw.csv'
    # df_epa.to_excel(file_out, index=False)
    df_epa.to_csv(file_out, index=False)