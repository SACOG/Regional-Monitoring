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

export=True
about=True
update=True
server=False


# Execute script to prepare API request inputs
path_1a = path_code / 'supplemental_scripts' / 'step01a__prepare_api_request_inputs.py'
with path_1a.open("r") as f:
    exec(f.read())
    
display(df_vars.head(3))




if geography == 'PUMA':
    estimate = re.sub('ACS', 'PUMS', estimate)

if margin_of_error == 'No':
    end = 'NoME_raw.csv'
else:
    end = 'raw.csv'
export_title = f"{indicator_name}_{geography}_{estimate}_{end}"

file_out = path_raw / export_title
df_census_raw = pd.read_csv(file_out)
display(df_census_raw.head())



# ***************************************************************************
# 
# Processing
# 
# ***************************************************************************



# # Execute script to prepare API request inputs
# path_2a = path_code / 'supplemental_scripts' / 'step02a__prepare_processing_parameters.py'
# with path_2a.open("r") as f:
#     exec(f.read())
    




## Make copy of raw data
df_census = df_census_raw.copy()
print(); print()

if sample_type in ['ACS', 'SUBJECT']:

    # Replace weird missing values with np.nan
    # Melt data from wide to long
    # Convert imported values to numeric
    # Manually check column names and clean as needed
    # Adjust dollars for inflation, if needed
    # Reorganize margin of error fields
    df_census = acs_processing_1(df_census, df_vars, geography, margin_of_error)
    display(df_census.head(3))

    # Merge cleam label field, variable mapping, race/ethnicity, and sorting field
    # Remove unneeded columns
    df_census = acs_processing_2(df_census, df_vars, estimate, indicator_name, geography, margin_of_error, year_end, path_main, path_git)
    display(df_census.head(3))

    # Create "Categorical" race/ethnicity field for sorting
    # Sort by geography, variable mapping, and race/ethnicity
    # sort and then remove categorical field
    df_census = acs_processing_3(df_census, geography)
    display(df_census.head(3))

    # Final processing step for ACS data
    # Link various FIPS codes
    # Roll up population/households/SE's to the desired geography and variable groupings
    # Calculate percentages by geography, race/ethnicity, and variables
    if geography == 'Places':
        df_places1, df_places2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_places1.head(3))
    if geography == 'Block Groups':
        df_blocks1, df_blocks2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_blocks1.head(3))
    if geography == 'Tracts':
        df_tracts1, df_tracts2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_tracts1.head(3))
    if geography == 'Counties':
        df_counties1, df_counties2, df_mpo1, df_mpo2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars, df_fips)
        display(df_mpo1.head(3))
    if geography == 'MSA':
        df_msa1, df_msa2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_msa1.head(3))
    if geography == 'Congressional Districts':
        df_cd1, df_cd2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_cd1.head(3))
    if geography == 'State Legislative Upper Districts':
        df_sldu1, df_sldu2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_sldu1.head(3))
    if geography == 'State Legislative Lower Districts':
        df_sldl1, df_sldl2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_sldl1.head(3))
    if geography == 'States':
        df_states1, df_states2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_states1.head(3))
    if geography == 'National':
        df_nat1, df_nat2 = acs_processing_4(df_census, estimate, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars)
        display(df_nat1.head(3))



if sample_type in ['PUMS', 'FOODSEC']:
    
    # Clean missing values, standardize how the categories are assigned by number, standardize state FIPS code
    # Convert weighted column to integer, convert value fields to string to use as merge field
    # Reshape data dictionary of values/descriptions and reorganize columns
    # Merge meaningful value descriptions onto imported data
    df_census, groups = pums_processing_1(df_census, df_vars, sample_type, weight)
    print('Groups: ' + ', '.join(groups))
    display(df_census.head(3))

    # Remove rows with missing values
    # Only keep description mappings, remove the original PUMS values
    df_census = pums_processing_2(df_census, sample_type, groups, df_fips, dict_fips, path_git)
    display(df_census.head(3))

    # Cleans race/ethnicity fields
    # Creates additional grouping variables for certain indicators
    # Adjusts income variables by inflation for the latest year
    df_census, groups = pums_processing_3(df_census, groups, indicator_name, path_config0)
    print('Groups: ' + ', '.join(groups))
    display(df_census.head(3))


    # Roll up using suggested weight field
    # Roll up to PUMA, counties, MSA, and MPO
    if sample_type == 'PUMS':
        df_puma, df_counties, df_msa, df_mpo, groups = pums_processing_4(df_census, indicator_name, weight, margin_of_error, MOE_thresh, percentages, groups)
        display(df_puma.head(3), df_counties.head(3), df_msa.head(3), df_mpo.head(3))

    # Roll up using suggested weight field
    # Roll up to counties and MPO
    if sample_type == 'FOODSEC':
        df_counties, df_mpo, groups = food_processing_4(df_census, weight, percentages, groups)
        display(df_counties.head(3), df_mpo.head(3))


if estimate == 'LEHD':
    if geography == 'Counties':
        df_counties, df_mpo = lehd_processing(df_census, geography, indicator_name, percentages, df_fips)
        display(df_counties.head(3), df_mpo.head(3))
    if geography == 'MSA':
        df_msa = lehd_processing(df_census, geography, indicator_name, percentages)
        display(df_msa.head(3))





# Final organization of tables for cleanliness
# Renaming columns, subsetting to only desired columns, ...

print(); print()
print('Final Results: ')
print()

if geography == 'Places':
    df_places1 = rename_census(df_places1        = df_places1
                               , geography       = geography
                               , indicator_name  = indicator_name
                               , margin_of_error = margin_of_error
                               , percentages     = percentages
                               , sample_type     = sample_type)
    display(df_places1)
if geography == 'Block Groups':
    df_blocks1 = rename_census(df_blocks1        = df_blocks1
                               , geography       = geography
                               , indicator_name  = indicator_name
                               , margin_of_error = margin_of_error
                               , percentages     = percentages
                               , sample_type     = sample_type)
    display(df_blocks1)
if geography == 'Tracts':
    df_tracts1 = rename_census(df_tracts1        = df_tracts1
                               , geography       = geography
                               , indicator_name  = indicator_name
                               , margin_of_error = margin_of_error
                               , percentages     = percentages
                               , sample_type     = sample_type)
    display(df_tracts1)
if geography == 'Congressional Districts':
    df_cd1 = rename_census(df_cd1            = df_cd1
                           , geography       = geography
                           , indicator_name  = indicator_name
                           , margin_of_error = margin_of_error
                           , percentages     = percentages
                           , sample_type     = sample_type)
    display(df_cd1)
if geography == 'State Legislative Upper Districts':
    df_sldu1 = rename_census(df_sldu1            = df_sldu1
                               , geography       = geography
                               , indicator_name  = indicator_name
                               , margin_of_error = margin_of_error
                               , percentages     = percentages
                               , sample_type     = sample_type)
    display(df_sldu1)
if geography == 'State Legislative Lower Districts':
    df_sldl1 = rename_census(df_sldl1            = df_sldl1
                               , geography       = geography
                               , indicator_name  = indicator_name
                               , margin_of_error = margin_of_error
                               , percentages     = percentages
                               , sample_type     = sample_type)
    display(df_sldl1)
if geography == 'Counties':
    if sample_type in ['ACS', 'SUBJECT']:
        df_counties1, df_mpo1 = rename_census(df_counties1      = df_counties1
                                              , df_mpo1         = df_mpo1
                                              , geography       = geography
                                              , indicator_name  = indicator_name
                                              , margin_of_error = margin_of_error
                                              , percentages     = percentages
                                              , sample_type     = sample_type
                                              , df_vars         = df_vars)
        display(df_counties1, df_mpo1)
    if sample_type == 'FOODSEC':
        df_counties, df_mpo = rename_census(df_counties         = df_counties
                                              , df_mpo          = df_mpo
                                              , geography       = geography
                                              , indicator_name  = indicator_name
                                              , sample_type     = sample_type
                                              , table_type      = table_type
                                              , groups          = groups)
        display(df_counties, df_mpo)
if geography == 'MSA':
    if sample_type in ['ACS', 'SUBJECT']:
        df_msa1 = rename_census(df_msa1           = df_msa1
                                , geography       = geography
                                , indicator_name  = indicator_name
                                , margin_of_error = margin_of_error
                                , percentages     = percentages
                                , sample_type     = sample_type)
        display(df_msa1)
if geography == 'States':
    if sample_type in ['ACS', 'SUBJECT']:
        df_states1 = rename_census(df_states1         = df_states1
                                    , geography       = geography
                                    , indicator_name  = indicator_name
                                    , margin_of_error = margin_of_error
                                    , percentages     = percentages
                                    , sample_type     = sample_type)
        display(df_states1)
if geography == 'National':
    if sample_type in ['ACS', 'SUBJECT']:
        df_nat1 = rename_census(df_nat1           = df_nat1
                                , geography       = geography
                                , indicator_name  = indicator_name
                                , margin_of_error = margin_of_error
                                , percentages     = percentages
                                , sample_type     = sample_type)
        display(df_nat1)
if geography == 'PUMA':
    df_puma, df_counties, df_msa, df_mpo = rename_census(df_puma           = df_puma
                                                         , df_counties     = df_counties
                                                         , df_msa          = df_msa
                                                         , df_mpo          = df_mpo
                                                         , geography       = geography
                                                         , indicator_name  = indicator_name
                                                         , margin_of_error = margin_of_error
                                                         , percentages     = percentages
                                                         , sample_type     = sample_type
                                                         , groups          = groups
                                                         , table_type      = table_type)
    display(df_puma, df_counties, df_msa, df_mpo)



# ***************************************************************************
# 
# Exporting
# 
# ***************************************************************************


if export:
    if about:
        if update:
            path_about = path_sp / 'Process Revamp' / 'Task 6. Process Map'
            year_start = df_census_raw.Year.min()
            year_end   = df_census_raw.Year.max()
            df_about = write_about(sample_type      = sample_type
                                   , indicator_name = indicator_name
                                   , year_start     = year_start
                                   , year_end       = year_end
                                   , path_config0   = path_config0
                                   , MOE_thresh     = MOE_thresh
                                   , estimate       = estimate)
            file_about = path_about / 'About Indicators.xlsx'
            with pd.ExcelWriter(file_about, mode = 'a', engine = 'openpyxl', if_sheet_exists = 'replace') as writer:
                df_about.to_excel(writer, index = False, sheet_name = indicator_name, header = False)


if export:
    if about:
        if estimate not in ['LEHD', 'CPS']:
            df_about = write_about(sample_type      = sample_type
                                   , indicator_name = indicator_name
                                   , year_start     = year_start
                                   , year_end       = year_end
                                   , path_config0   = path_config0
                                   , geography      = geography
                                   , MOE_thresh     = MOE_thresh
                                   , estimate       = estimate)
        else:
            df_about = write_about(sample_type      = sample_type
                                   , indicator_name = indicator_name
                                   , year_start     = year_start
                                   , year_end       = year_end
                                   , path_config0   = path_config0
                                   , geography      = geography
                                   , estimate       = estimate)
        
        print("About documentation of the output for:", indicator_name)
        display(df_about)



print(); print()

if export:
    if geography == 'PUMA':
        estimate = re.sub('ACS', 'PUMS', estimate)
        workbook_name1 = f"{indicator_name} PUMA {estimate}.xlsx"
        workbook_name2 = f"{indicator_name} Counties {estimate}.xlsx"
        workbook_name3 = f"{indicator_name} MSA {estimate}.xlsx"
        workbook_name4 = f"{indicator_name} MPO {estimate}.xlsx"
        print(workbook_name1)
        print(workbook_name2)
        print(workbook_name3)
        print(workbook_name4)
    
    elif geography == 'Counties':
        workbook_name1 = f"{indicator_name} {geography} {estimate}.xlsx"
        workbook_name2 = f"{indicator_name} MPO {estimate}.xlsx"
        print(workbook_name1)
        print(workbook_name2)
    else:
        workbook_name = f"{indicator_name} {geography} {estimate}.xlsx"
        print(workbook_name)
        print()
    
    path_out_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
    path_out_sp = path_main / export_loc / f"{indicator_name} {folder}"
    
    if 'RHNA' in indicator_name:
        path_out_sp = path_prod / export_loc
    if indicator_name == 'EJ_Analysis':
        path_out_sp = r'I:\Projects\Warren\Environmental_Justice_March_2023\SACOG_EJ_UPDATE_2024\Python\YOUR_OUTPUT_FOLDER\2 - Processed'
    
    if project == 'Monitoring and Reporting':
        if server:
            paths = [path_out_server, path_out_sp]
        else: paths = [path_out_sp]
    else:
        paths = [path_out_sp]
    
    for path_ in paths:
        try:
            path_wb = path_ / workbook_name
        except: pass
        
        if sample_type in ['ACS', 'SUBJECT']:
            if geography == 'Places':
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator_name] = 'Census Designated Places (Jurisdictions)'
                export_indicator(indicator_name, geography, df_places1, path_wb, about)
            if geography == 'Block Groups':
                export_indicator(indicator_name, geography, df_blocks1, path_wb, about)
            if geography == 'Tracts':
                export_indicator(indicator_name, geography, df_tracts1, path_wb, about)
            if geography == 'Counties':
                path_wb = path_ / workbook_name1
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator_name] = 'Counties'
                export_indicator(indicator_name, geography, df_counties1, path_wb, about)
                path_wb = path_ / workbook_name2
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator_name] = 'MPO'
                export_indicator(indicator_name, geography, df_mpo1, path_wb, about)
            if geography == 'MSA':
                export_indicator(indicator_name, geography, df_msa1, path_wb, about)
            if geography == 'Congressional Districts':
                export_indicator(indicator_name, geography, df_cd1, path_wb, about)
            if geography == 'State Legislative Upper Districts':
                export_indicator(indicator_name, geography, df_sldu1, path_wb, about)
            if geography == 'State Legislative Lower Districts':
                export_indicator(indicator_name, geography, df_sldl1, path_wb, about)
            if geography == 'States':
                export_indicator(indicator_name, geography, df_states1, path_wb, about)
            if geography == 'National':
                export_indicator(indicator_name, geography, df_nat1, path_wb, about)
        
        if sample_type == 'PUMS':
            # path_wb = path_ / workbook_name1
            # export_indicator(indicator_name, geography, df_puma, path_wb, about)
            path_wb = path_ / workbook_name2
            if about:
                df_about.loc[df_about['Indicator'] == 'Geography', 'Description'] = 'Counties'
            export_indicator(indicator_name, geography, df_counties, path_wb, about)
            # path_wb = path_ / workbook_name3
            # df_about.loc[df_about['Metadata'] == 'Geography', 'Description'] = 'MSA'
            # export_indicator(indicator_name, geography, df_msa, path_wb, about)
            path_wb = path_ / workbook_name4
            if about:
                df_about.loc[df_about['Indicator'] == 'Geography', 'Description'] = 'MPO'
            export_indicator(indicator_name, geography, df_mpo, path_wb, about)
        
        if sample_type == 'FOODSEC':
            path_wb = path_ / workbook_name1
            if about:
                df_about.loc[df_about['Indicator'] == 'Geography', indicator_name] = 'Counties'
            export_indicator(indicator_name, geography, df_counties, path_wb, about)
            path_wb = path_ / workbook_name2
            if about:
                df_about.loc[df_about['Indicator'] == 'Geography', 'Description'] = 'MPO'
            export_indicator(indicator_name, geography, df_mpo, path_wb, about)
        
        if estimate == 'LEHD':
            if geography == 'Counties':
                path_wb = path_ / workbook_name1
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator_name] = 'Counties'
                export_indicator(indicator_name, geography, df_counties, path_wb, about)
                path_wb = path_ / workbook_name2
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', 'Description'] = 'MPO'
                export_indicator(indicator_name, geography, df_mpo, path_wb, about)
            if geography == 'MSA':
                path_wb = path_ / workbook_name
                export_indicator(indicator_name, geography, df_msa1, path_wb, about)



