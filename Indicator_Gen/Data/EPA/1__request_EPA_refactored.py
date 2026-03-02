"""

EPA Data Request Pipeline - Refactored Version

This script fetches raw air quality data from EPA APIs based on user selections.
Configuration is now driven by epa_indicators.yaml instead of hard-coded values.

Interactive prompts guide user to select:
  - API source (AQI, CAM, etc.)
  - Indicator (Health_3, Health_4, Emissions_1, etc.)
  - Geography (Sacramento MSA, Yuba City MSA, etc.)
  - Years to import
  - Pollutants to download

All selections are saved to runs/ folder for audit trail and reproducibility.

"""

export = False

# ===============================================
# IMPORTS
# ===============================================

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
import sys
from IPython.display import display

pd.set_option('display.max_columns', None)

# ===============================================
# FILE PATHS
# ===============================================

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'EPA'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code = path_git / 'Data' / 'EPA'
path_config0 = path_git / 'config'
path_config = path_code / 'config'

# Add config to path so we can import epa_pre
sys.path.append(str(path_config))

# ===============================================
# LOAD HELPER FUNCTIONS
# ===============================================

# Load shared functions from config0
path_func = path_config0 / 'Functions.py'
with path_func.open("r") as f:
    exec(f.read())

# Load EPA-specific helper functions
import epa_pre as pre

# ===============================================
# LOAD API KEY
# ===============================================

# Obtain API Key from the following sources:
# Air Quality Index (AQI): https://aqs.epa.gov/aqsweb/documents/data_api.html
# Clean Air Markets (CAM): https://www.epa.gov/power-sector/cam-api-portal#/

print(); print()
print("=" * 70)
print("EPA DATA REQUEST PIPELINE - INTERACTIVE MODE")
print("=" * 70)
print()

file_api = path_config / 'api_key.txt'

try:
    exec(open(file_api).read())
except FileNotFoundError:
    print(f"ERROR: API key file not found at {file_api}")
    print("Please create api_key.txt with format:")
    print('  AQI: [your_api_key]')
    print('  CAM: [your_api_key]')
    raise

# ===============================================
# GET USER SELECTIONS VIA YAML + INTERACTIVE PROMPTS
# ===============================================

# Load configuration from YAML
yaml_epa = pre.load_yaml()

# Get user parameters (interactive prompts or from rerun)
rerun = False  # Set to True to reuse previous parameters
(api_source, indicator, geography, years_to_import, 
 year_start, year_end, pollutants, sp_location, folder,
 root_, email_, data_, geo_, available_geos) = pre.api_request_params(yaml_epa, rerun)

# Get API key for selected source
try:
    api_key = dict_api[api_source]
except KeyError:
    print(f"ERROR: API key for source '{api_source}' not found in {file_api}")
    raise

# ===============================================
# MAKE API REQUESTS
# ===============================================

start_time = time.time()

if api_source == 'AQI':
    
    print()
    print("=" * 70)
    print(f"REQUESTING DATA: {indicator}")
    print(f"API Source: {api_source}")
    print(f"Geographies: {geography}")
    print(f"Years: {min(years_to_import)} to {max(years_to_import)}")
    print(f"Pollutants: {', '.join(pollutants)}")
    print("=" * 70)
    print()
    
    # Parse geography string (could be multiple, comma-separated)
    geo_list = [g.strip() for g in geography.split(',')]
    
    list_df_geos = []
    
    for geo in geo_list:
        
        print(f'\nImporting MSA: {geo}')
        print()
        list_df_params = []
        
        for pollutant_code in pollutants:
            
            print(f'  Importing pollutant: {pollutant_code}')
            list_df_years = []
            
            for year in tqdm(years_to_import, desc=f'    Years for {pollutant_code}'):
                
                time.sleep(6)  # EPA rate limit: don't make requests faster than 1 per 6 seconds
                
                # Build URL
                url_to_import = (
                    f"{root_}{data_}/by{geo_}?"
                    f"email={email_}&key={api_key}&param={pollutant_code}&"
                    f"bdate={year}0101&edate={year}1231&{geo_.lower()}={geo}"
                )
                
                # Request
                try:
                    with urllib.request.urlopen(url_to_import) as url:
                        dict_aqi = json.load(url)
                    
                    if 'Data' in dict_aqi and dict_aqi['Data']:
                        df_aqi = pd.DataFrame(dict_aqi['Data'])
                        df_aqi['Year_Imported'] = year
                        df_aqi['Pollutant_Code'] = pollutant_code
                        list_df_years.append(df_aqi)
                        print(f'      ✓ {year}: {len(df_aqi)} rows')
                    else:
                        print(f'      ✗ {year}: No data returned')
                
                except Exception as e:
                    print(f'      ✗ {year}: Error - {str(e)[:50]}')
                    continue
            
            if list_df_years:
                df_params = pd.concat(list_df_years, ignore_index=True)
                list_df_params.append(df_params)
        
        if list_df_params:
            df_geo = pd.concat(list_df_params, ignore_index=True)
            list_df_geos.append(df_geo)
    
    if list_df_geos:
        df_epa = pd.concat(list_df_geos, ignore_index=True)
        df_epa = df_epa.reset_index(drop=True)
        
        print()
        print("=" * 70)
        print("FINISHED!!")
        print(f"Total rows: {len(df_epa)}")
        print(f"Date range: {df_epa['date_local'].min()} to {df_epa['date_local'].max()}")
        print(f"Process completed in {round((time.time() - start_time)/60, 1)} minutes")
        print("=" * 70)
        print()
        
        display(df_epa.head(10))
        print()
        print(f"Data shape: {df_epa.shape}")
        print()

elif api_source == 'CAM':
    
    print()
    print("=" * 70)
    print(f"ERROR: CAM data pipeline not fully implemented yet")
    print("=" * 70)
    print()
    print("The CAM (Clean Air Markets) API structure is different from AQI.")
    print("Implementation coming soon.")
    print()
    df_epa = None

else:
    print(f"ERROR: Unknown API source: {api_source}")
    df_epa = None

# ===============================================
# EXPORT RAW DATA
# ===============================================

if export and df_epa is not None:
    
    filename = pre.set_download_name(indicator, api_source, geography, years_to_import)
    file_out = path_raw / filename
    
    print()
    print("=" * 70)
    print("EXPORTING")
    print("=" * 70)
    print(f"File: {filename}")
    print(f"Location: {path_raw}")
    print()
    
    df_epa.to_csv(file_out, index=False)
    
    print(f"✓ Successfully exported to {file_out}")
    print()

elif not export:
    print()
    print("Note: To save raw data, set export=True at the top of this script")
    print()

