

## Packages ----

import numpy as np
import pandas as pd
import geopandas as gpd
import getpass
from pathlib import Path
import os
from tqdm import tqdm
import requests
import gzip
import io
import re
from datetime import date
from datetime import datetime
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import time
import functools as ft
import yaml
from IPython.display import display

import openpyxl
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
from openpyxl.styles import numbers
from openpyxl.styles import Border, Side
border_thin = Side(style='thin')

# Plotting
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.offline import plot
import plotly.subplots as sp
from plotly.subplots import make_subplots

import warnings
warnings.filterwarnings('ignore')
# import pdb; pdb.set_trace()


## File paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp   = path_users / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'
path_prod = path_sp    / 'Products' / 'RHNA'
path_raw  = path_prod  / 'New Data Collected'

path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_census = path_git  / 'Data' / 'Census'
path_config0 = path_git  / 'config'

path_prod = path_git / 'Products' / 'RHNA'
path_config = path_prod / 'config'
path_yaml = path_config / 'RHNA_indicators.yaml'
path_func = path_config / 'RHNA_functions.py'
path_py = path_prod / 'python'
path_i = Path(r'I:\Projects\Josh\RHNA')

# path_out = Path(r'I:\Projects\Josh\RHNA\Final Products')
# path_out = path_prod / 'Cycle7' / 'Final Products'
path_out = Path(r'C:\Users\jfontes\Documents\Projects\General\RHNA\Final Products')

path_geo = Path(r'I:\Projects\Josh\Geospatial Data\crosswalks')
path_lodes = Path(r'I:\Projects\Josh\Regional Monitoring')


## Indicators ---

indicators = [
    'POPEMP_1'
    , 'POPEMP_2'
    , 'POPEMP_3'
    , 'POPEMP_4'
    , 'POPEMP_5'
    , 'POPEMP_6'
    , 'POPEMP_7'
    , 'POPEMP_8'
    , 'POPEMP_9'
    , 'POPEMP_10'
    , 'POPEMP_11'
    , 'POPEMP_12'
    , 'POPEMP_13'
    , 'POPEMP_14'
    , 'POPEMP_15'
    , 'POPEMP_16'
    , 'POPEMP_17'
    , 'POPEMP_18'
    , 'POPEMP_19'
    , 'POPEMP_20'
    , 'POPEMP_21'
    , 'POPEMP_22'
    , 'POPEMP_23'
    , 'POPEMP_24'
    # , 'POPEMP_25'
    , 'HSG_1'
    , 'HSG_2'
    , 'HSG_3'
    , 'HSG_4'
    , 'HSG_5'
    , 'HSG_6'
    , 'HSG_7'
    , 'HSG_8'
    , 'HSG_9' 
    , 'HSG_10'
    , 'HSG_11'
    # , 'RISK_1'
    , 'OVER_1'
    , 'OVER_2'
    , 'OVER_3'
    , 'OVER_4'
    , 'OVER_5'
    , 'OVER_6'
    , 'OVER_7'
    , 'OVER_8'
    , 'OVER_9'
    , 'FARM_1'
    , 'FARM_2'
    , 'LGFEM_1'
    , 'LGFEM_2'
    , 'LGFEM_3'
    , 'LGFEM_4'
    , 'LGFEM_5'
    , 'SEN_1'
    , 'SEN_2'
    , 'SEN_3'
    , 'SEN_4'
    , 'DISAB_1'
    , 'DISAB_2'
    , 'DISAB_3'
    , 'DISAB_4'
    , 'DISAB_5'
    , 'HOMELS_1'
    , 'HOMELS_2'
    # , 'HOMELS_3' # Can remove
    , 'HOMELS_4'
    , 'HOMELS_5'
    , 'ELI_1'
    , 'ELI_2'
    , 'ELI_3'
    , 'AFFH_1'
    , 'AFFH_2'
    , 'AFFH_3'
    # , 'HHPROJ_1'
]



indicators=['POPEMP_11']



## Main ---


export=False
list_indicators = []

with open(path_yaml, 'r', encoding='utf-8') as yaml_file:
    dict_about = yaml.load(yaml_file, Loader=yaml.SafeLoader)


start_time = time.time()


for indicator in indicators:
    print(); print()
    print(indicator)
    path_run = path_py / f'{indicator}.py'
    with path_run.open("r") as f: exec(f.read())


print(); print()
print('Finished!! Now go outside.')
print(f'Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---')
print(); print()
# takes 45 min for local exporting
# takes ~150 minutes for I drive or SharePoint exporting


## Check indicators ---

print(); print()
print('Indicators processed: '); print()
print(list_indicators)
print()
