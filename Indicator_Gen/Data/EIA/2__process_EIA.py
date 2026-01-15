



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

rerun=True
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
path_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring")



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




## Rerun ---

# Configuration notes
print(); print(); print()
indicator = input("Please enter the indicator you want to process: "); print()

file_config = path_config / 'Configurations' / f'{indicator}.txt'
file_config = open(file_config)
config = file_config.read()
file_config.close()
print(config)


list_config = [tuple(text.split(':')) for text in config.split('\n')]
list_config.pop()
dict_api = dict(list_config)



cat         = dict_api['Category'    ].strip()
route1      = dict_api['Route 1'     ].strip()
route2      = dict_api['Route 2'     ].strip()
facetOption = dict_api['Facet Option'].strip()
facet       = dict_api['Facet'       ].strip()
freq        = dict_api['Frequency'   ].strip()




# Execute script to prepare API request inputs
path_1 = path_code / 'config' / 'config_file.py'
with path_1.open("r") as f:
    exec(f.read())




## Processing ---

cat         = df_api['category'   ].values[0]
route1      = df_api['route1'     ].values[0]
route2      = df_api['route2'     ].values[0]
facetOption = df_api['facetOption'].values[0]
facet       = df_api['facet'      ].values[0]
freq        = freq.lower()


end = 'raw.csv'


if indicator == 'Faclities_1':

    df_fact1 = pd.read_csv(os.path.join(path_raw, f"{indicator}_EIA_{cat}_{route1}_{route2}_{facetOption}_california_{freq}_{end}"))


if indicator == 'Road_1':

    file_us = path_raw / f"{indicator}_EIA_{cat}_{route1}_{route2}_{facetOption}_NUS_{freq}_{end}"
    file_ca = path_raw / f"{indicator}_EIA_{cat}_{route1}_{route2}_{facetOption}_SCA_{freq}_{end}"

    df_road1_us = pd.read_csv(file_us)
    df_road1_ca = pd.read_csv(file_ca)

    df_road1_us = df_road1_us[df_road1_us['product-name'] == 'Regular Gasoline']
    df_road1_ca = df_road1_ca[df_road1_ca['product-name'] == 'Regular Gasoline']

    df_eia = pd.concat([df_road1_us, df_road1_ca])
    
    df_eia = df_eia.dropna()
    df_eia = df_eia[df_eia['value'] != 'null']
    
    df_eia = df_eia.sort_values(['period', 'duoarea'], ascending = [False, True])
    df_eia = df_eia.reset_index(drop = True)
    df_eia = df_eia[['period', 'area-name', 'product', 'product-name', 'process-name', 'value']]
    df_eia.columns = ['Year', 'Geography', 'Product', 'Product Name', 'Process', 'Price']
    df_eia['Price'] = df_eia['Price'].astype('float32')
    df_eia['Year' ] = df_eia['Year' ].astype('int')
    df_eia = df_eia[df_eia['Year'] >= 2000]

    df_eia.loc[df_eia['Geography'] == 'U.S.'      , 'Geography'] = 'National'
    df_eia.loc[df_eia['Geography'] == 'CALIFORNIA', 'Geography'] = 'California'
    
    print(df_eia.Year.unique())
    display(df_eia)




## Exporting ---

year_start = df_eia['Year'].min()
year_end = df_eia['Year'].max()
sample_type = 'EIA'
tag = 'Gas Prices'

df_about = write_about(sample_type    = sample_type
                       , indicator    = indicator
                       , year_start   = year_start
                       , year_end     = year_end
                       , path_config0 = path_config0)

display(df_about)






if export:
    path_yaml = path_config / 'eia_indicators.yaml'

    try:
        with open(path_yaml, 'r') as yaml_file:
            dict_config = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


    export_loc = dict_config['Indicators']['Monitoring and Reporting'][indicator]['sp_location']
    workbook_name = f'{indicator} {tag} {sample_type}.xlsx'


    file_out = path_main / export_loc / workbook_name
    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_about.to_excel(writer, index=False, sheet_name='About', header=False)
        df_eia  .to_excel(writer, index=False, sheet_name=tag                  )

    print('Export Location: ' + str(file_out))



    file_out = path_server / 'Data' / workbook_name
    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_about.to_excel(writer, index=False, sheet_name='About', header=False)
        df_eia  .to_excel(writer, index=False, sheet_name=tag                  )

    print('Export Location: ' + str(file_out))

