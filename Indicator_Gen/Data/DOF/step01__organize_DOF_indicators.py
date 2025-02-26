#!/usr/bin/env python
# coding: utf-8

# ***************************************************************************************
# 
# Preparing Workspace
# 
# ***************************************************************************************



export=True

## Importing packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
from tqdm.auto import tqdm
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
# pd.options.display.float_format = '{:.0f}'.format


## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp   = path_users / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'
path_main = path_sp / 'Data'

path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'DOF'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'
path_out_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")


## User defined functions ---

path_func = path_config0 / 'Functions.py'
with path_func.open("r") as f:
    exec(f.read())

def export_dof(df, indicator_name, geography, path, df_folder):

    if 'webmapping-svr' not in str(path):
        folder = df_folder[df_folder['Indicator'] == indicator_name].Folder.values[0]
        folder = f'{indicator_name} {folder}'
        path = path / folder
    
    print(f"Exporting to the following location: {path}")
    print('')
    
    workbook_name = f"{indicator_name} DOF {geography}.xlsx"
    file_out = path / workbook_name
    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_about.to_excel(writer, index=False, header=False, sheet_name='About')
        df      .to_excel(writer, index=False              , sheet_name='Data' )



# ***************************************************************************************
# 
# Preparing Import Parameters
# 
# ***************************************************************************************

# These urls listed below can be copied and pasted into your browser, so you can see the exact table we are importing.  The tables (and url) can also be found here https://dof.ca.gov/forecasting/demographics/.  Click on "Estimates" to access tables.
# 
# 
# ### Population Estimates
# 
# E4
# 
# - 2020 to 2024 -> https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/E-4_2024_InternetVersion.xlsx
# - 2010 to 2020 -> https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/E-4_2010-2020-Internet-Version.xlsx
# - 2000 to 2010 -> https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/E4_2000-2010_Report_Final_EOC_000.xlsx
# 
# ### Population and Housing Estimates
# 
# E5
# 
# - 2020 to 2024 -> https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/E-5-2024_Geo_InternetVersion.xlsx
# 
# 
# E8
# 
# - 2010 to 2020 -> https://dof.ca.gov/wp-content/uploads/sites/352/2023/11/E-8_2010_2020_by_Geo_Internet.xlsx
# - 2000 to 2010 -> https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/Closed_E8_Full_Decade_Final_v2.xlsx
# 
# 
# 
# NOTE -  _Sometimes, the tables are adjusted (even older tables).  The code below makes certain assumptions about the tables (like how many rows we need to skip to get the column headers correct).  If the code below errors out, you will need to manually check each tables at the links listed above to make sure that the tables are in the format as coded below._



## Import E5 and E8 DOF data ##

# Set custom browser user agent so that DOF doesn't deny your request to access data
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0'}

# Organize E5/E8 urls by year
dict_url = {
    2020:"https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/E-5-2024_Geo_InternetVersion.xlsx"
    , 2010:"https://dof.ca.gov/wp-content/uploads/sites/352/2023/11/E-8_2010_2020_by_Geo_Internet.xlsx"
    , 2000:"https://dof.ca.gov/wp-content/uploads/sites/352/Forecasting/Demographics/Documents/Closed_E8_Full_Decade_Final_v2.xlsx"
}

# Import Area Codes
df_fips = pd.read_excel(os.path.join(path_config0, 'Area Codes.xlsx'), sheet_name = 'CountyFIPS')
df_fips = df_fips[df_fips['State'] == 'CA'].dropna()

df_fips['County FIPS'] = df_fips['County FIPS'].astype(str).apply('{:0>3}'.format)
df_fips['State FIPS' ] = df_fips['State FIPS' ].astype(str).apply('{:0>2}'.format)

SACOG_counties = df_fips[df_fips['MPO'] == 'SACOG']['County Name'].values

print(SACOG_counties)
display(df_fips.head())


# ***************************************************************************************
# 
# Importing
# 
# ***************************************************************************************

# _Import code was last updated on Aug 7, 2024_



print(); print()

# Import E5 and E8 DOF Data
path_import = path_code / 'supplemental_scripts' / 'import_DOF_data.py'
with path_import.open("r") as f:
    exec(f.read())


# Mariposa, Alpine, Trinity not included in the "Cities" df because they don't have any jurisdictions


# Export raw data in full
path_out_sp = path_main / 'Vibrant and Inclusive Places' / 'People and Community' / 'Pop and Demographics'
paths = [path_out_sp, path_out_server]
# paths = [path_out_sp]





print(); print()


# All of CA
df_cities2  = df_cities .copy()
df_balance2 = df_balance.copy()

df_balance2['Jurisdiction'] = 'Unincorporated'
df_cities3 = pd.concat([df_cities2, df_balance2])

df_cities3 = df_cities3.sort_values(['County', 'Jurisdiction', 'Year'], ascending = [True, True, False])

if export:
    df_cities3.to_excel(os.path.join(path_out_sp, 'DOF_E5_and_E8_Jurisdictions.xlsx'), index = False)
    
display(df_cities3.head())



# ***************************************************************************************
# 
# Organize Indicators
# 
# ***************************************************************************************



# Import folder name table
file_in = path_config / 'DOF_configuration_file.xlsx'
df_folder = pd.read_excel(file_in, sheet_name = 'Indicators')

# Sample we are pulling from
sample_type = 'DOF'
year_start = 2000
year_end = 2024





print(); print()


## Pop_1 -------------------------------------------------------------------------------------------------


indicator_name = 'Pop_1'

# Import about table
geography = 'Counties'
df_about = write_about(sample_type, indicator_name, year_start, year_end, path_config0)
print("About page documentation table:")
display(df_about)
print()

# Organize indicator
df_pop1 = df_counties[df_counties['County'].isin(SACOG_counties)]
df_pop1 = df_pop1[['County', 'Year', 'Population', 'Household Population']].drop_duplicates()


# View
print('Indicator table:')
display(df_pop1.head())


# Export
if export:
    for path in paths:
        export_dof(df_pop1, indicator_name, geography, path, df_folder)


print()
print("Successfully exported!   \m/( -_- )")





print(); print()


df_plot = df_pop1.copy()

x = 'Year'
y = 'Population'
color = 'County'
labels = 'County'

fig = px.line(df_plot, x=x, y=y, color=color, markers=True, labels=labels)
fig.update_layout(title = 'Population by County')

fig.show()





print(); print()

## Pop_2 -------------------------------------------------------------------------------------------------


indicator_name = 'Pop_2'


## Jurisdictions ---

# Import about table
geography = 'Jurisdictions'
df_about = write_about(sample_type, indicator_name, year_start, year_end, path_config0)

df_pop2 = df_cities[df_cities['County'].isin(SACOG_counties)]
df_pop2_balance = df_balance[df_balance['County'].isin(SACOG_counties)]
df_pop2_balance['Jurisdiction'] = 'Unincorporated'

df_pop2 = pd.concat([df_pop2, df_pop2_balance])  
df_pop2 = df_pop2[['County', 'Jurisdiction', 'Year', 'Population', 'Household Population']]
df_pop2 = df_pop2[df_pop2['Jurisdiction'] != 'Incorporated']
df_pop2 = df_pop2.sort_values(['Jurisdiction', 'Year'], ascending = [True, True])
df_pop2['Population_GR'          ] = df_pop2['Population'          ].pct_change()*100
df_pop2['Household Population_GR'] = df_pop2['Household Population'].pct_change()*100
df_pop2.loc[df_pop2['Year'] == 2000, 'Population_GR'          ] = np.nan
df_pop2.loc[df_pop2['Year'] == 2000, 'Household Population_GR'] = np.nan
df_pop2.loc[df_pop2['Population_GR'          ] == np.inf, 'Population_GR'          ] = np.nan
df_pop2.loc[df_pop2['Household Population_GR'] == np.inf, 'Household Population_GR'] = np.nan
df_pop2 = df_pop2.sort_values(['County', 'Jurisdiction', 'Year'], ascending = [True, True, False])

# Export
if export:
    for path in paths:
        export_dof(df_pop2, indicator_name, geography, path, df_folder)



## Counties ---

# Import about table
geography = 'Counties'
df_about = write_about(sample_type, indicator_name, year_start, year_end, path_config0)

df_pop2 = df_counties[df_counties['County'].isin(SACOG_counties)]
df_pop2 = df_pop2[['County', 'Year', 'Population', 'Household Population']]
df_pop2 = df_pop2[df_pop2['County'] != 'Incorporated']
df_pop2 = df_pop2.sort_values(['County', 'Year'], ascending = [True, True])
df_pop2['Population_GR'          ] = df_pop2['Population'          ].pct_change()*100
df_pop2['Household Population_GR'] = df_pop2['Household Population'].pct_change()*100
df_pop2.loc[df_pop2['Year'] == 2000, 'Population_GR'          ] = np.nan
df_pop2.loc[df_pop2['Year'] == 2000, 'Household Population_GR'] = np.nan
df_pop2.loc[df_pop2['Population_GR'          ] == np.inf, 'Population_GR'          ] = np.nan
df_pop2.loc[df_pop2['Household Population_GR'] == np.inf, 'Household Population_GR'] = np.nan
df_pop2 = df_pop2.sort_values(['County', 'Year'], ascending = [True, False])

# Export
if export:
    for path in paths:
        export_dof(df_pop2, indicator_name, geography, path, df_folder)



# 5 year time lapses
print("About page documentation table:")
df_about.loc[df_about['Indicator'] == 'Year(s)', indicator_name] = f"{year_start}-{year_end}, 5-Year Time Series"
display(df_about)
print('')

df_pop2_5 = df_counties[df_counties['County'].isin(SACOG_counties)]
df_pop2_5 = df_pop2_5[df_pop2_5['Year'].isin([2000, 2005, 2010, 2015, 2020, 2024])]
df_pop2_5 = df_pop2_5[['County', 'Year', 'Population']]
df_pop2_5 = df_pop2_5.sort_values(['County', 'Year'], ascending = [True, True])
df_pop2_5['Population_Diff'] = df_pop2_5.groupby('County')['Population'].diff()
df_pop2_5['Year_Diff'] = df_pop2_5.groupby('County')['Year'].diff()
df_pop2_5['Year_Diff'].fillna(1, inplace=True)  # Assuming the difference of one year when NaN, adjust if needed
df_pop2_5['Population_Diff'].fillna(0, inplace=True)

df_pop2_5['Previous_POP'] = df_pop2_5.groupby('County')['Population'].shift(1)
df_pop2_5['Result'] = round(((df_pop2_5['Population_Diff']) / df_pop2_5['Previous_POP']) * 100 / df_pop2_5['Year_Diff'], 1)
df_pop2_5 = df_pop2_5[~df_pop2_5['Result'].isna()]
df_pop2_5 = df_pop2_5.sort_values(['County', 'Year'], ascending = [True, False])


df_pop2_5 = df_pop2_5.pivot_table(index = ['County']
                                 , columns = 'Year'
                                 , values = 'Result').reset_index()

df_pop2_5.columns = ['County', '2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2024']

df_pop2_5['2000-2005'] = df_pop2_5['2000-2005'].astype('str').apply(lambda x: str(x)+'%')
df_pop2_5['2005-2010'] = df_pop2_5['2005-2010'].astype('str').apply(lambda x: str(x)+'%')
df_pop2_5['2010-2015'] = df_pop2_5['2010-2015'].astype('str').apply(lambda x: str(x)+'%')
df_pop2_5['2015-2020'] = df_pop2_5['2015-2020'].astype('str').apply(lambda x: str(x)+'%')
df_pop2_5['2020-2024'] = df_pop2_5['2020-2024'].astype('str').apply(lambda x: str(x)+'%')


print("Indicator Table: ")
display(df_pop2_5.head())

# Export
geography = 'Counties_5 Year Time Series'
if export:
    for path in paths:
        export_dof(df_pop2_5, indicator_name, geography, path, df_folder)

print()
print("Successfully exported!   \m/( -_- )")

print(); print()




print(); print()


df_plot = df_pop2.copy()
df_plot['Population_GR'] = round(df_plot['Population_GR']*100, 1)

x = 'Year'
y = 'Population_GR'
color = 'County'
labels = 'County'

fig = px.line(df_plot, x=x, y=y, color=color, markers=True, labels=labels)
fig.add_hline(y = 0, line_dash = 'dash', line_color = 'black')
fig.update_layout(title = 'Population Growth Rate by County (%)')

fig.show()





print(); print()


## Pop_5 -------------------------------------------------------------------------------------------------


indicator_name = 'Pop_5'


## Jurisdiction ---

# Import about table
geography = 'Jurisdictions'
df_about = write_about(sample_type, indicator_name, year_start, year_end, path_config0)

df_pop5 = df_cities[df_cities['County'].isin(SACOG_counties)]
df_pop5_balance = df_balance[df_balance['County'].isin(SACOG_counties)]
df_pop5_balance['Jurisdiction'] = 'Unincorporated'
df_pop5 = pd.concat([df_pop5, df_pop5_balance])  

df_pop5 = df_pop5[['MPO', 'County', 'Jurisdiction', 'Year', 'Population', 'Household Population']]
df_pop5 = df_pop5[df_pop5['Jurisdiction'] != 'Incorporated']
df_pop5 = df_pop5.sort_values(['MPO', 'County', 'Jurisdiction', 'Year'], ascending = [True, True, True, True])
df_pop5['Population_GR'          ] = df_pop5['Population'          ].pct_change()
df_pop5['Household Population_GR'] = df_pop5['Household Population'].pct_change()
df_pop5.loc[df_pop5['Year'] == 2000, 'Population_GR'          ] = np.nan
df_pop5.loc[df_pop5['Year'] == 2000, 'Household Population_GR'] = np.nan
df_pop5.loc[df_pop5['Population_GR'          ] == np.inf, 'Population_GR'          ] = np.nan
df_pop5.loc[df_pop5['Household Population_GR'] == np.inf, 'Household Population_GR'] = np.nan
df_pop5 = df_pop5.sort_values(['MPO', 'County', 'Jurisdiction', 'Year'], ascending = [True, True, True, False])

# Export
if export:
    for path in paths:
        export_dof(df_pop5, indicator_name, geography, path, df_folder)



# Counties ---

# Import about table
geography = 'Counties'
df_about = write_about(sample_type, indicator_name, year_start, year_end, path_config0)

df_pop5 = df_counties[['MPO', 'County', 'Year', 'Population', 'Household Population']]
df_pop5 = df_pop5[df_pop5['County'] != 'Incorporated']
df_pop5 = df_pop5.sort_values(['County', 'Year'], ascending = [True, True])
df_pop5['Population_GR'          ] = df_pop5['Population'          ].pct_change()
df_pop5['Household Population_GR'] = df_pop5['Household Population'].pct_change()
df_pop5.loc[df_pop5['Year'] == 2000, 'Population_GR'          ] = np.nan
df_pop5.loc[df_pop5['Year'] == 2000, 'Household Population_GR'] = np.nan
df_pop5.loc[df_pop5['Population_GR'          ] == np.inf, 'Population_GR'          ] = np.nan
df_pop5.loc[df_pop5['Household Population_GR'] == np.inf, 'Household Population_GR'] = np.nan
df_pop5 = df_pop5.sort_values(['MPO', 'County', 'Year'], ascending = [True, True, False])

# Export
if export:
    for path in paths:
        export_dof(df_pop5, indicator_name, geography, path, df_folder)



## MPO ---

# Import about table
geography = 'MPO'
df_about = write_about(sample_type, indicator_name, year_start, year_end, path_config0)
display(df_about)
print()

df_pop5 = df_counties[df_counties['County'] != 'Incorporated']
df_pop5 = df_pop5[['MPO', 'Year', 'Population', 'Household Population']]
df_pop5 = df_pop5.groupby(['MPO', 'Year'], as_index = False).agg(sum)
df_pop5 = df_pop5.sort_values(['MPO', 'Year'], ascending = [True, True])
df_pop5['Population_GR'          ] = df_pop5['Population'          ].pct_change()
df_pop5['Household Population_GR'] = df_pop5['Household Population'].pct_change()
df_pop5.loc[df_pop5['Year'] == 2000, 'Population_GR'          ] = np.nan
df_pop5.loc[df_pop5['Year'] == 2000, 'Household Population_GR'] = np.nan
df_pop5.loc[df_pop5['Population_GR'          ] == np.inf, 'Population_GR'          ] = np.nan
df_pop5.loc[df_pop5['Household Population_GR'] == np.inf, 'Household Population_GR'] = np.nan
df_pop5 = df_pop5.sort_values(['MPO', 'Year'], ascending = [True, False])


# View
print("Indicator Table: ")
display(df_pop5.head())

# Export
if export:
    for path in paths:
        export_dof(df_pop5, indicator_name, geography, path, df_folder)


print()
print("Successfully exported!   \m/( -_- )")

print(); print()




print(); print()


## Just by MPO ##
df_plot = df_pop5.copy()
df_plot['Population_GR'] = round(df_plot['Population_GR']*100, 1)


x = 'Year'
y = 'Population_GR'
color = 'MPO'


fig = px.line(df_plot, x=x, y=y, color=color, markers=True)

fig.add_hline(y = 0, line_dash = 'dash', line_color = 'black')
fig.update_layout(title = 'Population Growth Rate by MPO (%)')

    
fig.show()





