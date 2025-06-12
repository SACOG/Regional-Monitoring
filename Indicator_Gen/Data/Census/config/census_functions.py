
import numpy as np
import pandas as pd
import os
import json
from tqdm import tqdm
import re
from datetime import date
import requests
import ast
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import yaml

# Plotting
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio




## Aggregations for processing weighted averages and rolling up margins of error
wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average (or Population or Households)
sqrtsumsq  = lambda x: np.sqrt(np.sum(x**2))                                         # Square root of the sum of squares (to roll up SE's when +/- random variables)

# def sq_weighted(x):
#     weight = 
#     x = (x**2)*weight


# ## Split attributes field in the "Census Configuration File.xlsx" ACS tab to get the ME estimate ID
# def ME_split(text):
#     return ",".join(text.split(',')[0:3:2])

# ## Split attributes field in the "Census Configuration File.xlsx" ACS tab to get the ME estimate ID
# def ME_split(text):
#     if (text is None) or (text is pd.NA) or (text is np.nan):
#         return text
#     else:
#         estimates = text.split(',')
#         pattern = re.compile('.*E$|.*M$')
#         text = ','.join([est for est in estimates if pattern.match(est)])
#         return text


def ME_split(text):
    try:
        estimates = text.split(',')
        pattern = re.compile('.*E$|.*M$')
        text = ','.join([est for est in estimates if pattern.match(est)])
        return text
    except:
        return text


def clean_fips(df):
        
        if 'State FIPS' in df.columns:
            df['State FIPS'] = df['State FIPS'].astype(str).apply('{:0>2}'.format)
        if 'Place ID' in df.columns:
            df['Place ID'] = df['Place ID'].astype(str).apply('{:0>5}'.format)
        if 'County FIPS' in df.columns:
            df['County FIPS'] = df['County FIPS'].astype(str).apply('{:0>3}'.format)
        if 'Congressional District' in df.columns:
            df['Congressional District'] = df['Congressional District'].astype(str).apply('{:0>2}'.format)
        if 'State Legislative Upper District' in df.columns:
            df['State Legislative Upper District'] = df['State Legislative Upper District'].astype(str).apply('{:0>3}'.format)
        if 'State Legislative Lower District' in df.columns:
            df['State Legislative Lower District'] = df['State Legislative Lower District'].astype(str).apply('{:0>3}'.format)

        return df



color_map_comp = {
                "SACOG": "#000000",
                 "California":"#9DC209",
                 "National": "#DC381F",
                 "Peer MSA": "#1E90FF"
}



## Main function used to query data ------

'''
User defined function to import Data from the Census Bureau
User inputs: [api_key, estimate, geography variables, year] to tell Census Bureau that we have access with the API key and
                what type of sample data to pull, which variables we want to import, what year, and which state
The "df_urls" object pulls the "URL" tab from the "Census Configuration File.xlsx", which contains the root URL needed for any API request available here https://api.census.gov/data.html         
Only pulls 1 year at a time (geography IDs, like census tracts, sometimes change at the start of each decade)
'''

def query_census(
        df_urls
        , api_key, estimate, sample, geography, variables, year
        , state=None, county=None, msa=None, puma=None, ZIPcode=None
    ):
        
    # Assert that inputs for estimate and geography are appropriate
    assert estimate  in ['ACS5', 'ACS1', 'DEC', 'CPS' , 'RH', 'SA', 'SE'], "Unacceptable estimate input, requires 'ACS5', 'ACS1', 'DEC', 'LEHD', or 'CPS' "
    assert sample    in ['ACS', 'DEC', 'DHC', 'PUMS', 'FOODSEC' , 'SUBJECT', 'LEHD'], "Unacceptable sample type input, requires 'ACS', 'DEC', 'DHS', 'PUMS', 'FOODSEC', 'SUBJECT', 'RH', 'SA', or 'SE'"
    assert geography in ['Places', 'Block Groups', 'Tracts', 'Counties', 'MSA', 'PUMA', 'ZIP Codes', 'Congressional Districts', 'State Legislative Upper Districts', 'State Legislative Lower Districts', 'States', 'National'], "Unacceptable geography input, requires 'Places', 'Block Groups', 'Tracts', 'Counties', 'MSA', or 'PUMA' "


    ## Construct URL
    df_url = df_urls[
          (df_urls['Sample'   ] == sample  )
        & (df_urls['Estimate' ] == estimate)
        & (df_urls['c_vintage'] == year    )
        ]

    # Create rootpath and specify dataset type
    root_ = df_url['c_url'].values[0]
    g_ = '?get='

    if sample == 'LEHD':
        root_ = re.sub('<NA>/', '', root_)

    # User inputs for user API key, desired variables and years to import
    api_key_ = f"&key={api_key}"
    variables_ = variables

    # Specify which geography to import
    if geography == 'ZIP Codes':
        location_ = '&for=zip%20code%20tabulation%20area:' + ZIPcode
    if geography == 'Congressional Districts':
        location_ = '&for=congressional%20district:*' + '&in=state:' + state
    if geography == 'State Legislative Upper Districts':
        location_ = '&for=state%20legislative%20district%20(upper%20chamber):*' + '&in=state:' + state
    if geography == 'State Legislative Lower Districts':
        location_ = '&for=state%20legislative%20district%20(lower%20chamber):*' + '&in=state:' + state
    if geography == 'Places':
        location_ = '&for=place:*' + '&in=state:' + state
    if geography == 'Block Groups':
        location_ = '&for=block%20group:*' + '&in=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'Tracts':
        location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'Counties':
        if year == 'timeseries':
            location_ = '&for=county:' + county + '&in=state:' + state + '&time=from 2000-Q1 to 2023-Q4'
        else:
            location_ = '&for=county:' + county + '&in=state:' + state
            # location_ = '&for=county:*' + '&in=state:' + state
    if geography == 'MSA':
        if sample in ['LEHD']:
            if year == 'timeseries':
                location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa) + '&in=state:' + state + '&time=from 2000-Q1 to 2024-Q4'
            else:
                location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa) + '&in=state:' + state
        else:
            location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)
            # location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*'
    if geography == 'PUMA':
        location_ =  '&for=public%20use%20microdata%20area:' + puma + '&in=state:' + state
    if geography == 'States':
        location_ = '&for=state:' + state
    if geography == 'National':
        location_ = '&for=us:*'
    
    ## Concatenate constructed URL
    query = f"{root_}{g_}{variables_}{location_}{api_key_}"
    
    ## Call data using URL

    # Use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_census = pd.DataFrame(response[1:], columns=response[0])
    
    # apply year tag
    if sample != 'LEHD':
        df_census['Year'] = year

    ## Return
    return df_census



## ------





## Main geographic groupings used throughout processing functions
group_puma     = ['State FIPS', 'MPO', 'PUMA'       , 'PUMA NAME'  ]
group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
group_msa      = ['State FIPS',        'MSA_ID'     , 'MSA'        ]
group_mpo      = ['State FIPS', 'MPO'                              ]
group_cd       = ['State FIPS', 'Congressional District'           ]
group_slud     = ['State FIPS', 'State Legislative Upper District' ]
group_slld     = ['State FIPS', 'State Legislative Lower District' ]
group_states   = ['State FIPS'                                     ]




## Processing steps ------


'''
Disclaimer: The processing steps are somewhat unique to how SACOG has defined the indicators, meaning this is 
how we wanted to process the data for our own data needs.  These steps may or may not be useful to other users
that want to pull data from the Census Bureau.

All user defined geography/variable mappings seen throughout the processing steps are predetermined by the user
in the "Census Configuration File.xlsx" workbook.  This includes which estimates are being pulled, how to group
different estimates together, which race/ethnicities to include, and how to sort the variables for a clean output.
Also includes whether or not to include the margin of error estimates and whether or not to calculate percentages.

All function inputs/objects are assigned in the processing script (Step 02 - Process Census Data.ipynb), before
these functions are called (so they are already lined up perfectly).

Some of the functions here (like "sequence()") are user defined functions that are stored in the Regional-Monitoring/
Indicator_Gen/config/Functions.py script.
'''


## ACS processing steps ---

## ACS processing step (1)

'''
User defined function to clean/process ACS tables immediately after query
Replaces weird missing values with np.nan
Drops rows with all missing
Melts data from wide to long
Merges clean variable mapping, race/ethnicity label, and sorting assignment
Removes unneeded columns
Adjusts dollars for inflation as needed
'''

def acs_processing_1(df_census, df_vars, geography, margin_of_error):

    print()
    print('Processing Step 1:')
    print('Reshaping data from columns to rows...')
    print('Mapping Estimate ID field to table ID, table name, and estimate label... (if margin of errors were pulled, including those as well)')
    print()

    if geography == 'Places':
        geo_ID = ['state', 'place', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['state', 'County Name', 'county', 'tract', 'block group', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['state', 'County Name', 'county', 'tract', 'NAME']
    if geography == 'Counties':
        geo_ID = ['state', 'County Name', 'county', 'NAME']
    if geography == 'MSA':
        df_census = df_census.rename(columns={'metropolitan statistical area/micropolitan statistical area':'MSA_ID', 'NAME':'MSA'})
        geo_ID = ['MSA_ID', 'MSA']
    if geography == 'Congressional Districts':
        geo_ID = ['NAME', 'state', 'congressional district']
    if geography == 'State Legislative Upper Districts':
        geo_ID = ['NAME', 'state', 'state legislative district (upper chamber)']
    if geography == 'State Legislative Lower Districts':
        geo_ID = ['NAME', 'state', 'state legislative district (lower chamber)']
    if geography == 'States':
        geo_ID = ['NAME', 'state']
    if geography == 'National':
        geo_ID = ['NAME']


    df_census = df_census.replace('-666666666'  , np.nan)
    df_census = df_census.replace('-666666666.0', np.nan)
    df_census = df_census.replace( -666666666.0 , np.nan)
    df_census = df_census.replace('-222222222'  , np.nan)
    df_census = df_census.replace('-222222222.0', np.nan)
    df_census = df_census.replace( -222222222.0 , np.nan)
    df_census = df_census.replace( '-333333333' , np.nan)
    df_census = df_census.replace( -333333333.0 , np.nan)
    df_census = df_census.replace('-555555555'  , np.nan)
    df_census = df_census.replace( -555555555.0 , np.nan)
    df_census = df_census.replace('-999999999.0', np.nan)
    df_census = df_census.replace( -999999999.0 , np.nan)
    df_census = df_census.replace('null', np.nan)
    df_census = df_census.dropna(axis=1, how='all')
    
    df_census = pd.melt(
        df_census
        , id_vars = geo_ID + ['Year']
        , var_name = 'ID'
        , value_name = 'Total'
    )
    df_census = df_census.dropna()
    
    df_census['Total'] = df_census['Total'].apply(pd.to_numeric)
    df_census = df_census.merge(df_vars[['ID2', 'Table', 'Table Name', 'Label', 'Year']].rename(columns={'ID2':'ID'}), on=['Year', 'ID'], how='left')
    df_census = df_census.drop_duplicates()

    if margin_of_error == 'Yes':
        df_census_me = df_census.copy()
        df_me = df_census_me[df_census_me['Label'].isna()]
        df_census_me = df_census_me.dropna()
        df_me = df_me[['ID'] + geo_ID + ['Year', 'Total']].rename(columns={'Total':'ME'})
        df_me['ID'] = df_me['ID'].apply(lambda s : re.sub("M", "E", s))
        df_census_me = df_census_me.merge(df_me, on=['ID'] + geo_ID + ['Year'], how='left')
        df_census_me['Year'] = df_census_me['Year'].astype(str)
        df_census = df_census_me.copy()
        df_census = df_census[list(df_census.drop(['Total', 'ME'], axis=1).columns) + ['Total', 'ME']]

    if margin_of_error == 'No':
        df_census = df_census[list(df_census.drop(['Total'], axis=1).columns) + ['Total']]

    if geography == 'MSA':
        df_census = df_census.sort_values(['MSA_ID', 'Year', 'ID'], ascending=[True, False, True])
    else:
        df_census = df_census.sort_values(geo_ID + ['Year', 'ID'], ascending=[item in geo_ID for item in geo_ID] + [False, True])

    df_census = df_census.reset_index(drop=True)

    return df_census





## ACS processing step (2)

'''
User defined function to process ACS tables for SACOG specific indicators
Maps the Estimate ID's from the Census Bureau to cleaned label fields, rolls up groupings, race/ethnicity mappings, and sorting order
For any indicator involving money ($-USD), adjusts for inflation based on latest year
For any indicator involving rolls ups that need to be weighted by the population by geography, imports and merges population estimates
'''

def acs_processing_2(df_census, df_vars, estimate, indicator, geography, margin_of_error, year_end, path_main, path_git):

    print()
    print('Processing Step 2:')
    print('Mapping Estimate ID field to cleaned label field, variable grouping fields, race/ethnicity mapping, and variable sorting order...')
    print('If needed, adjusting income data for inflation...')
    print('If needed for any aggregations, population weights are merged onto the dataframe...')
    print()

    if geography == 'Places':
        geo_ID = ['state', 'place', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['state', 'County Name', 'county', 'tract', 'block group', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['state', 'County Name', 'county', 'tract', 'NAME']
    if geography == 'Counties':
        geo_ID = ['state', 'County Name', 'county', 'NAME']
    if geography == 'MSA':
        df_census = df_census.rename(columns={'metropolitan statistical area/micropolitan statistical area':'MSA_ID', 'NAME':'MSA'})
        geo_ID = ['MSA_ID', 'MSA']
    if geography == 'Congressional Districts':
        geo_ID = ['NAME', 'state', 'congressional district']
    if geography == 'State Legislative Upper Districts':
        geo_ID = ['NAME', 'state', 'state legislative district (upper chamber)']
    if geography == 'State Legislative Lower Districts':
        geo_ID = ['NAME', 'state', 'state legislative district (lower chamber)']
    if geography == 'States':
        geo_ID = ['NAME', 'state']
    if geography == 'National':
        geo_ID = ['NAME']
    df_census['Year'] = df_census['Year'].astype(int)

    df_census = df_census.merge(df_vars[['Year', 'ID2','Label_clean', 'Variable', 'Race_Ethnicity', 'Sort']].rename(columns={'ID2':'ID'}), on=['Year', 'ID'], how='left')

    if margin_of_error == 'Yes':
        cols_to_keep = ['ID'] + geo_ID + ['Year', 'Variable', 'Race_Ethnicity', 'Sort', 'Total', 'ME']
    else:
        cols_to_keep = ['ID'] + geo_ID + ['Year', 'Variable', 'Race_Ethnicity', 'Sort', 'Total']
    df_census = df_census[cols_to_keep]

    if indicator in ['Income_1', 'Income_3']:#, 'Chamber_H_5']:
        file_cpi = path_config0 / 'CPI_IAF.xlsx'
        df_cpi = pd.read_excel(file_cpi, sheet_name='BLS_West')
        df_cpi = df_cpi[['Year', 'IAF_' + str(year_end)]]
        df_census = df_census.merge(df_cpi, on='Year', how='left')
        df_census['Total'] = round(df_census['Total']*df_census['IAF_' + str(year_end)])
        df_census = df_census.drop(['IAF_' + str(year_end)], axis=1)

    # Some indicators require the roll up to be weighted by population
    # The following step aligns the Race/Ethnicity mappings with the population counts workbook
    if weighted_by != 'No':
        path_weights = path_main / 'Reference' / 'Weights'
        file_weights = path_weights / f'Total_{weighted_by} {geography} {estimate}.xlsx'
        if geography in ['Block Groups', 'Tracts', 'Counties', 'MPO', 'States', 'National', 'Places', 'MSA']:
            df_weight = pd.read_excel(file_weights, sheet_name=geography)
        elif geography == 'Congressional Districts':
            df_weight = pd.read_excel(file_weights, sheet_name='CD')
        elif geography == 'State Legislative Upper Districts':
            df_weight = pd.read_excel(file_weights, sheet_name='SLDU')
        elif geography == 'State Legislative Lower Districts':
            df_weight = pd.read_excel(file_weights, sheet_name='SLDL')

        if geography == 'MSA':
            cols_pop = ['MSA_ID', 'Year','Race_Ethnicity', weighted_by]
        else:
            cols_pop = ['NAME', 'Year','Race_Ethnicity', weighted_by]
        df_weight = df_weight[cols_pop]
        conditions = [
                        (df_weight["Race_Ethnicity"] == 'All'                                           ),
                        (df_weight["Race_Ethnicity"] == 'American Indian or Alaska Native (NH)'         ),
                        (df_weight["Race_Ethnicity"] == 'Asian (NH)'                                    ),
                        (df_weight["Race_Ethnicity"] == 'Black or African American (NH)'                ),
                        (df_weight["Race_Ethnicity"] == 'Hispanic or Latino'                            ),
                        (df_weight["Race_Ethnicity"] == 'Native Hawaiian or other Pacific Islander (NH)'),
                        (df_weight["Race_Ethnicity"] == 'White (NH)'                                    ),
                        (df_weight["Race_Ethnicity"] == 'Some other race (NH)'                          ),
                        (df_weight["Race_Ethnicity"] == 'Two or more races (NH)'                        )
                    ]
        choices = ["All", "American Indian or Alaska Native", "Asian", "Black or African American", "Hispanic or Latino",
                    "Native Hawaiian or other Pacific Islander", "White (NH)", "Some other race", "Two or more races"]
        df_weight["Race_Ethnicity"] = np.select(conditions, choices)

        if geography == 'MSA':
            cols_merge = ['MSA_ID', 'Year', 'Race_Ethnicity']
        else:
            cols_merge = ['NAME', 'Year', 'Race_Ethnicity']
        df_census = df_census.merge(df_weight, on=cols_merge, how='left')

        if indicator in ['Chamber_H_5', 'Chamber_H_7']:
            df_hisp = df_census[df_census['Race_Ethnicity'] == 'Hispanic or Latino']
            df_hisp = df_hisp[geo_ID + ['Year', 'Households']]
            df_hisp = df_hisp.rename(columns={'Households':'Hispanic Households'})
            df_census = df_census.merge(df_hisp, on=geo_ID+['Year'], how='left')
            df_census.loc[df_census['Race_Ethnicity'] == 'All', 'Households'] = df_census['Households'] - df_census['Hispanic Households']
            df_census = df_census.drop('Hispanic Households', axis=1)
    
    df_census = df_census.rename(columns={
        'ID':'Estimate ID'
            ,'state':'State FIPS'
            , 'place':'Place ID'
            , 'county':'County FIPS'
            , 'tract':'Tract ID'
            , 'block group':'Block Group ID'
            , 'congressional district':'Congressional District'
            , 'state legislative district (upper chamber)':'State Legislative Upper District'
            , 'state legislative district (lower chamber)':'State Legislative Lower District'
        })

    df_census = clean_fips(df_census)

    if geography == 'Places':
        file_cdp = path_config0 / 'area_codes.xlsx'
        df_codes = pd.read_excel(file_cdp, sheet_name='CDPcodes')
        if unincorporated == 'Yes':
            df_codes = df_codes[(df_codes['MPO'].str.contains('SACOG')) & (df_codes['Incorporated'] == 'Yes')]
        df_codes['place'] = df_codes['place'].astype(str).apply('{:0>5}'.format)
        CDP_to_keep = list(df_codes['place'].unique())
        df_census = df_census[df_census['Place ID'].isin(CDP_to_keep)]
        df_codes = df_codes.rename(columns={'place':'Place ID'})

        df_codes = df_codes[['Year', 'Place ID', 'County Name']]
        df_codes2010 = df_codes[df_codes['Year'] == 2010]
        df_codes2020 = df_codes[df_codes['Year'] == 2020]

        df_census2010 = df_census[df_census['Year'] <  2020]
        df_census2020 = df_census[df_census['Year'] >= 2020]

        df_census2010 = df_census2010.merge(df_codes2010.drop('Year', axis=1), on='Place ID', how='left')
        df_census2020 = df_census2020.merge(df_codes2020.drop('Year', axis=1), on='Place ID', how='left')

        df_census = pd.concat([df_census2020, df_census2010])

        df_census['NAME'] = df_census['NAME'].str.replace(' CDP, California' , '', regex=True)
        df_census['NAME'] = df_census['NAME'].str.replace(' town, California', '', regex=True)
        df_census['NAME'] = df_census['NAME'].str.replace(' city, California', '', regex=True)
        df_census = df_census.drop_duplicates()

    df_census = df_census.reset_index(drop=True)

    return df_census




## ACS processing step (3)

'''
User defined function to clean/process ACS tables margin of error fields
Also sorts the table by race/ethnicity (for consistency in the outputs) and by assigned variable sorting order
'''

def acs_processing_3(df_census, geography):

    print()
    print('Processing Step 3:')
    print('Sort by user defined race/ethnicity field and variable sorting field, then drop those fields...')
    print()

    if geography == 'Places':
        geo_ID = ['State FIPS', 'County Name', 'Place ID', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
    if geography == 'Counties':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID']
    if geography == 'Congressional Districts':
        geo_ID = ['Congressional District']
    if geography == 'State Legislative Upper Districts':
        geo_ID = ['State Legislative Upper District']
    if geography == 'State Legislative Lower Districts':
        geo_ID = ['State Legislative Lower District']
    if geography == 'States':
        geo_ID = ['State FIPS', 'NAME']
    if geography == 'National':
        geo_ID = ['NAME']

    df_census['Race_Ethnicity_sort'] = pd.Categorical(df_census['Race_Ethnicity'], ['All'
                                                                , 'American Indian or Alaska Native'
                                                                , 'American Indian or Alaska Native (NH)'
                                                                , 'Asian'
                                                                , 'Asian (NH)'
                                                                , 'Black or African American'
                                                                , 'Black or African American (NH)'
                                                                , 'Hispanic or Latino'
                                                                , 'Native Hawaiian or other Pacific Islander'
                                                                , 'Native Hawaiian or other Pacific Islander (NH)'
                                                                , 'White'
                                                                , 'White (NH)'
                                                                , 'Some other race'
                                                                , 'Some other race (NH)'
                                                                , 'Two or more races'
                                                                , 'Two or more races (NH)'
                                                            ])
    
    df_census = df_census.sort_values(by= geo_ID + ['Year', 'Race_Ethnicity_sort', 'Sort'], ascending=[item in geo_ID for item in geo_ID] + [False, True, True])
    df_census = df_census.drop(['Race_Ethnicity_sort', 'Sort'], axis=1)
    
    return df_census









## ACS processing step (4)

'''
User defined function to process ACS tables
Rolls up population/household counts and standard errors and calculates percentages based on user defined geography/variable mappings
'''

def acs_processing_4(df_census, estimate, indicator, geography, percentages, margin_of_error, MOE_thresh, num_vars, df_fips=None):
    print('Margin of error threshold: ', MOE_thresh)

    print()
    print('Processing Step 4:')
    print('Roll up estimates (and margin of errors) to user defined variable groupings...')
    print('Calculate percentages by geography and year combinations, if needed...')
    print('Reshape data from rows to columns...')
    print()

    # User defined functions
    def calculate_ME_ratio(df, MOE_thresh):
        df['ME_ratio'] = df['ME']/df['Total']
        conditions = [
            (df['Race_Ethnicity'] == 'All') & (len(df['Race_Ethnicity'].unique()) > 1)
            , df['ME_ratio'] <= MOE_thresh
            , df['ME_ratio']  > MOE_thresh
        ]
        choices = ['Yes', 'Yes', 'No']
        df['Use for Reporting'] = np.select(conditions, choices, default='No')
        return df

    # Set geo_ID object
    if geography == 'Places':
        geo_ID = ['State FIPS', 'County Name', 'Place ID', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
    if geography == 'Counties':
        if mpo == 'Yes':
            geo_ID = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME']
        else:
            geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'MSA']
    if geography == 'Congressional Districts':
        geo_ID = ['State FIPS', 'Congressional District', 'NAME']
    if geography == 'State Legislative Upper Districts':
        geo_ID = ['State FIPS', 'State Legislative Upper District', 'NAME']
    if geography == 'State Legislative Lower Districts':
        geo_ID = ['State FIPS', 'State Legislative Lower District', 'NAME']
    if geography == 'States':
        geo_ID = ['State FIPS', 'NAME']
    if geography == 'National':
        geo_ID = ['NAME']

    # If MPO roll up needed
    if geography == 'Counties':
        if mpo == 'Yes':
            df_mpo = df_fips[['County Name', 'MPO']]
            df_census = df_census.merge(df_mpo, on=['County Name'], how='left')


    # If weighted roll up is needed
    if weighted_by != 'No':
        df_census[weighted_by] = df_census[weighted_by].fillna(0)
        df_census[weighted_by] = df_census[weighted_by].replace(0, 1)
        df_census = df_census.rename(columns={weighted_by:'Weight'})
        wm = lambda x: np.average(x, weights=df_census.loc[x.index, 'Weight']) # weighted average

        if indicator == 'RHNA_HSG_10':
            col_var = 'Median Contract Rent'
        else:
            col_var = 'Median Household Income'

        if indicator == 'Chamber_H_5':
            conditions = [
                    (df_census["Race_Ethnicity"] == 'All'               ),
                    (df_census["Race_Ethnicity"] == 'Hispanic or Latino')
                ]
            choices = ["Not Hispanic or Latino", "Hispanic or Latino"]
            df_census["Race_Ethnicity"] = np.select(conditions, choices)


    if geography == 'Places':
        if unincorporated == 'Yes':
            if project == 'Monitoring and Reporting':
                path_server = r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data"
                file_counties = path_server / f'{indicator} Counties {estimate}.xlsx'  
            if project in ['RHNA', 'Blueprint']:
                file_counties = path_prod / export_loc / f'{indicator} Counties {estimate}.xlsx'
            if project in ['Miscellaneous']:
                file_counties = path_main / export_loc / f'{indicator} Counties {estimate}.xlsx'     


    # reorder columns
    # fill missing values (represent a population of 0)
    # Roll up metrics to variable mappings (and MPO if Counties)

    if margin_of_error == 'Yes' and weighted_by != 'No':
        cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Weight', 'Total', 'ME']
    elif margin_of_error == 'Yes' and weighted_by == 'No':
        cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME']
    elif margin_of_error == 'No' and weighted_by != 'No':
        cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Weight', 'Total']
    else:
        cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total']

    df_census = df_census[cols]
    df_census['Total'] = df_census['Total'].fillna(0)
    

    # Fill missings with 0, then 1 to make sure nothing gets removed if population is 0
    # create weighted average lambda function
    # roll up to different geographies using population weighted average

    if margin_of_error == 'Yes':

        df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan

        if weighted_by != 'No':

            wm = lambda x: np.average(x, weights = df_census.loc[x.index, 'Weight']) # weighted average (or Population or Households)
            df_census = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', wm), ME=('ME', sqrtsumsq), Weight=('Weight', 'sum'))
            df_census = calculate_ME_ratio(df_census, MOE_thresh)

            if geography == 'Counties':
                if mpo == 'Yes':
                    wm = lambda x: np.average(x, weights = df_census.loc[x.index, 'Weight']) # weighted average (or Population or Households)
                    df_mpo = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', wm), ME=('ME', sqrtsumsq), Weight=('Weight', 'sum'))
                    df_mpo = calculate_ME_ratio(df_mpo, MOE_thresh)

            if geography == 'Places':

                if unincorporated == 'Yes':
                    wm = lambda x: np.average(x, weights = df_census.loc[x.index, 'Weight']) # weighted average (or Population or Households)
                    df_inc1 = df_census.groupby(['State FIPS', 'County Name', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', wm), ME=('ME', sqrtsumsq), Weight=('Weight', 'sum'))

                    df_counties = pd.read_excel(file_counties, sheet_name='Counties')
                    df_inc1 = df_inc1.merge(df_counties[['County Name', 'Year', 'Race_Ethnicity', 'Variable', col_var, 'Margin of Error']], on=['County Name', 'Year', 'Race_Ethnicity', 'Variable'], how='left')
                    df_inc1['diff'] = df_inc1[col_var] - df_inc1['Total']
                    df_inc1['diff_ME'] = np.sqrt(df_inc1['Margin of Error']**2 + df_inc1['ME']**2)
                    df_inc1['Place ID'] = 'Unincorporated'
                    df_inc1['NAME'    ] = 'Unincorporated'
                    df_uninc = df_inc1[['State FIPS', 'County Name', 'Place ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'diff', 'diff_ME']]
                    df_uninc = df_uninc.rename(columns={'diff': 'Total', 'diff_ME':'ME'})
                    df_uninc = calculate_ME_ratio(df_uninc, MOE_thresh)
                    df_census = pd.concat([df_census, df_uninc])
                    df_census = df_census.reset_index(drop=True)

        else:

            if indicator == 'Income_4':
                df_census1 = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
                df_census2 = df_census.groupby(geo_ID + ['Year',                   'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
                df_census2.loc[:, 'Race_Ethnicity'] = 'All'
                df_census2 = df_census2[df_census2['Year'].isin(['2009', '2010', '2011', '2012'])]
                df_census = pd.concat([df_census1, df_census2])

            else:

                df_census = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))

            df_census = calculate_ME_ratio(df_census, MOE_thresh)

            if geography == 'Counties':
                if mpo == 'Yes':
                    if indicator == 'Income_4':
                        df_mpo1 = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
                        df_mpo2 = df_census.groupby(['State FIPS', 'MPO', 'Year',                   'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
                        df_mpo2.loc[:, 'Race_Ethnicity'] = 'All'
                        df_mpo2 = df_mpo2[df_mpo2['Year'].isin(['2009', '2010', '2011', '2012'])]
                        df_mpo = pd.concat([df_mpo1, df_mpo2])
                    else:
                        df_mpo = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))

                    df_mpo = calculate_ME_ratio(df_mpo, MOE_thresh)

            if geography == 'Places':

                if unincorporated == 'Yes':

                    df_inc1 = df_census.groupby(['State FIPS', 'County Name', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))

                    df_counties = pd.read_excel(file_counties, sheet_name='Counties')
                    if 'Population' in df_counties.columns:
                        col_var = 'Population'
                    if 'Households' in df_counties.columns:
                        col_var = 'Households'
                    if 'Housing Units' in df_counties.columns:
                        col_var = 'Housing Units'

                    df_inc1 = df_inc1.merge(df_counties[['County Name', 'Year', 'Race_Ethnicity', 'Variable', col_var, 'Margin of Error']], on=['County Name', 'Year', 'Race_Ethnicity', 'Variable'], how='left')
                    df_inc1['diff'] = df_inc1[col_var] - df_inc1['Total']
                    df_inc1['diff_ME'] = np.sqrt(df_inc1['Margin of Error']**2 + df_inc1['ME']**2)
                    df_inc1['Place ID'] = 'Unincorporated'
                    df_inc1['NAME'    ] = 'Unincorporated'
                    df_uninc = df_inc1[['State FIPS', 'County Name', 'Place ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'diff', 'diff_ME']]
                    df_uninc = df_uninc.rename(columns={'diff': 'Total', 'diff_ME':'ME'})
                    df_uninc = calculate_ME_ratio(df_uninc, MOE_thresh)
                    df_census = pd.concat([df_census, df_uninc])
                    df_census = df_census.reset_index(drop=True)

        df_census = df_census.drop_duplicates()

        if geography == 'MSA':
            df_census = df_census.sort_values(['MSA_ID', 'Year'], ascending=[True, False])
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo = df_mpo.drop_duplicates()
                df_mpo = df_mpo.sort_values(['MPO', 'Year'], ascending=[True, False])


    if margin_of_error == 'No':

        if weighted_by != 'No':
            wm = lambda x: np.average(x, weights = df_census.loc[x.index, 'Weight']) # weighted average (or Population or Households)
            df_census = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', wm), Weight=('Weight', 'sum'))

            if geography == 'Counties':
                if mpo == 'Yes':
                    wm = lambda x: np.average(x, weights = df_census.loc[x.index, 'Weight']) # weighted average (or Population or Households)
                    df_mpo = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', wm), Weight=('Weight', 'sum'))

            if geography == 'Places':

                if unincorporated == 'Yes':

                    wm = lambda x: np.average(x, weights = df_census.loc[x.index, 'Weight']) # weighted average (or Population or Households)
                    df_inc1 = df_census.groupby(['State FIPS', 'County Name', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', wm), Weight=('Weight', 'sum'))

                    df_counties = pd.read_excel(file_counties, sheet_name='Counties')
                    df_inc1 = df_inc1.merge(df_counties[['County Name', 'Year', 'Race_Ethnicity', 'Variable', col_var]], on=['County Name', 'Year', 'Race_Ethnicity', 'Variable'], how='left')
                    df_inc1['diff'] = df_inc1[col_var] - df_inc1['Total']
                    df_inc1['Place ID'] = 'Unincorporated'
                    df_inc1['NAME'    ] = 'Unincorporated'
                    df_uninc = df_inc1[['State FIPS', 'County Name', 'Place ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'diff']]
                    df_uninc = df_uninc.rename(columns={'diff': 'Total', 'diff_ME':'ME'})
                    df_census = pd.concat([df_census, df_uninc])
                    df_census = df_census.reset_index(drop=True)

        else:

            if indicator == 'Income_4':
                df_census1 = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))
                df_census2 = df_census.groupby(geo_ID + ['Year',                   'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))
                df_census2.loc[:, 'Race_Ethnicity'] = 'All'
                df_census2 = df_census2[df_census2['Year'].isin(['2009', '2010', '2011', '2012'])]
                df_census = pd.concat([df_census1, df_census2])

            else:

                df_census = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))

            if geography == 'Counties':
                if mpo == 'Yes':
                    if indicator == 'Income_4':
                        df_mpo1 = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))
                        df_mpo2 = df_census.groupby(['State FIPS', 'MPO', 'Year',                   'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))
                        df_mpo2.loc[:, 'Race_Ethnicity'] = 'All'
                        df_mpo2 = df_mpo2[df_mpo2['Year'].isin(['2009', '2010', '2011', '2012'])]
                        df_mpo = pd.concat([df_mpo1, df_mpo2])
                    else:
                        df_mpo = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))

            if geography == 'Places':

                if unincorporated == 'Yes':

                    df_inc1 = df_census.groupby(['State FIPS', 'County Name', 'Year', 'Race_Ethnicity', 'Variable'], as_index=False, sort=False).agg(Total=('Total', 'sum'))

                    df_counties = pd.read_excel(file_counties, sheet_name='Counties')
                    if 'Population' in df_counties.columns:
                        col_var = 'Population'
                    if 'Households' in df_counties.columns:
                        col_var = 'Households'
                    if 'Housing Units' in df_counties.columns:
                        col_var = 'Housing Units'
                    df_inc1 = df_inc1.merge(df_counties[['County Name', 'Year', 'Race_Ethnicity', 'Variable', col_var]], on=['County Name', 'Year', 'Race_Ethnicity', 'Variable'], how='left')
                    df_inc1['diff'] = df_inc1[col_var] - df_inc1['Total']
                    df_inc1['Place ID'] = 'Unincorporated'
                    df_inc1['NAME'    ] = 'Unincorporated'
                    df_uninc = df_inc1[['State FIPS', 'County Name', 'Place ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'diff']]
                    df_uninc = df_uninc.rename(columns={'diff': 'Total'})
                    df_census = pd.concat([df_census, df_uninc])
                    df_census = df_census.reset_index(drop=True)

        df_census = df_census.drop_duplicates()

        if geography == 'MSA':
            df_census = df_census.sort_values(['MSA_ID', 'Year'], ascending=[True, False])
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo = df_mpo.drop_duplicates()
                df_mpo = df_mpo.sort_values(['MPO', 'Year'], ascending=[True, False])


    # Replace infinite values with NaN
    # missing values represent a population of 0
    df_census = df_census.replace([np.inf, -np.inf, 0], np.nan)
    
    ## Check if we want to calculate proportions
    if percentages == 'Yes':

        if num_vars == 1:
            df_census['Percentage'] = df_census['Total'] / df_census[df_census['Race_Ethnicity'] != 'All'].groupby(geo_ID + ['Year'])['Total'].transform('sum')
            if geography == 'Counties':
                if mpo == 'Yes':
                    df_mpo['Percentage'] = df_mpo['Total'] / df_mpo[df_mpo['Race_Ethnicity'] != 'All'].groupby(['State FIPS', 'MPO', 'Year'])['Total'].transform('sum')

        if num_vars > 1:
            df_census['Percentage'] = df_census['Total'] / df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity'])['Total'].transform('sum')
            if geography == 'Counties':
                if mpo == 'Yes':
                    df_mpo['Percentage'] = df_mpo['Total'] / df_mpo.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity'])['Total'].transform('sum')

            
    if geography == 'Counties':
        if mpo == 'Yes':
            return df_census, df_mpo
        else:
            return df_census
    else:
        return df_census



## ---


## PUMS processing steps ---


## PUMS processing step (1)

'''
User defined function to do initial cleaning of PUMS tables
Cleans the FIPS codes fields
Subsets to head of household (LEHD)
Reassigns raw variable values with the descriptio on user defined geography/variable mappings
'''

def pums_processing_1(df_census, df_vars, sample_type, weight):

    print()
    print('Processing Step 1:')
    print('Cleans FIPS codes fields, subsets to head of household (LEHD), reassigns raw variable values with the description, ...')
    print()

    groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
    groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

    if sample_type == 'PUMS':
        df_census['PUMA'] = df_census['PUMA'].astype(str).apply('{:0>5}'.format)
        df_census[weight] = df_census[weight].astype(int)

    if sample_type == 'FOODSEC':
        df_census['Household_ID'] = df_census['HRHHID'].map(str) + '-' + df_census['HRHHID2'].map(str)
        df_census = df_census.drop(['HRHHID', 'HRHHID2'], axis=1)
        df_census['Householder'] = df_census.groupby(['Household_ID', 'Year'], as_index=False)['PERRP'].transform(min)
        df_census = df_census[df_census['PERRP'] == df_census['Householder']]
        df_census = df_census.drop_duplicates(['Household_ID', 'Year'])

    for group in groups2:
        df_census[group] = df_census[group].astype(str).apply('{:0>2}'.format)

    df_vars   ['Value1'] = df_vars   ['Value1'].astype(str).apply('{:0>2}'.format)
    df_census ['state' ] = df_census ['state' ].astype(str).apply('{:0>2}'.format)

    if sample_type == 'PUMS':
        df_census[weight] = df_census[weight].astype(int)
    if sample_type == 'FOODSEC':
        df_census[weight] = df_census[weight].astype('float')
    df_census[groups2] = df_census[groups2].astype("string")

    df_vars2 = df_vars.pivot_table(index = ['Year', 'Value1']
                                        , columns='ID2'
                                        , values = 'Description2'
                                        , aggfunc = lambda x: x).reset_index()
    cols = ['Year', 'Value1'] + groups2
    df_vars2 = df_vars2[cols]

    list_values = []
    for group in groups2:
        list_values = list_values + list(df_census[group].values)
    set_values = set(list_values)

    df_vars2 = df_vars2[df_vars2['Value1'].isin(set_values)]
    df_vars2 = df_vars2.add_suffix('_desc').rename(columns={'Value1_desc':'Value1', 'Year_desc':'Year'})

    for col in cols[2:]:
        df_census = df_census.merge(df_vars2[['Value1', col+'_desc', 'Year']], left_on=[col, 'Year'], right_on=['Value1', 'Year'], how='inner')
        df_census[col] = df_census[col+'_desc']
        df_census = df_census.drop(['Value1', col+'_desc'], axis=1)

    return df_census, groups



## PUMS processing step (2)

'''
User defined function to process PUMS tables
Maps area codes together
Links PUMA codes to county FIPS codes by year
Then maps the county FIPS codes to MSA IDs
'''

def pums_processing_2(df_census, estimate, sample_type, groups, df_fips, dict_fips):
    
    print()
    print('Processing Step 2:')
    print('Mapping PUMA codes to other area codes...')
    print()

    # df_census = df_census.dropna()
    df_census = df_census.rename(columns={'state':'State FIPS', 'county':'County FIPS'})

    if sample_type == 'PUMS':
        file_puma_codes = path_config0 / 'area_codes.xlsx'
        df_fips_pums = pd.read_excel(file_puma_codes, sheet_name='PUMAcodes', dtype={'STATEFP': object, 'COUNTYFP': object, 'TRACTCE': object, 'PUMA5CE': object})
        df_fips_pums = df_fips_pums[df_fips_pums['STATEFP'].isin(list(dict_fips.keys()))]
        df_fips_pums = df_fips_pums[['STATEFP', 'PUMA5CE', 'PUMA NAME', 'COUNTYFP', 'Years']].rename(columns={'PUMA5CE':'PUMA', 'STATEFP':'State FIPS', 'COUNTYFP':'County FIPS'}).drop_duplicates()

        if estimate in ['ACS5', 'PUMS5']:
            df_census1 = df_census[df_census['Year'].isin(sequence(2012, 2021, 1))]
            df_census2 = df_census[df_census['Year'].isin(sequence(2022, 2031, 1))]
        else:
            df_census1 = df_census[df_census['Year'].isin(sequence(2010, 2020, 1))]
            df_census2 = df_census[df_census['Year'].isin(sequence(2021, 2030, 1))]           

        df_census1 = df_census1.merge(df_fips_pums[df_fips_pums['Years'] == '2012-2021'], on=['State FIPS', 'PUMA'], how='left')
        df_census2 = df_census2.merge(df_fips_pums[df_fips_pums['Years'] == '2022-2031'], on=['State FIPS', 'PUMA'], how='left')
        df_census = pd.concat([df_census1, df_census2])
        df_census = df_census.drop('Years', axis=1)

        df_census['County FIPS'] = df_census['County FIPS'].astype(str).apply('{:0>3}'.format)
        df_census = df_census.merge(df_fips[['State FIPS', 'MPO', 'County FIPS', 'County Name', 'MSA_ID', 'MSA_acs']].drop_duplicates(), on=['State FIPS', 'County FIPS'])
        df_census = df_census.rename(columns={'MSA_acs':'MSA'})
        df_census = df_census.set_index(['State FIPS', 'MPO', 'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'Year']).reset_index()
        df_census = df_census.sort_values(['State FIPS', 'PUMA', 'Year'] + groups, ascending=[True, True, False] + [item in groups for item in groups])
    
    if sample_type == 'FOODSEC':
        df_census = df_census.sort_values(['State FIPS', 'MPO', 'County FIPS', 'Year'] + groups, ascending=[True, True, True, False] + [item in groups for item in groups])

    return df_census



## PUMS processing step (3)

'''
User defined function to clean grouping fields of PUMS tables
Adjusts the race/ethnicity field to include hispanic or latino
Creates new groups for Cost_6 indicator
Adjusts $USD fields for inflation to the latest year (creates groupings as needed)
'''

def pums_processing_3(df_census, groups, indicator, path_config0):

    print()
    print('Processing Step 3:')
    print('Cleaning the race/ethnicity fields, creating new groups for specific indicators, adjusting income variables for inflation, ...')
    print()

    if 'HISP' in groups:
        if project == 'Monitoring and Reporting':
            df_census.loc[df_census['HISP'] == 'Hispanic or Latino', 'RAC1P'] = 'Hispanic or Latino'
            df_census = df_census.drop('HISP', axis=1)
            groups.remove('HISP')
        # if project == 'Chamber Study Missions': ## HERE
        #     df_census.loc[df_census['HISP'] == 'Hispanic or Latino', 'RAC1P'] = 'Hispanic or Latino'
        #     df_census = df_census.drop('HISP', axis=1)
        #     groups.remove('HISP')


    if 'HHLDRHISP' in groups:
        df_census.loc[df_census['HHLDRHISP'] == 'Hispanic or Latino', 'HHLDRRAC1P'] = 'Hispanic or Latino'
        df_census = df_census.drop('HHLDRHISP', axis=1)
        groups.remove('HHLDRHISP')

    if 'PEHSPNON' in groups:
        df_census.loc[df_census['PEHSPNON'] == 'Hispanic or Latino', 'PTDTRACE'] = 'Hispanic or Latino'
        df_census = df_census.drop('PEHSPNON', axis=1)
        groups.remove('PEHSPNON')

    if indicator == 'Cost_6':
        cols = ['GRPIP', 'OCPIP']
        df_census[cols] = df_census[cols].astype(int)
        conditions = [
                        ( (df_census['WGTP' ] == 0) ),
                        ( (df_census['GRPIP'] == 0) & (df_census['OCPIP'] == 0) ),
                        ( (df_census['GRPIP'] == 0) & (df_census['OCPIP']  > 0) ),
                        ( (df_census['OCPIP'] == 0) & (df_census['GRPIP']  > 0) )
                    ]
        choices = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Owner', 'Renter']
        df_census["housing_type"] = np.select(conditions, choices)
        conditions = [
                        (  (df_census['WGTP' ] ==  0) ),
                        (  (df_census['GRPIP'] ==  0) & (df_census['OCPIP'] == 0)),
                        ( ((df_census['GRPIP'] ==  0) & (df_census['OCPIP'] <= 30)) | ((df_census['OCPIP'] ==  0) & (df_census['GRPIP'] <= 30)) ),
                        ( ((df_census['GRPIP']  > 30) & (df_census['GRPIP'] <= 50)) | ((df_census['OCPIP']  > 30) & (df_census['OCPIP'] <= 50)) ),
                        (  (df_census['GRPIP']  > 50) | (df_census['OCPIP']  > 50) )
                    ]
        choices = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Cost burden <=30%', 'Cost burden >30% to <=50%', 'Cost burden >50%']
        df_census["housing_burden"] = np.select(conditions, choices)
        df_census = df_census.drop(['GRPIP', 'OCPIP'], axis=1)
        # groups = list(map(lambda x: x.replace('GRPIP', 'housing_type'  ), groups))
        # groups = list(map(lambda x: x.replace('OCPIP', 'housing_burden'), groups))
        groups = ['RAC1P', 'housing_type', 'housing_burden']

    if indicator in ['Income_2', 'Accessibility_2', 'Accessibility_4']:
        df_cpi = pd.read_excel(os.path.join(path_config0, 'CPI Inflation Adjustment Factors.xlsx'), sheet_name='BLS_West')
        df_cpi = df_cpi[['Year', 'IAF_2023']]

        df_census = df_census.merge(df_cpi, on='Year', how='left')
        cols = ['HINCP', 'ADJINC']
        df_census[cols] = df_census[cols].astype('float32')
        df_census['HINCP'] = df_census['HINCP']*df_census['ADJINC']*df_census['IAF_2023']
        df_census = df_census.drop(['IAF_2023', 'ADJINC'], axis=1)

        df_income_brackets = pd.read_excel(os.path.join(path_config0, 'CA State Income Brackets by Household Size.xlsx'), sheet_name='Table')
        df_income_brackets['County'].fillna(method='ffill', inplace=True)
        df_income_brackets['County'] = df_income_brackets['County'].str.replace(' County.*'         , '' , regex = True)
        df_income_brackets['County'] = df_income_brackets['County'].str.replace('\n'                , ' ', regex = True)
        df_income_brackets['AMI'   ] = df_income_brackets['County'].str.extract('\$?([0-9,]+)[.%]?')
        df_income_brackets['AMI'   ] = df_income_brackets['AMI'   ].str.replace(','                 , '' , regex = True)
        df_income_brackets['County'] = df_income_brackets['County'].str.replace(' \$?([0-9,]+)[.%]?', '' , regex = True)
        df_income_brackets = pd.melt(df_income_brackets
                                      , id_vars = ['County', 'Income Bracket', 'AMI']
                                      , var_name = 'NP'
                                      , value_name = 'Income Threshold')
        df_income_brackets = df_income_brackets[df_income_brackets['Income Bracket'].isin(['Low Income', 'Moderate Income'])]
        df_income_brackets = df_income_brackets.pivot_table(index = ['County', 'NP']
                                                             , columns='Income Bracket'
                                                             , values = 'Income Threshold').reset_index().rename(columns={'County':'County Name'})
        # df_income_brackets['NP'] = df_income_brackets['NP'].astype(str)
        df_census = df_census.merge(df_income_brackets, on=['County Name', 'NP'], how='left')
        df_census.loc[ df_census['HINCP'] <= df_census['Low Income']                                                        , 'Income Bracket'] = 'Low Income'
        df_census.loc[(df_census['HINCP']  > df_census['Low Income']) & (df_census['HINCP'] <= df_census['Moderate Income']), 'Income Bracket'] = 'Moderate Income'
        df_census.loc[ df_census['HINCP']  > df_census['Moderate Income']                                                   , 'Income Bracket'] = 'High Income'
        df_census.loc[ df_census['NP'] == 0                                                                                 , 'Income Bracket'] = 'No data available'
        df_census = df_census.drop(['HINCP', 'NP'], axis=1)
        groups = ['Income Bracket'] + groups[:-1]
        if indicator == 'Accessibility_4':
            df_census = df_census[df_census['JWTRNS'] != 'N/A, not a civillian in the labor force']
            df_census['JWMNP'] = df_census['JWMNP'].astype('float32')
            df_census.loc[(df_census['JWMNP'] ==  0)                             , 'Travel Time'] = 'No commute (worked from home)'
            df_census.loc[(df_census['JWMNP']  >  0) & (df_census['JWMNP'] <= 15), 'Travel Time'] = '0 to 15 minutes'
            df_census.loc[(df_census['JWMNP']  > 15) & (df_census['JWMNP'] <= 30), 'Travel Time'] = '15 to 30 minutes'
            df_census.loc[(df_census['JWMNP']  > 30)                             , 'Travel Time'] = 'More than 30 minutes'
            groups = groups[:-1] + ['Travel Time'] + ['RAC1P']
            df_census = df_census.drop('JWTRNS', axis=1)
            groups.remove('JWTRNS')

    return df_census, groups




## PUMS processing step (4)

'''
User defined function to process PUMS tables
Rolls up population/household counts and standard errors and calculates percentages based on user defined geography/variable mappings
'''

def pums_processing_4(df_census, indicator, weight, margin_of_error, MOE_thresh, percentages, groups):

    print()
    print('Processing Step 4:')
    print('Rolling up estimtaes to desired group variables and geographies, and calculating percentages...')
    print()

    df_puma     = df_census.drop([                            'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'SERIALNO'], axis=1)
    df_counties = df_census.drop([       'PUMA', 'PUMA NAME', 'MSA_ID', 'MSA',                               'SERIALNO'], axis=1)
    df_msa      = df_census.drop(['MPO', 'PUMA', 'PUMA NAME',                  'County FIPS', 'County Name', 'SERIALNO'], axis=1)
    df_mpo      = df_census.drop([       'PUMA', 'PUMA NAME', 'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'SERIALNO'], axis=1)
    
    df_puma     = df_puma    .set_index(group_puma    ).reset_index()
    df_counties = df_counties.set_index(group_counties).reset_index()
    df_msa      = df_msa     .set_index(group_msa     ).reset_index()
    df_mpo      = df_mpo     .set_index(group_mpo     ).reset_index()

    if margin_of_error == 'Yes':
        df_puma    .loc[df_puma    ['ME'] < 0, 'ME'] = np.nan
        df_counties.loc[df_counties['ME'] < 0, 'ME'] = np.nan
        df_msa     .loc[df_msa     ['ME'] < 0, 'ME'] = np.nan
        df_mpo     .loc[df_mpo     ['ME'] < 0, 'ME'] = np.nan
        
        if indicator in ['Income_2', 'Accessibility_2', 'Accessibility_3', 'Accessibility_4']:
            if indicator == 'Accessibility_4':
                df_puma1     = df_puma    .groupby(group_puma     + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_counties1 = df_counties.groupby(group_counties + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_msa1      = df_msa     .groupby(group_msa      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo1      = df_mpo     .groupby(group_mpo      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_puma2     = df_puma    .groupby(group_puma     + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_counties2 = df_counties.groupby(group_counties + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_msa2      = df_msa     .groupby(group_msa      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo2      = df_mpo     .groupby(group_mpo      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_puma1    .loc[:, 'Income Bracket'] = 'All'
                df_counties1.loc[:, 'Income Bracket'] = 'All'
                df_msa1     .loc[:, 'Income Bracket'] = 'All'
                df_mpo1     .loc[:, 'Income Bracket'] = 'All'
                df_puma2    .loc[:, 'RAC1P'] = 'All'
                df_counties2.loc[:, 'RAC1P'] = 'All'
                df_msa2     .loc[:, 'RAC1P'] = 'All'
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_puma     = pd.concat([df_puma1    , df_puma2    ])
                df_counties = pd.concat([df_counties1, df_counties2])
                df_msa      = pd.concat([df_msa1     , df_msa2     ])
                df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])
            if indicator == 'Accessibility_3':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo1     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH', 'RAC1P'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo2     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_mpo      = pd.concat([df_mpo1, df_mpo2])           
            if indicator == 'Accessibility_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            if indicator == 'Income_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))

        elif indicator == 'Cost_6':
            df_puma1 = df_puma.groupby(list(df_puma.drop([weight, 'ME'         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_puma2 = df_puma.groupby(list(df_puma.drop([weight, 'ME', 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_puma2.loc[:, 'RAC1P'] = 'All'
            df_puma2 = pd.concat([df_puma1, df_puma2])
            df_puma3 = df_puma2[df_puma2['housing_type'].isin(['Owner', 'Renter'])]
            df_puma3 = df_puma3.groupby(list(df_puma3.drop(['Total', 'ME', 'housing_type'], axis=1).columns), as_index=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
            df_puma3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_puma = pd.concat([df_puma2, df_puma3])

            df_counties1 = df_counties.groupby(list(df_counties.drop([weight, 'ME'         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_counties2 = df_counties.groupby(list(df_counties.drop([weight, 'ME', 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_counties2.loc[:, 'RAC1P'] = 'All'
            df_counties2 = pd.concat([df_counties1, df_counties2])
            df_counties3 = df_counties2[df_counties2['housing_type'].isin(['Owner', 'Renter'])]
            df_counties3 = df_counties3.groupby(list(df_counties3.drop(['Total', 'ME', 'housing_type'], axis=1).columns), as_index=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
            df_counties3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_counties = pd.concat([df_counties2, df_counties3])

            df_msa1 = df_msa.groupby(list(df_msa.drop([weight, 'ME'         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_msa2 = df_msa.groupby(list(df_msa.drop([weight, 'ME', 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_msa2.loc[:, 'RAC1P'] = 'All'
            df_msa2 = pd.concat([df_msa1, df_msa2])
            df_msa3 = df_msa2[df_msa2['housing_type'].isin(['Owner', 'Renter'])]
            df_msa3 = df_msa3.groupby(list(df_msa3.drop(['Total', 'ME', 'housing_type'], axis=1).columns), as_index=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
            df_msa3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_msa = pd.concat([df_msa2, df_msa3])

            df_mpo1 = df_mpo.groupby(list(df_mpo.drop([weight, 'ME'         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_mpo2 = df_mpo.groupby(list(df_mpo.drop([weight, 'ME', 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_mpo2.loc[:, 'RAC1P'] = 'All'
            df_mpo2 = pd.concat([df_mpo1, df_mpo2])
            df_mpo3 = df_mpo2[df_mpo2['housing_type'].isin(['Owner', 'Renter'])]
            df_mpo3 = df_mpo3.groupby(list(df_mpo3.drop(['Total', 'ME', 'housing_type'], axis=1).columns), as_index=False).agg(Total=('Total', 'sum'), ME=('ME', sqrtsumsq))
            df_mpo3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_mpo = pd.concat([df_mpo2, df_mpo3])

            df_puma    ['ME_ratio'] = df_puma    ['ME']/df_puma    ['Total']
            df_counties['ME_ratio'] = df_counties['ME']/df_counties['Total']
            df_msa     ['ME_ratio'] = df_msa     ['ME']/df_msa     ['Total']
            df_mpo     ['ME_ratio'] = df_mpo     ['ME']/df_mpo     ['Total']
        
        else:
            df_puma     = df_puma    .groupby(list(df_puma    .drop([weight, 'ME'], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_counties = df_counties.groupby(list(df_counties.drop([weight, 'ME'], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_msa      = df_msa     .groupby(list(df_msa     .drop([weight, 'ME'], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
            df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight, 'ME'], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'), ME=('ME', sqrtsumsq))
        
        df_puma    ['ME_ratio'] = df_puma    ['ME']/df_puma    ['Total']
        df_counties['ME_ratio'] = df_counties['ME']/df_counties['Total']
        df_msa     ['ME_ratio'] = df_msa     ['ME']/df_msa     ['Total']
        df_mpo     ['ME_ratio'] = df_mpo     ['ME']/df_mpo     ['Total']
        
        conditions = [df_puma['ME_ratio'] <= MOE_thresh, df_puma['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_puma['Use for Reporting'] = np.select(conditions, choices, default='No')
        
        conditions = [df_counties['ME_ratio'] <= MOE_thresh, df_counties['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_counties['Use for Reporting'] = np.select(conditions, choices, default='No')
        
        conditions = [df_msa['ME_ratio'] <= MOE_thresh, df_msa['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_msa['Use for Reporting'] = np.select(conditions, choices, default='No')
        
        conditions = [df_mpo['ME_ratio'] <= MOE_thresh, df_mpo['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_mpo['Use for Reporting'] = np.select(conditions, choices, default='No')
    
    if margin_of_error == 'No':
        if indicator in ['Income_2', 'Accessibility_2', 'Accessibility_3', 'Accessibility_4']:
            if indicator == 'Accessibility_4':
                df_puma1     = df_puma    .groupby(group_puma     + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties1 = df_counties.groupby(group_counties + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa1      = df_msa     .groupby(group_msa      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo1      = df_mpo     .groupby(group_mpo      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_puma2     = df_puma    .groupby(group_puma     + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties2 = df_counties.groupby(group_counties + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa2      = df_msa     .groupby(group_msa      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo2      = df_mpo     .groupby(group_mpo      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_puma1    .loc[:, 'Income Bracket'] = 'All'
                df_counties1.loc[:, 'Income Bracket'] = 'All'
                df_msa1     .loc[:, 'Income Bracket'] = 'All'
                df_mpo1     .loc[:, 'Income Bracket'] = 'All'
                df_puma2    .loc[:, 'RAC1P'] = 'All'
                df_counties2.loc[:, 'RAC1P'] = 'All'
                df_msa2     .loc[:, 'RAC1P'] = 'All'
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_puma     = pd.concat([df_puma1    , df_puma2    ])
                df_counties = pd.concat([df_counties1, df_counties2])
                df_msa      = pd.concat([df_msa1     , df_msa2     ])
                df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])
            if indicator == 'Accessibility_3':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo1     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH', 'RAC1P'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo2     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_mpo      = pd.concat([df_mpo1, df_mpo2])
            if indicator == 'Accessibility_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
            if indicator == 'Income_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                
        if indicator == 'Cost_6':
            df_puma1 = df_puma.groupby(list(df_puma.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_puma2 = df_puma.groupby(list(df_puma.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_puma2.loc[:, 'RAC1P'] = 'All'
            df_puma2 = pd.concat([df_puma1, df_puma2])
            df_puma3 = df_puma2[df_puma2['housing_type'].isin(['Owner', 'Renter'])]
            df_puma3 = df_puma3.groupby(list(df_puma3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=('Total', 'sum'))
            df_puma3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_puma3['Percentage'] = df_puma3['Total']/df_puma3.groupby(list(df_puma3.drop(['housing_burden', 'Total'], axis=1).columns))['Total'].transform('sum')
            df_puma = pd.concat([df_puma2, df_puma3])

            df_counties1 = df_counties.groupby(list(df_counties.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_counties2 = df_counties.groupby(list(df_counties.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_counties2.loc[:, 'RAC1P'] = 'All'
            df_counties2 = pd.concat([df_counties1, df_counties2])
            df_counties3 = df_counties2[df_counties2['housing_type'].isin(['Owner', 'Renter'])]
            df_counties3 = df_counties3.groupby(list(df_counties3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_counties3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_counties = pd.concat([df_counties2, df_counties3])

            df_msa1 = df_msa.groupby(list(df_msa.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_msa2 = df_msa.groupby(list(df_msa.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_msa2.loc[:, 'RAC1P'] = 'All'
            df_msa2 = pd.concat([df_msa1, df_msa2])
            df_msa3 = df_msa2[df_msa2['housing_type'].isin(['Owner', 'Renter'])]
            df_msa3 = df_msa3.groupby(list(df_msa3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_msa3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_msa = pd.concat([df_msa2, df_msa3])
            
            df_mpo1 = df_mpo.groupby(list(df_mpo.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_mpo2 = df_mpo.groupby(list(df_mpo.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_mpo2.loc[:, 'RAC1P'] = 'All'
            df_mpo2 = pd.concat([df_mpo1, df_mpo2])
            df_mpo3 = df_mpo2[df_mpo2['housing_type'].isin(['Owner', 'Renter'])]
            df_mpo3 = df_mpo3.groupby(list(df_mpo3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_mpo3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_mpo = pd.concat([df_mpo2, df_mpo3])

        else:
            df_puma     = df_puma    .groupby(list(df_puma    .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
            df_counties = df_counties.groupby(list(df_counties.drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
            df_msa      = df_msa     .groupby(list(df_msa     .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
            df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
    
    if 'RAC1P' in groups:# and indicator not in ['Cost_6', 'Accessibility_1']:
        groups.remove('RAC1P')
        groups = ['RAC1P'] + groups

    if percentages == 'Yes':
        if margin_of_error == 'Yes':
            if len(groups) > 1:
                df_puma    ['Percentage'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop([groups[-1]] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop([groups[-1]] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop([groups[-1]] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_mpo     ['Percentage'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop([groups[-1]] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
            if len(groups) == 1:
                df_puma    ['Percentage'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_mpo     ['Percentage'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
        if margin_of_error == 'No':
            if len(groups) > 1:
                df_puma    ['Percentage'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_mpo     ['Percentage'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
            if len(groups) == 1:
                df_puma    ['Percentage'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups      + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups      + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups      + ['Total'], axis=1).columns))['Total'].transform('sum')           
                df_mpo     ['Percentage'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups      + ['Total'], axis=1).columns))['Total'].transform('sum')

    df_puma    .reset_index(drop=True, inplace=True)
    df_counties.reset_index(drop=True, inplace=True)
    df_msa     .reset_index(drop=True, inplace=True)
    df_mpo     .reset_index(drop=True, inplace=True)

    if indicator == 'Accessibility_4':
        if percentages == 'Yes':
            df_puma2     = df_puma    [df_puma    ['RAC1P'] != 'All']
            df_counties2 = df_counties[df_counties['RAC1P'] != 'All']
            df_msa2      = df_msa     [df_msa     ['RAC1P'] != 'All']
            df_mpo2      = df_mpo     [df_mpo     ['RAC1P'] != 'All']
            df_puma1     = df_puma    [df_puma    ['RAC1P'] == 'All']
            df_counties1 = df_counties[df_counties['RAC1P'] == 'All']
            df_msa1      = df_msa     [df_msa     ['RAC1P'] == 'All']
            df_mpo1      = df_mpo     [df_mpo     ['RAC1P'] == 'All']
            groups.remove('Income Bracket')
            groups = groups + ['Income Bracket']
            if margin_of_error == 'Yes':
                df_puma1     = df_puma1    .drop('Percentage', axis=1)
                df_counties1 = df_counties1.drop('Percentage', axis=1)
                df_msa1      = df_msa1     .drop('Percentage', axis=1)
                df_mpo1      = df_mpo1     .drop('Percentage', axis=1)
                df_puma1    ['Percentage'] = df_puma1    ['Total'] / df_puma1    .groupby(list(df_puma1    .drop(groups[:-1] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_counties1['Percentage'] = df_counties1['Total'] / df_counties1.groupby(list(df_counties1.drop(groups[:-1] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_msa1     ['Percentage'] = df_msa1     ['Total'] / df_msa1     .groupby(list(df_msa1     .drop(groups[:-1] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_mpo1     ['Percentage'] = df_mpo1     ['Total'] / df_mpo1     .groupby(list(df_mpo1     .drop(groups[:-1] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
            df_puma     = pd.concat([df_puma1    , df_puma2    ])
            df_counties = pd.concat([df_counties1, df_counties2])
            df_msa      = pd.concat([df_msa1     , df_msa2     ])
            df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])

    return df_puma, df_counties, df_msa, df_mpo, groups



## ---


## CPS processing steps ---

## FOODSEC processing step (4) (use 1-3 from PUMS process steps)

def food_processing_4(df_census, weight, percentages, groups):

    print()
    print('Processing 4:')
    print('Rolling up estimtaes to desired group variables and geographies, and calculating percentages...')
    print()

    if 'PTDTRACE' in groups:
        groups.remove('PTDTRACE')
        groups_to_drop=groups.copy()
        groups = ['PTDTRACE'] + groups

    df_counties = df_census.drop([                              'Household_ID', 'Householder', 'PERRP'], axis=1)
    df_mpo      = df_census.drop(['County FIPS', 'County Name', 'Household_ID', 'Householder', 'PERRP'], axis=1)

    group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
    group_mpo      = ['State FIPS', 'MPO'                              ]

    df_counties = df_counties.set_index(group_counties).reset_index()
    df_mpo      = df_mpo     .set_index(group_mpo     ).reset_index()

    df_counties = df_counties.drop('Year', axis=1)
    df_mpo      = df_mpo     .drop('Year', axis=1)

    df_counties[weight] = 1
    df_mpo     [weight] = 1

    df_counties = df_counties.groupby(list(df_counties.drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
    df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))

    if percentages == 'Yes':
        df_counties['Percentage'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups_to_drop + ['Total'], axis=1).columns))['Total'].transform('sum')
        df_mpo     ['Percentage'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups_to_drop + ['Total'], axis=1).columns))['Total'].transform('sum')

    df_counties['Total'] = round(df_counties['Total'])
    df_mpo     ['Total'] = round(df_mpo     ['Total'])

    df_counties['Total'] = df_counties['Total'].astype(int)
    df_mpo     ['Total'] = df_mpo     ['Total'].astype(int)

    return df_counties, df_mpo, groups


## ---




## LEHD processing steps ---

def lehd_processing(df_census, geography, indicator, percentages, df_fips=None):
    if indicator == 'Jobs_4':
        df_census = df_census[df_census['Emp'] != 'null']
        df_census = df_census[~df_census['Emp'].isna()]
        df_census['Emp'    ] = df_census['Emp'    ].astype('int')
        df_census['firmage'] = df_census['firmage'].astype('int')
        df_census = df_census[df_census['firmage'] != 0]
        df_census.loc[ df_census['firmage'].isin([1, 2, 3]), 'Firm Age'] = 'Less than or equal to 5 years old'
        df_census.loc[~df_census['firmage'].isin([1, 2, 3]), 'Firm Age'] = 'Greater than 5 years old'
        df_census = df_census.drop(['Year', 'ownercode', 'firmage'], axis=1)

        df_census = df_census.rename(columns={'time':'Quarter'})
        # df_census = df_census[df_census['Quarter'].str.contains('Q3')] # remove this if you want to show all quarters

        if geography == 'Counties':

            df_mpo = df_fips[['County Name', 'MPO']]
            df_census = df_census.merge(df_mpo, on=['County Name'], how='left')
            
            df_census = df_census[['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Quarter', 'Firm Age', 'Emp']]
            df_census['Emp'] = df_census['Emp'].astype('int')

            df_census['State FIPS' ] = df_census['State FIPS' ].astype(str).apply('{:0>2}'.format)
            df_census['County FIPS'] = df_census['County FIPS'].astype(str).apply('{:0>3}'.format)

            df_counties = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Quarter', 'Firm Age'], as_index=False).agg(Total=('Emp', 'sum'))
            df_mpo      = df_census.groupby(['State FIPS', 'MPO',                               'Quarter', 'Firm Age'], as_index=False).agg(Total=('Emp', 'sum'))
            
            df_counties = df_counties.sort_values(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Quarter', 'Firm Age'], ascending=[True, True, True, True, False, False])
            df_mpo      = df_mpo     .sort_values(['State FIPS', 'MPO',                               'Quarter', 'Firm Age'], ascending=[True, True, False, False])
            
            df_counties = df_counties.reset_index(drop=True)
            df_mpo      = df_mpo     .reset_index(drop=True)

            if percentages == 'Yes':
                df_counties['Percentage'] = df_counties['Total'] / df_counties.groupby(['State FIPS',        'County FIPS', 'Quarter'])['Total'].transform('sum')
                df_mpo     ['Percentage'] = df_mpo     ['Total'] / df_mpo     .groupby(['State FIPS', 'MPO',                'Quarter'])['Total'].transform('sum')

        if geography == 'MSA':
            
            df_census = df_census[['MSA_ID', 'MSA', 'Quarter', 'Firm Age', 'Emp']]

            df_msa = df_census.groupby(['MSA_ID', 'MSA', 'Quarter', 'Firm Age'], as_index=False).agg(Total=('Emp', 'sum'))
            df_msa = df_msa.sort_values(['MSA', 'Quarter', 'Firm Age'], ascending=[True, False, False])
            df_msa = df_msa.reset_index(drop=True)

            if percentages == 'Yes':
                df_msa['Percentage'] = df_msa['Total'] / df_msa.groupby(['MSA', 'Quarter'])['Total'].transform('sum')

    if geography == 'Counties':
        return df_counties, df_mpo
    if geography == 'MSA':
        return df_msa
    




    
def clean_pop_6(df_census, geography):

    # Some indicators require the roll up to be weighted by population
    # The following step aligns the Race/Ethnicity mappings with the population counts workbook
    path_weights = path_main / 'Reference' / 'Weights'
    file_weights = path_weights / f'Pop_3 {geography} {estimate}.xlsx'
    if geography in ['Block Groups', 'Tracts', 'Counties', 'MPO', 'States', 'National', 'Places', 'MSA']:
        df_pop = pd.read_excel(file_weights, sheet_name=geography)
    elif geography == 'Congressional Districts':
        df_pop = pd.read_excel(file_weights, sheet_name='CD')
    elif geography == 'State Legislative Upper Districts':
        df_pop = pd.read_excel(file_weights, sheet_name='SLDU')
    elif geography == 'State Legislative Lower Districts':
        df_pop = pd.read_excel(file_weights, sheet_name='SLDL')

    # if geography == 'MSA':
    #     cols_merge = ['MSA_ID', 'Year', 'Race_Ethnicity', metric]
    # elif geography == 'MPO':
    #     cols_merge = ['MPO', 'Year', 'Race_Ethnicity', metric]
    # else:
    #     cols_merge = ['NAME', 'Year', 'Race_Ethnicity', metric]

    # df_census = df_census.merge(df_pop, on=cols_merge, how='left')

    df_pop = df_pop.rename(columns={'Population': f'Total {metric}'})

    conditions = [
                    (df_pop["Race_Ethnicity"] == 'All'                                            ),
                    (df_pop["Race_Ethnicity"] == 'American Indian or Alaska Native (NH)'          ),
                    (df_pop["Race_Ethnicity"] == 'Asian (NH)'                                     ),
                    (df_pop["Race_Ethnicity"] == 'Black or African American (NH)'                 ),
                    (df_pop["Race_Ethnicity"] == 'Hispanic or Latino'                             ),
                    (df_pop["Race_Ethnicity"] == 'Native Hawaiian or other Pacific Islander (NH)' ),
                    (df_pop["Race_Ethnicity"] == 'White (NH)'                                     ),
                    (df_pop["Race_Ethnicity"] == 'Some other race (NH)'                           ),
                    (df_pop["Race_Ethnicity"] == 'Two or more races (NH)'                         )
                ]
    choices = ["All", "American Indian or Alaska Native", "Asian", "Black or African American", "Hispanic or Latino",
                "Native Hawaiian or other Pacific Islander", "White (NH)", "Some other race", "Two or more races"]
    df_pop["Race_Ethnicity"] = np.select(conditions, choices)

    if geography == 'MSA':
        cols_merge = ['MSA_ID', 'Year', 'Race_Ethnicity']
    elif geography == 'MPO':
        cols_merge = ['MPO', 'Year', 'Race_Ethnicity']
    else:
        cols_merge = ['NAME', 'Year', 'Race_Ethnicity']

    df_census = df_census.merge(df_pop, on=cols_merge, how='left')

    df_census['Total Population'] = df_census['Total Population'].fillna(0)
    df_census['Total Population'] = df_census['Total Population'].replace(0, 1)
    df_census['Birth Rate Per 1,000 People'] = (df_census['Population'] / df_census['Total Population']) * 1000
    df_census = df_census[df_census['Variable'] == 'Woman aged 15-44 who had a birth in the past 12 months']
    
    return df_census


def clean_pop_7(df_census, geography):

    if geography == 'Places':
        geo_ID = ['State FIPS', 'County Name', 'Place ID', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
    if geography == 'Counties':
        geo_ID = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'MSA']
    if geography == 'Congressional Districts':
        geo_ID = ['State FIPS', 'Congressional District', 'NAME']
    if geography == 'State Legislative Upper Districts':
        geo_ID = ['State FIPS', 'State Legislative Upper District', 'NAME']
    if geography == 'State Legislative Lower Districts':
        geo_ID = ['State FIPS', 'State Legislative Lower District', 'NAME']
    if geography == 'States':
        geo_ID = ['State FIPS', 'NAME']
    if geography == 'National':
        geo_ID = ['NAME']

    df_census['Total Population'] = df_census.groupby(geo_ID + ['Year'])['Population'].transform('sum')

    df_census['Marriage Rate Per 1,000 People'] = (df_census['Population'] / df_census['Total Population']) * 1000
    df_census = df_census[df_census['Variable'] == 'Married last year']
    df_census = df_census.drop_duplicates()
    df_census = df_census.reset_index(drop=True)
    
    return df_census






## ---





## Final organization/renaming of census data

'''
User defined function to finalize organizing of Census Bureau tables, based on SACOG specific indicators
'''

def rename_census(
        indicator, geography, sample_type, margin_of_error=None, percentages=None, groups=None, table_type=None, df_vars=None,
        df_census=None, df_puma=None, df_counties=None, df_msa=None, df_mpo=None
        ):
    

    if geography == 'Places':
        geo_ID = ['State FIPS', 'County Name', 'Place ID', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
    if geography == 'Counties':
        if mpo == 'Yes':
            geo_ID = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME']
        else:
            geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'MSA']
    if geography == 'Congressional Districts':
        geo_ID = ['State FIPS', 'Congressional District', 'NAME']
    if geography == 'State Legislative Upper Districts':
        geo_ID = ['State FIPS', 'State Legislative Upper District', 'NAME']
    if geography == 'State Legislative Lower Districts':
        geo_ID = ['State FIPS', 'State Legislative Lower District', 'NAME']
    if geography == 'States':
        geo_ID = ['State FIPS', 'NAME']
    if geography == 'National':
        geo_ID = ['NAME']


    if margin_of_error == 'Yes':
        if sample_type in ['ACS', 'SUBJECT', 'DEC']:
            if percentages == 'No':
                df_census = df_census[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
                if geography == 'Counties':
                    if mpo == 'Yes':
                        df_mpo = df_mpo[['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
            else:
                df_census = df_census[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
                if geography == 'Counties':
                    if mpo == 'Yes':
                        df_mpo = df_mpo[['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_census = df_census.rename(columns={'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            if geography == 'Counties':
                if mpo == 'Yes':
                    df_mpo = df_mpo.rename(columns={'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})

        if sample_type == 'PUMS':
            if indicator not in ['Accessibility_2']:
                groups.reverse()
            if indicator == 'Cost_6':
                groups = ['RAC1P', 'housing_type', 'housing_burden']
            if indicator == 'Accessibility_4':
                groups = ['RAC1P', 'Income Bracket', 'Travel Time']
            if indicator == 'Accessibility_3':
                groups = ['VEH']
                groups_mpo = ['RAC1P', 'VEH']

            df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_counties = df_counties[group_counties + ['Year'] + groups + ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            if indicator == 'Accessibility_3':
                df_mpo = df_mpo[group_mpo + ['Year'] + groups_mpo + ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            else:
                df_mpo = df_mpo[group_mpo + ['Year'] + groups + ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_puma     = df_puma    .rename(columns={'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_counties = df_counties.rename(columns={'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_msa      = df_msa     .rename(columns={'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_mpo      = df_mpo     .rename(columns={'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})

    if margin_of_error == 'No':
        if sample_type  in ['ACS', 'SUBJECT', 'DEC']:
            if percentages == 'No':
                df_census = df_census[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total']]
                if geography == 'Counties':
                    if mpo == 'Yes':
                        df_mpo = df_mpo[['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total']]
            else:
                df_census = df_census[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]
                if geography == 'Counties':
                    if mpo == 'Yes':
                        df_mpo = df_mpo[['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]

        if sample_type == 'PUMS':
            groups.reverse()
            if percentages == 'Yes':
                df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total', 'Percentage']]
                df_counties = df_counties[group_counties + ['Year'] + groups + ['Total', 'Percentage']]
                df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total', 'Percentage']]
                df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups + ['Total', 'Percentage']]
            else:
                df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total']]
                df_counties = df_counties[group_counties + ['Year'] + groups + ['Total']]
                df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total']]
                df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups + ['Total']]
        if sample_type == 'FOODSEC':
            df_counties = df_counties[group_counties + groups + ['Total', 'Percentage']]
            df_mpo      = df_mpo     [group_mpo      + groups + ['Total', 'Percentage']]

    if geography == 'Places':
        df_census = df_census.sort_values(['State FIPS', 'County Name', 'Place ID', 'Year'], ascending=[True, True, True, False])
        df_census = df_census.reset_index(drop=True)

    if geography == 'PUMA':
        if table_type == 'P':
            df_puma     = df_puma    .rename(columns={'Total':'Population'})
            df_counties = df_counties.rename(columns={'Total':'Population'})
            df_msa      = df_msa     .rename(columns={'Total':'Population'})
            df_mpo      = df_mpo     .rename(columns={'Total':'Population'})
        if table_type == 'H':
            df_puma     = df_puma    .rename(columns={'Total':'Households'})
            df_counties = df_counties.rename(columns={'Total':'Households'})
            df_msa      = df_msa     .rename(columns={'Total':'Households'})
            df_mpo      = df_mpo     .rename(columns={'Total':'Households'})
        df_puma     = df_puma    .sort_values(group_puma     + ['Year'] + groups, ascending=[True, True, True, True, False] + [item in groups for item in groups])
        df_counties = df_counties.sort_values(group_counties + ['Year'] + groups, ascending=[True, True, True, True, False] + [item in groups for item in groups])
        df_msa      = df_msa     .sort_values(group_msa      + ['Year'] + groups, ascending=[True, True, True,       False] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + ['Year'] + groups, ascending=[True, True,             False] + [item in groups for item in groups])
    if sample_type == 'FOODSEC':
        if table_type == 'P':
            df_counties = df_counties.rename(columns={'Total':'Population'})
            df_mpo      = df_mpo     .rename(columns={'Total':'Population'})
        if table_type == 'H':
            df_counties = df_counties.rename(columns={'Total':'Households'})
            df_mpo      = df_mpo     .rename(columns={'Total':'Households'})
        df_counties = df_counties.sort_values(group_counties + groups, ascending=[True, True, True, True] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + groups, ascending=[True, True,           ] + [item in groups for item in groups])
        if 'PTDTRACE' in groups:
            df_counties = df_counties.set_index(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'PTDTRACE']).reset_index()
            df_mpo      = df_mpo     .set_index(['State FIPS', 'MPO',                               'PTDTRACE']).reset_index()


    ## Renaming specifically by indicators
    if indicator in ['Income_3']:
        path_inc = path_main / 'Vibrant and Inclusive Places' / 'Economy' / 'Income' / 'Income_1 HH Income'
        file_inc = path_inc / 'Income_1 MPO ACS5.xlsx'
        df_mpo_wm = pd.read_excel(file_inc, sheet_name='MPO')
        df_mpo_wm = df_mpo_wm[df_mpo_wm['Race_Ethnicity'] == 'All'].reset_index(drop=True)
    
        df_census = df_census.merge(df_mpo_wm[['Year', 'Median Household Income']].rename(columns={'Median Household Income':'Regional Median Household Income'}), on=['Year'], how='left')
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo = df_mpo.merge(df_mpo_wm[['Year', 'Median Household Income']].rename(columns={'Median Household Income':'Regional Median Household Income'}), on=['Year'], how='left')
    
        df_census['Percent of Regional Median Household Income'] = (df_census['Total']/df_census['Regional Median Household Income'])
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo['Percent of Regional Median Household Income'] = (df_mpo['Total']/df_mpo['Regional Median Household Income'])

    if indicator == 'Accessibility_1':
        factor_commutes = ['Car, truck, or van', 'Public transportation (bus, subway, or rail)', 'Bicycle', 'Walked', 'Other method', 'Worked from home']
        df_puma    ['JWTRNS_sort'] = pd.Categorical(df_puma    ['JWTRNS'], factor_commutes)
        df_counties['JWTRNS_sort'] = pd.Categorical(df_counties['JWTRNS'], factor_commutes)
        df_msa     ['JWTRNS_sort'] = pd.Categorical(df_msa     ['JWTRNS'], factor_commutes)
        df_mpo     ['JWTRNS_sort'] = pd.Categorical(df_mpo     ['JWTRNS'], factor_commutes)

        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True,  True,  True, False, True, True])
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True,  True,  True, False, True, True])
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True,  True, False,  True, True      ])
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True, False,  True,  True            ])

        df_puma     = df_puma    .drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
        df_counties = df_counties.drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
        df_msa      = df_msa     .drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
        df_mpo      = df_mpo     .drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
            
    if indicator == 'Accessibility_2':
        factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)

        factor_commutes = ['Car, truck, or van', 'Public transportation (bus, subway, or rail)', 'Bicycle', 'Walked', 'Worked from home', 'Other method']
        df_puma    ['JWTRNS_sort'] = pd.Categorical(df_puma    ['JWTRNS'], factor_commutes)
        df_counties['JWTRNS_sort'] = pd.Categorical(df_counties['JWTRNS'], factor_commutes)
        df_msa     ['JWTRNS_sort'] = pd.Categorical(df_msa     ['JWTRNS'], factor_commutes)
        df_mpo     ['JWTRNS_sort'] = pd.Categorical(df_mpo     ['JWTRNS'], factor_commutes)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True, True, True, False, True, True])
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True, True, True, False, True, True])
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True, True, False, True, True])
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True, False, True, True])

        df_puma     = df_puma    .drop(['Income_sort', 'JWTRNS_sort'], axis=1)
        df_counties = df_counties.drop(['Income_sort', 'JWTRNS_sort'], axis=1)
        df_msa      = df_msa     .drop(['Income_sort', 'JWTRNS_sort'], axis=1)
        df_mpo      = df_mpo     .drop(['Income_sort', 'JWTRNS_sort'], axis=1)    

    if indicator == 'Accessibility_4':
        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)
        
        factor_incomes = ['All', 'No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)

        factor_times = ['No commute (worked from home)', '0 to 15 minutes', '15 to 30 minutes', 'More than 30 minutes']
        df_puma    ['Travel_sort'] = pd.Categorical(df_puma    ['Travel Time'], factor_times)
        df_counties['Travel_sort'] = pd.Categorical(df_counties['Travel Time'], factor_times)
        df_msa     ['Travel_sort'] = pd.Categorical(df_msa     ['Travel Time'], factor_times)
        df_mpo     ['Travel_sort'] = pd.Categorical(df_mpo     ['Travel Time'], factor_times)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True, True, True, False, True, True, True])
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True, True, True, False, True, True, True])
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True, True, False, True, True, True])
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True, False, True, True, True])

        df_puma     = df_puma    .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)
        df_counties = df_counties.drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)
        df_msa      = df_msa     .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)
        df_mpo      = df_mpo     .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)

    if indicator == 'Accessibility_3':
        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_mpo['RAC1P_sort'] = pd.Categorical(df_mpo['RAC1P'], factor_race)
        df_mpo = df_mpo.sort_values(by= group_mpo + ['Year', 'RAC1P_sort', 'VEH'], ascending=[True, True, False, True, True])
        df_mpo = df_mpo.drop(['RAC1P_sort'], axis=1)
        
    if indicator == 'Income_2':
        factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)
        
        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'Income_sort'], ascending=[True, True, True, True, False, True])
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'Income_sort'], ascending=[True, True, True, True, False, True])
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'Income_sort'], ascending=[True, True, True, False, True])
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'Income_sort'], ascending=[True, True, False, True])

        df_puma     = df_puma    .drop(['Income_sort'], axis=1)
        df_counties = df_counties.drop(['Income_sort'], axis=1)
        df_msa      = df_msa     .drop(['Income_sort'], axis=1)
        df_mpo      = df_mpo     .drop(['Income_sort'], axis=1)

    if indicator == 'Cost_6':
        factor_burden = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Cost burden <=30%', 'Cost burden >30% to <=50%', 'Cost burden >50%']
        df_puma    ['housing_burden_sort'] = pd.Categorical(df_puma    ['housing_burden'], factor_burden)
        df_counties['housing_burden_sort'] = pd.Categorical(df_counties['housing_burden'], factor_burden)
        df_msa     ['housing_burden_sort'] = pd.Categorical(df_msa     ['housing_burden'], factor_burden)
        df_mpo     ['housing_burden_sort'] = pd.Categorical(df_mpo     ['housing_burden'], factor_burden)

        factor_types = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Owner', 'Renter', 'Owners and Renters']
        df_puma    ['housing_type_sort'] = pd.Categorical(df_puma    ['housing_type'], factor_types)
        df_counties['housing_type_sort'] = pd.Categorical(df_counties['housing_type'], factor_types)
        df_msa     ['housing_type_sort'] = pd.Categorical(df_msa     ['housing_type'], factor_types)
        df_mpo     ['housing_type_sort'] = pd.Categorical(df_mpo     ['housing_type'], factor_types)

        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True,  True,  True, False, True, True, True])
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True,  True,  True, False, True, True, True])
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True,  True, False,  True, True, True      ])
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True, False,  True,  True, True            ])

        df_puma     = df_puma    .drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1)
        df_counties = df_counties.drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1)
        df_msa      = df_msa     .drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1)
        df_mpo      = df_mpo     .drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1)

        df_puma     = df_puma    .rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})
        df_counties = df_counties.rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})
        df_msa      = df_msa     .rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})
        df_mpo      = df_mpo     .rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})

    if geography == 'Counties':
        if mpo == 'Yes':
            df_mpo = df_mpo.merge(df_vars[['Variable', 'Race_Ethnicity', 'Sort']].drop_duplicates(), on=['Variable', 'Race_Ethnicity'], how='left')
            df_mpo['Race_Ethnicity_sort'] = pd.Categorical(df_mpo['Race_Ethnicity'], [
                                                                    'All'
                                                                    , 'American Indian or Alaska Native'
                                                                    , 'American Indian or Alaska Native (NH)'
                                                                    , 'Asian'
                                                                    , 'Asian (NH)'
                                                                    , 'Black or African American'
                                                                    , 'Black or African American (NH)'
                                                                    , 'Hispanic or Latino'
                                                                    , 'Native Hawaiian or other Pacific Islander'
                                                                    , 'Native Hawaiian or other Pacific Islander (NH)'
                                                                    , 'White'
                                                                    , 'White (NH)'
                                                                    , 'Some other race'
                                                                    , 'Some other race (NH)'
                                                                    , 'Two or more races'
                                                                    , 'Two or more races (NH)'
                                                                ])
            
            df_mpo = df_mpo.sort_values(by= ['State FIPS', 'MPO', 'Year', 'Race_Ethnicity_sort', 'Sort'], ascending=[True, True, False, True, True])
            df_mpo = df_mpo.drop(['Race_Ethnicity_sort', 'Sort'], axis=1)
            df_mpo = df_mpo.drop_duplicates()

    if geography != 'PUMA':
        df_census = df_census.rename(columns={'Total': metric})
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo = df_mpo.rename(columns={'Total': metric})
    else:
        df_puma     = df_puma    .rename(columns={'Total': metric})
        df_counties = df_counties.rename(columns={'Total': metric})
        df_msa      = df_msa     .rename(columns={'Total': metric})
        df_mpo      = df_mpo     .rename(columns={'Total': metric})

    if indicator == 'Pop_6':
        df_census = clean_pop_6(df_census, geography)
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo = clean_pop_6(df_mpo, 'MPO')

    if indicator == 'Pop_7':
        df_census = clean_pop_7(df_census, geography)
        if geography == 'Counties':
            if mpo == 'Yes':
                df_mpo = clean_pop_7(df_mpo, 'MPO')

    if geography == 'Counties':
        if sample_type in ['ACS', 'SUBJECT', 'DEC']:
            if mpo == 'Yes':
                return df_census, df_mpo
            else:
                return df_census
    elif geography == 'PUMA':
        return df_puma, df_counties, df_msa, df_mpo
    else:
        return df_census





## Exporting ------------------------------


def export_indicator(indicator, geography, df_census, path_wb, about):
    print()
    print('Excel files exported here: ' + str(path_wb))

    writer = pd.ExcelWriter(path_wb, engine='xlsxwriter')
    
    if geography == 'Congressional Districts':
        sheet_geo = 'CD'
    elif geography == 'State Legislative Lower Districts':
        sheet_geo = 'SLDL'
    elif geography == 'State Legislative Upper Districts':
        sheet_geo = 'SLDU'
    elif 'MPO' in str(path_wb):
        sheet_geo = 'MPO'
    else:
        sheet_geo = geography

    if about:
        df_about.to_excel(writer, sheet_name='About'  , index=False, header=False)
    
    df_census.to_excel(writer, sheet_name=sheet_geo, index=False, header=True)
    
    workbook = writer.book
    
    format_numbers = workbook.add_format({'num_format': '#,##0' })
    formet_percent = workbook.add_format({'num_format': '0.0%'  })
    formet_dollars = workbook.add_format({'num_format': '$#,##0'})
    

    worksheet = writer.sheets[sheet_geo]
    
    try:
        idx_col = df_census.columns.get_loc('Population')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Households')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Housing Units')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Margin of Error')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Percentage')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Margin of Error Ratio')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
        idx_col = df_census.columns.get_loc('Margin of Error')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
        idx_col = df_census.columns.get_loc('Regional Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
        idx_col = df_census.columns.get_loc('Percent of Regional Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Total Population')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Birth Rate Per 1,000 People')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df_census.columns.get_loc('Marriage Rate Per 1,000 People')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass


    worksheet.autofit()
    
    writer.close()

    print()
    print("Successfully exported!")
    print()