


export=False


## Packages ---

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


import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.offline import plot
import plotly.subplots as sp
from plotly.subplots import make_subplots


## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'EPA'
path_main = path_sp / 'Data'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'EPA'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'


## User defined functions ---

path_func = path_config0 / 'Functions.py'

with path_func.open("r") as f:
    exec(f.read())




## Processing ---


start_time = time.time()

print('AQI data:')
print()
file_in = path_raw / 'Health_3_MSA_EPA_raw.csv'
df_aqi_raw = pd.read_csv(file_in)
print(df_aqi_raw.shape)
print(df_aqi_raw['sample_duration'].unique())
print(df_aqi_raw['pollutant_standard'].unique())
print()
display(df_aqi_raw.tail(3))
print();print()

print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")






df_aqi = df_aqi_raw.copy()

df_aqi = df_aqi[~df_aqi['aqi'].isna()]
df_aqi = df_aqi[~df_aqi['pollutant_standard'].isna()]

aqi_grouping = ['cbsa_code', 'cbsa', 'date_local', 'Year_Imported']

df_aqi = df_aqi.groupby(aqi_grouping, as_index=False)['aqi'].max()

conditions = [
            ( (df_aqi['aqi'] >=   0) & (df_aqi['aqi'] <=  50) ),
            ( (df_aqi['aqi'] >=  51) & (df_aqi['aqi'] <= 100) ),
            ( (df_aqi['aqi'] >= 101) & (df_aqi['aqi'] <= 150) ),
            ( (df_aqi['aqi'] >= 151) & (df_aqi['aqi'] <= 200) ),
            ( (df_aqi['aqi'] >= 201) & (df_aqi['aqi'] <= 300) ),
            ( (df_aqi['aqi'] >= 301)                          )
        ]

choices = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
df_aqi["Level of Concern"] = np.select(conditions, choices)

df_aqi['Sort'] = pd.Categorical(df_aqi['Level of Concern'], choices)
df_aqi = df_aqi.sort_values(['cbsa', 'date_local', 'Sort'], ascending = [True, False, True])
df_aqi = df_aqi.drop('Sort', axis=1)
df_aqi = df_aqi.reset_index(drop=True)

df_aqi = df_aqi.rename(columns = {'aqi':'AQI Daily Maximum', 'cbsa_code':'MSA ID', 'cbsa':'MSA', 'Year_Imported':'Year'})


print(df_aqi.shape)
display(df_aqi.head())






indicator = 'Health_3'
year_start = df_aqi['Year'].min()
year_end = df_aqi['Year'].max()
sample_type = 'EPA'
tag = 'AQI'

df_about = write_about(sample_type      = sample_type
                       , indicator = indicator
                       , year_start     = year_start
                       , year_end       = year_end
                       , path_config0   = path_config0)

display(df_about)


if export:
    # Set parameters for export file
    path_out = path_main / 'Vibrant and Inclusive Places' / 'People and Community' / 'Healthy Places' / f'{indicator_name} {tag}'
    workbook = f'{indicator_name} MSA {sample_type}.xlsx'
    file_out = path_out / workbook

    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_about.to_excel(writer, index = False, sheet_name = 'About', header=False)
        df_aqi  .to_excel(writer, index = False, sheet_name = 'MSA'                )

    print('Export Location: ' + str(path_out))



    # Set parameters for export file
    path_out = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
    workbook = f'{indicator_name} MSA {sample_type}.xlsx'
    file_out = path_out / workbook

    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_about.to_excel(writer, index = False, sheet_name = 'About', header=False)
        df_aqi  .to_excel(writer, index = False, sheet_name = 'MSA'                )

    print('Export Location: ' + str(path_out))