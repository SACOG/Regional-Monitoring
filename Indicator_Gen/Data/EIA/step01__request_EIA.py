


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
from IPython.display import display


pd.options.display.float_format = '{:.1f}'.format



## File paths ---

rerun=False
export=True

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'EIA'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'EIA'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'



## User defined functions ---

path_func = path_config0 / 'Functions.py'
with path_func.open("r") as f:
    exec(f.read())

        


## Setitng the API key ---

# Obtain API Key from the following source 
# https://www.eia.gov/opendata/documentation.php
# Copy retrieved API key to .txt file for safe keeping
path_api = path_config / 'api_key.txt'
file_api = open(path_api)
api_key = file_api.read()
file_api.close()




## Requesting ---

# Execute script to prepare API request inputs
path_1 = path_code / 'config' / 'config_file.py'
with path_1.open("r") as f:
    exec(f.read())



# Execute script to send API request
path_2 = path_code / 'supplemental_scripts' / 'API_request.py'
with path_2.open("r") as f:
    exec(f.read())


## Processing ---

list_df = []

for row in range(len(response['response']['data'])):
    list_df.append(pd.DataFrame(response['response']['data'][row], index = [0]))

df_eia = pd.concat(list_df)
df_eia = df_eia.sort_values('period')
df_eia = df_eia.reset_index(drop = True)

display(df_eia.head())


if export:

    # Name of the export
    end = 'raw.csv'
    file_name = f"{indicator}_EIA_{cat}_{route1}_{route2}_{facetOption}_{facet}_{freq}_{end}"


    # Export location
    print(f"Exporting {file_name} to the following location: ")
    print(path_raw)


    # Export
    file_out = path_raw / file_name
    df_eia.to_csv(file_out, index=False)

    print()
    print('Successfully exported!')