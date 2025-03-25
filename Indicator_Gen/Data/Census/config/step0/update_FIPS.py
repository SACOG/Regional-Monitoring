

## Preparing Workspace -----------------------------------------------------------------------------------------------------------


## Importing packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
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



# pd.options.display.float_format = '{:.0f}'.format


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

path_csv = path_config / 'step0' / 'csv'


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



year_start = 2023
year_end   = 2023
years_to_import = range(year_start, year_end+1)
years_to_import = [2000, 2010, 2020]



counties=False
msa=False
places=True
congressional_districts=False
state_legislative_districts_upper=False
state_legislative_districts_lower=False
puma=False




## Updating FIPS codes -----------------------------------------------------------------------------------------------------------------------------------


# Use URL to county fips mapping table
# Import county FIPS codes by state
url_fips = "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt"
df_states = pd.read_csv(url_fips, header = None, sep = ',')

df_states.columns = ['State', 'State FIPS', 'County FIPS', 'County Name', 'to be removed']
df_states = df_states[['State', 'State FIPS']].drop_duplicates()

df_states = df_states[df_states['State FIPS'] < 60]
df_states = df_states.reset_index(drop = True)
df_states['State FIPS' ] = df_states['State FIPS' ].astype(str).apply('{:0>2}'.format)

states = df_states['State FIPS'].unique()
states=['51']



if counties:

    print()
    print('Counties ------------------------------------------------------------------------------------------------------------------------')
    print()

    start_time = time.time()

    print()
    print('Importing County FIPS codes...'); print()

    # Use URL to county fips mapping table
    # Import county FIPS codes by state
    url_fips = "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt"
    df_counties = pd.read_csv(url_fips, header = None, sep = ',')


    # Clean and subset FIPS file
    # rename columns
    # clean county name
    # reformat FIPS field

    df_counties.columns = ['State', 'State FIPS', 'County FIPS', 'County Name', 'to be removed']
    df_counties = df_counties[['State', 'State FIPS', 'County FIPS', 'County Name']]
    df_counties['County Name'] = df_counties['County Name'].str.replace(' County', '')
    df_counties = clean_fips(df_counties)


    file_in = path_csv / 'CountyFIPS.csv'
    df_config = pd.read_csv(file_in)
    df_config = clean_fips(df_config)

    df_counties = df_counties.merge(df_config, on=['State', 'State FIPS', 'County FIPS', 'County Name'], how='outer')
    display(df_counties)

    file_out = path_csv / 'CountyFIPS.csv'
    df_counties.to_csv(file_out, index=False)



    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all County FIPS codes")
    print("")



if msa:

    print()
    print('MSA ------------------------------------------------------------------------------------------------------------------------')
    print()


    start_time = time.time()

    list_df_census = []

    print(); print('Importing MSA codes for all states...'); print()

    for year in tqdm(years_to_import, position=0):

        # User inputs for user API key, desired variables
        # Specify which geography to import
        # Concatenate constructed URL
        # Call data using URL
        # Use requests package to call out to the API
        # convert parsed response text to pandas df
        # apply year tag
        
        root_ = f'https://api.census.gov/data/{year}/acs/acs5'
        g_ = '?get='
        variables_ = 'NAME'
        location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*'
        api_key_ = f"&key={api_key}"

        query = f"{root_}{g_}{variables_}{location_}{api_key_}"

        response = requests.get(query).text
        response = ast.literal_eval(response)
        
        df_msa = pd.DataFrame(response[1:], columns = response[0])
        df_msa['Year'] = year

        list_df_census.append(df_msa)


    print()
    print('Concatenating all states together...')

    df_msa = pd.concat(list_df_census)




    print("Cleaning...")

    def re_extract_city(x, exp1=',', exp2='-'):
        if x == 'nan':
            return 'nan'
        else:
            x = x.split(exp1, 1)[0]
            x = x.split(exp2, 1)[0]
            return x

    def re_extract_state(x, exp=','):
        if x == 'nan':
            return 'nan'
        else:
            x = x.split(exp, 1)[1]
            x = x[1:3]
            return x

        
    df_msa['City' ] = df_msa['NAME'].apply(re_extract_city )
    df_msa['State'] = df_msa['NAME'].apply(re_extract_state)
    df_msa['Abbrv'] = df_msa['City'] + ', ' + df_msa['State']

    file_in = path_csv / 'CountyFIPS.csv'
    df_fips = pd.read_csv(file_in)
    df_fips = clean_fips(df_fips)


    df_fips = df_fips[['State', 'State FIPS']].drop_duplicates()

    df_msa = df_msa.merge(df_fips, on='State', how='left')
    df_msa = df_msa.rename(columns = {'NAME':'MSA', 'metropolitan statistical area/micropolitan statistical area':'MSA_ID'})

    peer_msa = [
        'Austin, TX'
        , 'Charlotte, NC'
        , 'Cincinnati, OH'
        , 'Cleveland, OH'
        , 'Columbus, OH'
        , 'Detroit, MI'
        , 'Indianapolis, IN'
        , 'Kansas City, MO'
        , 'Miami, FL'
        , 'Orlando, FL'
        , 'Phoenix, AZ'
        , 'Pittsburgh, PA'
        , 'Portland, OR'
        , 'Riverside, CA'
        , 'Sacramento, CA'
        , 'St. Louis, MO'
        , 'Salt Lake City, UT'
        , 'San Antonio, TX'
        , 'San Diego, CA'
        , 'San Francisco, CA'
        , 'San Jose, CA'
        , 'Tampa, FL'
        , 'Yuba City, CA'
    ]

    df_msa['Peer MSA'] = 'No'
    df_msa.loc[df_msa['Abbrv'].isin(peer_msa), 'Peer MSA'] = 'Yes'

    chamber_study = [
        'Boston, MA'
        , 'Pittsburgh, PA'
        , 'Columbus, OH'
        , 'Nashville, TN'
        , 'Knoxville, TN'
        , 'Dallas, TX'
        , 'Kansas City, MO'
        , 'Madison, WI'
        , 'Sacramento, CA'
        , 'Yuba City, CA'
    ]

    df_msa['Chamber Study'] = 'No'
    df_msa.loc[df_msa['Abbrv'].isin(chamber_study), 'Chamber Study'] = 'Yes'

    df_msa = df_msa[['Year', 'State FIPS', 'State', 'MSA_ID', 'MSA', 'Abbrv', 'Peer MSA', 'Chamber Study']]
    df_msa = df_msa.sort_values(['State FIPS', 'Abbrv', 'Year'], ascending=[True, True, False])
    df_msa = df_msa.dropna()


    # file_out = path_csv / 'MSAcodes.csv'
    # df_msa.to_csv(file_out)


    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all MSA codes")
    print("")






if places:

    print()
    print('Census Designated Places ------------------------------------------------------------------------------------------------------------------------')
    print()


    start_time = time.time()


    list_df_census = []

    print()
    print('Importing place IDs for all states...')
    print()

    for state in tqdm(states, position=0):
        for year in years_to_import:
            
            # User inputs for user API key, desired variables
            # Specify which geography to import
            # Concatenate constructed URL
            # Call data using URL
            # Use requests package to call out to the API
            # convert parsed response text to pandas df
            # apply year tag
            
            if year in [2000, 2010]:
                root_ = f'https://api.census.gov/data/{year}/dec/sf1'
            else:
                root_ = f'https://api.census.gov/data/{year}/dec/dhc'
            g_ = '?get='
            variables_ = 'NAME'
            location_ = '&for=place:*' + '&in=state:' + state
            api_key_ = f"&key={api_key}"

            query = f"{root_}{g_}{variables_}{location_}{api_key_}"
        
            response = requests.get(query).text
            response = ast.literal_eval(response)
            
            df_cdp = pd.DataFrame(response[1:], columns = response[0])
            df_cdp['Year'] = year

            list_df_census.append(df_cdp)


    print()
    print('Concatenating all states together...')

    df_cdp = pd.concat(list_df_census)

    df_cdp = df_cdp.sort_values(['Year', 'state', 'place', 'NAME'], ascending=[False, True, True, True])
    df_cdp = df_cdp.set_index('Year').reset_index()

    def re_remove_post(x, exp = ','):
        if x == 'nan':
            return 'nan'
        else:
            return x.split(exp, 1)[0]
            
    df_cdp['NAME'] = df_cdp['NAME'].apply(re_remove_post)

    file_out = path_csv / 'CDPcodes.csv'
    df_cdp.to_csv(file_out, index=False)


    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all Census Designated Places codes")
    print("")





if congressional_districts:

    print()
    print('Congressional Districts ------------------------------------------------------------------------------------------------------------------------')
    print()


    start_time = time.time()


    list_df_census = []

    print()
    print('Importing Congressional Districts for all states...')
    print()

    for year in tqdm(years_to_import, position=0):
        
        # User inputs for user API key and which variables to import
        # Specify which geography to import
        # Concatenate constructed URL
        # Call data using URL
        # Use requests package to call out to the API
        # convert parsed response text to pandas df
        # apply year tag

        root_ = f'https://api.census.gov/data/{year}/acs/acs5'
        g_ = '?get='
        variables_ = 'NAME'
        location_ = '&for=congressional%20district:*'
        api_key_ = f"&key={api_key}"
    
        query = f"{root_}{g_}{variables_}{location_}{api_key_}"

        response = requests.get(query).text
        response = ast.literal_eval(response)
        
        df_cd = pd.DataFrame(response[1:], columns = response[0])
        df_cd['Year'] = year

        list_df_census.append(df_cd)


    print()
    print('Concatenating all states together...')

    df_cd = pd.concat(list_df_census)


    df_cd = df_cd.sort_values(['Year', 'state', 'congressional district'], ascending = [False, True, True])


    # file_out = path_csv / 'CDcodes.csv'
    # df_cd.to_csv(file_out)


    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all Congressional District codes")
    print()







if state_legislative_districts_upper:

    print()
    print('State Legislative Upper Districts ------------------------------------------------------------------------------------------------------------------------')
    print()




    start_time = time.time()


    print('Importing State Legislative Upper Districts for all states...')
    print()

    list_df_states = []

    for state in tqdm(states):

        list_df_years = []
        
        for year in years_to_import:

            # User inputs for user API key, desired variables and years to import
            # Specify which geography to import
            # Concatenate constructed URL
            # Call data using URL
            # Use requests package to call out to the API
            # convert parsed response text to pandas df
            # apply year tag
            
            root_ = f'https://api.census.gov/data/{year}/acs/acs5'
            g_ = '?get='        
            variables_ = 'NAME'
            location_ = '&for=state%20legislative%20district%20(upper%20chamber):*&in=state:' + str(state)
            api_key_ = f"&key={api_key}"
            
            query = f"{root_}{g_}{variables_}{location_}{api_key_}"
        
            response = requests.get(query).text
            response = ast.literal_eval(response)
            
            df_census = pd.DataFrame(response[1:], columns = response[0])
            
            df_census['Year'] = year
            # df_census['State FIPS Code'] = state
        
            list_df_years.append(df_census)

        try:
            df_state = pd.concat(list_df_years)
            df_state = df_state.reset_index(drop=True)
            list_df_states.append(df_state)
        except: pass

    print()
    print('Concatenating all states together...')

    df_sldu = pd.concat(list_df_states)
    df_sldu  = df_sldu.sort_values(['Year', 'state', 'state legislative district (upper chamber)'], ascending = [False, True, True])

    # file_out = path_csv / 'SLDUcodes.csv'
    # df_sldu.to_csv(file_out)

    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- State Legislative Upper District codes")
    print("")



if state_legislative_districts_lower:

    print()
    print('State Legislative Lower Districts ------------------------------------------------------------------------------------------------------------------------')
    print()



    start_time = time.time()


    print('Importing place IDs for all states...')
    print()

    list_df_states = []

    for state in tqdm(states, position=0):

        list_df_years = []
        
        for year in years_to_import:

            try:
            
                # User inputs for user API key, desired variables and years to import
                # Specify which geography to import
                # Concatenate constructed URL
                # Call data using URL
                # Use requests package to call out to the API
                # convert parsed response text to pandas df
                # apply year tag
                
                root_ = f'https://api.census.gov/data/{year}/acs/acs5'
                g_ = '?get='        
                variables_ = 'NAME'
                location_ = '&for=state%20legislative%20district%20(lower%20chamber):*&in=state:' + str(state)
                api_key_ = f"&key={api_key}"
                
                query = f"{root_}{g_}{variables_}{location_}{api_key_}"
            
                response = requests.get(query).text
                response = ast.literal_eval(response)
                
                df_census = pd.DataFrame(response[1:], columns = response[0])
                
                df_census['Year'] = year
                # df_census['State FIPS Code'] = state
            
                list_df_years.append(df_census)
            except: pass

        try:
            df_state = pd.concat(list_df_years)
            df_state = df_state.reset_index(drop=True)
            list_df_states.append(df_state)
        except: pass

    print()
    print('Concatenating all states together...')

    df_sldl = pd.concat(list_df_states)
    df_sldl = df_sldl.sort_values(['Year', 'state', 'state legislative district (lower chamber)'], ascending = [False, True, True])

    # file_out = path_csv / 'SLDLcodes.csv'
    # df_sldl.to_csv(file_out)


    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update State Legislative Lower District codes")
    print("")



if puma:

    print()
    print('PUMAs --------------------------------------------------------------------------------------------------------------------------------------------')
    print()


    # Use URL to county fips mapping table
    # Import county FIPS codes by state
    url_puma_2020 = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/2020_Census_Tract_to_2020_PUMA.txt"
    url_puma_2010 = "https://www2.census.gov/geo/docs/maps-data/data/rel/2010_Census_Tract_to_2010_PUMA.txt"

    df_puma_2020 = pd.read_csv(url_puma_2020, header=0, sep=',')
    df_puma_2010 = pd.read_csv(url_puma_2010, header=0, sep=',')

    df_puma_2020['Years'] = '2022-2031'
    df_puma_2010['Years'] = '2012-2021'

    df_puma = pd.concat([df_puma_2020, df_puma_2010])


    df_puma['PUMA5CE' ] = df_puma['PUMA5CE' ].astype(str).apply('{:0>5}'.format)
    df_puma['TRACTCE' ] = df_puma['TRACTCE' ].astype(str).apply('{:0>6}'.format)
    df_puma['COUNTYFP'] = df_puma['COUNTYFP'].astype(str).apply('{:0>3}'.format)
    df_puma['STATEFP' ] = df_puma['STATEFP' ].astype(str).apply('{:0>2}'.format)


    file_in = path_csv / '2020_PUMA_Names.csv'
    df_puma_names_2020 = pd.read_csv(file_in)
    file_in = path_csv / '2010_PUMA_Names.csv'
    df_puma_names_2010 = pd.read_csv(file_in)

    df_puma_names_2020['Years'] = '2022-2031'
    df_puma_names_2010['Years'] = '2012-2021'

    df_puma_names = pd.concat([df_puma_names_2020, df_puma_names_2010])

    df_puma_names['PUMA5CE'] = df_puma_names['PUMA5CE'].astype(str).apply('{:0>5}'.format)
    df_puma_names['STATEFP'] = df_puma_names['STATEFP'].astype(str).apply('{:0>2}'.format)

    df_puma = df_puma.merge(df_puma_names, on = ['STATEFP', 'PUMA5CE', 'Years'], how = 'left')


    # file_out = path_csv / 'PUMAcodes.csv'
    # df_puma.to_csv(file_out)


    print("")
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update PUMA codes")


