### Packages -----------------------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd
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

# Plotting
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio





### GENERAL FUNCTIONS ----------------------------------------------------------------------------------------------------------------- 


# Aggregations
wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
sqrtsumsq  = lambda x: np.sqrt(np.sum(x**2))                                      # Square root of the sum of squares (to roll up SE's when +/- random variables)
# sqrtsumsq  = lambda x: np.sqrt(np.sum((x/1.645)**2))                            # check that these work out the same way        
# Doing the square root of the sum of squared ME's is equivalent to doing it on the SE's, I proved it once, did not take notes, sorry, just trust me


# function to get unique values
def unique(list1):
 
    # initialize a null list
    unique_list = []
 
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list


# Function to create list of values inbetween range
def sequence(r1, r2, step):
    return [item for item in range(r1, r2+1, step)]


# Remove anything after specified string, use regular expression (currently set to remove everything after the first period)
def re_remove_post(x, exp = '.'):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[0]


# Split attributes string
def ME_split(text):
    return ",".join(text.split(',')[0:3:2])




### CENSUS FUNCTIONS -----------------------------------------------------------------------------------------------------------------



# Split attributes string
def ME_split(text):
    return ",".join(text.split(',')[0:3:2])

# Split attributes string
def ME_split(text):
    return ",".join(text.split(',')[0:3:2])

group_puma     = ['State FIPS', 'MPO', 'PUMA'       , 'PUMA NAME'  ]
group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
group_msa      = ['State FIPS',        'MSA_ID'     , 'MSA'        ]
group_mpo      = ['State FIPS', 'MPO'                              ]



# Main function used to query data
def query_census(
        df_urls
        , api_key, estimate, sample, geography, variables, year
        , state=None, county=None, msa=None, puma=None
    ):
        
    '''
    User defined function to import Data from the Census Bureau
    User inputs: [api_key, estimate, geography variables, year] to tell ACS that we have access with the API key and
                    what type of sample data to pull, which variables we want to import, what year, 
                    and which state and record type (persons or households)
                    - record type is for PUMS data only
                    - only pulls 1 year at a time (geography IDs, like census tracts, change at the start of each decade)
    '''

    # Assert that inputs for estimate and geography are appropriate

    assert estimate  in ['ACS5'  , 'ACS1'    , 'DEC', 'CPS'                       ], "Unacceptable estimate input, requires 'ACS5', 'ACS1', 'DEC', or 'CPS' "
    assert sample    in ['ACS'   , 'DEC'     , 'DHC', 'PUMS', 'FOODSEC', 'SUBJECT'], "Unacceptable estimate input, requires 'ACS', 'DEC', 'DHS', 'PUMS_h', 'PUMS_p', 'FOODSEC', or 'SUBJECT'"
    assert geography in ['Tracts', 'Counties', 'MSA', 'PUMA'                      ], "Unacceptable geography input, requires 'Tract', 'County', 'MSA', or 'PUMA' "
    assert estimate  in ['ACS5'  , 'ACS1'    , 'DEC', 'CPS'                           ], "Unacceptable estimate input, requires 'ACS5', 'ACS1', 'DEC', or 'CPS' "
    assert sample    in ['ACS'   , 'DEC'     , 'DHC', 'PUMS', 'FOODSEC', 'SUBJECT'    ], "Unacceptable sample type input, requires 'ACS', 'DEC', 'DHS', 'PUMS_h', 'PUMS_p', 'FOODSEC', or 'SUBJECT'"
    assert geography in ['Places', 'Block Groups', 'Tracts', 'Counties', 'MSA', 'PUMA'], "Unacceptable geography input, requires 'Places', 'Block Groups', 'Tracts', 'Counties', 'MSA', or 'PUMA' "

    assert estimate  in ['ACS5'  , 'ACS1'    , 'DEC', 'CPS'                       ], "Unacceptable estimate input, requires 'ACS5', 'ACS1', 'DEC', or 'CPS' "
    assert sample    in ['ACS'   , 'DEC'     , 'DHC', 'PUMS', 'FOODSEC', 'SUBJECT'], "Unacceptable estimate input, requires 'ACS', 'DEC', 'DHS', 'PUMS_h', 'PUMS_p', 'FOODSEC', or 'SUBJECT'"
    assert geography in ['Tracts', 'Counties', 'MSA', 'PUMA'                      ], "Unacceptable geography input, requires 'Tract', 'County', 'MSA', or 'PUMA' "


    ## Construct URL
    df_url = df_urls[
          (df_urls['Sample'   ] == sample  )
        & (df_urls['Estimate' ] == estimate)
        & (df_urls['c_vintage'] == year    )
        ]

    # Create rootpath and specify dataset type
    df_url
    root_ = df_url['c_url'].values[0]
    g_ = '?get='

    # User inputs for user API key, desired variables and years to import
    api_key_ = f"&key={api_key}"
    variables_ = variables

    # Specify which geography to import

    if geography == 'PUMA':
        location_ =  '&for=public%20use%20microdata%20area:' + puma + '&in=state:' + state
    if geography == 'Counties':
        location_ = '&for=county:' + county + '&in=state:' + state
    if geography == 'Places':
        location_ = '&for=place:*' + '&in=state:' + state
    if geography == 'Block Groups':
        location_ = '&for=block%20group:*' + '&in=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'Tracts':
        location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'Counties':
        location_ = '&for=county:' + county + '&in=state:' + state
    if geography == 'MSA':
        location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)

    
    if geography == 'PUMA':
        location_ =  '&for=public%20use%20microdata%20area:' + puma + '&in=state:' + state

    ## Concatenate constructed URL
    query = f"{root_}{g_}{variables_}{location_}{api_key_}"
    
    ## Call data using URL

    # Use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_census = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_census['Year'] = year
    

    ## Return
    return df_census


def acs_processing_1(df_census, df_vars, indicator_name, geography):

    '''
    User defined function to clean/process ACS data immediately after query
    Replaces weird missing values with np.nan
    Drops rows with all missing
    Melts data from wide to long
    Merges clean variable mapping, race/ethnicity label, and sorting assignment
    Removes unneeded columns
    Adjusts dollars for inflation as needed
    '''

    if geography == 'Tracts':
        df_census = df_census.replace('-666666666', np.nan)
        df_census = df_census.replace('null', np.nan)
        df_census = df_census.dropna(axis = 1, how = 'all')
        
        df_census = pd.melt(df_census
                          , id_vars = ['County Name', 'NAME', 'state', 'county', 'tract', 'Year']
                          , var_name = 'ID'
                          , value_name = 'Total'
                         )
        df_census = df_census.dropna()
        
        df_census['Total'] = df_census['Total'].apply(pd.to_numeric)
        df_census = df_census.merge(df_vars[['ID', 'Label_clean', 'Variable', 'Race_Ethnicity', 'Sort']], on = 'ID', how = 'left')
        df_census = df_census[['ID', 'County Name', 'NAME', 'state', 'Label_clean',
                         'county', 'tract', 'Year', 'Variable', 'Race_Ethnicity', 'Sort', 'Total']]
        df_census = df_census.rename(columns = {
            'ID':'Table ID'
            , 'state':'State FIPS'
            , 'county':'County FIPS'
            , 'tract':'Tract ID'
        })

        if indicator_name in ['Income_1', 'Income_3']:
            df_cpi = pd.read_excel(os.path.join(path_git, 'config', 'CPI Inflation Adjustment Factors.xlsx'), sheet_name = 'BLS_West')
            df_cpi = df_cpi[['Year', 'IAF_' + str(year_end)]]

            df_census = df_census.merge(df_cpi, on = 'Year', how = 'left')
            df_census['Total'] = round(df_census['Total']*df_census['IAF_' + str(year_end)])
            df_census = df_census.drop(['IAF_' + str(year_end)], axis = 1)

        # Some indicators require the roll up to be weighted by population
        # The following step aligns the Race/Ethnicity mappings with the population counts workbook
        if indicator_name in ['Income_3', 'Labor_2']:
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community'
                                            , 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 Tracts ACS5.xlsx'), sheet_name = 'Tracts')
            df_pop = df_pop[['NAME', 'Year','Race_Ethnicity', 'Population']]
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
            df_census = df_census.merge(df_pop, on = ['NAME', 'Year', 'Race_Ethnicity'], how = 'left')
            # df_census = df_census.fillna(0)
            # df_census = df_census.dropna()

    if geography == 'Counties':
        df_census = df_census.replace('null', np.nan)
        df_census = df_census.replace('-666666666', np.nan)
        df_census = df_census.dropna(axis = 1, how = 'all')
        
        df_census = pd.melt(df_census
                          , id_vars = ['County Name', 'NAME', 'state', 'county', 'Year']
                          , var_name = 'ID'
                          , value_name = 'Total'
                         )
        
        df_census['Total'] = df_census['Total'].apply(pd.to_numeric)
        df_census = df_census.merge(df_vars[['ID', 'Label_clean', 'Variable', 'Race_Ethnicity', 'Sort']], on = 'ID', how = 'left')
        df_census = df_census[['ID', 'County Name', 'NAME', 'state', 'Label_clean',
                           'county', 'Year', 'Variable', 'Race_Ethnicity', 'Sort', 'Total']]
        df_census = df_census.rename(columns = {
            'ID':'Table ID'
            , 'state':'State FIPS'
            , 'county':'County FIPS'
        })

        if indicator_name in ['Income_1', 'Income_3']:
            df_cpi = pd.read_excel(os.path.join(path_git, 'config', 'CPI Inflation Adjustment Factors.xlsx'), sheet_name = 'BLS_West')
            df_cpi = df_cpi[['Year', 'IAF_' + str(year_end)]]

            df_census = df_census.merge(df_cpi, on = 'Year', how = 'left')
            df_census['Total'] = round(df_census['Total']*df_census['IAF_' + str(year_end)])
            df_census = df_census.drop(['IAF_' + str(year_end)], axis = 1)
        

        # Some indicators require the roll up to be weighted by population
        # The following step aligns the Race/Ethnicity mappings with the population counts workbook
        if indicator_name in ['Income_3', 'Labor_2']:
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community'
                                            , 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 Counties ACS5.xlsx'), sheet_name = 'Counties')
            df_pop = df_pop[['County Name', 'Year','Race_Ethnicity', 'Population']]
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
            df_census = df_census.merge(df_pop, on = ['County Name', 'Year', 'Race_Ethnicity'], how = 'left')
            # df_census = df_census.fillna(0)
            # df_census = df_census.dropna()

    if geography == 'MSA':
        df_census = df_census.replace('-666666666', np.nan)
        df_census = df_census.replace('null', np.nan)
        df_census = df_census.dropna(axis = 1, how = 'all')
    
        
        df_census = df_census.rename(columns = {'metropolitan statistical area/micropolitan statistical area':'MSA_ID'})
        df_msa_map = df_census[df_census['Year'] == 2022][['NAME', 'MSA_ID']].drop_duplicates().rename(columns = {'NAME':'MSA'})
        df_census = df_census.merge(df_msa_map, on = 'MSA_ID', how = 'left')
        df_census = pd.melt(df_census
                          , id_vars = ['NAME', 'MSA', 'MSA_ID', 'Year']
                          , var_name = 'ID'
                          , value_name = 'Total'
                         )
    
        df_census['Total'] = df_census['Total'].apply(pd.to_numeric)
        df_census = df_census.merge(df_vars[['ID', 'Label_clean', 'Variable', 'Race_Ethnicity', 'Sort']], on = 'ID', how = 'left')
        df_census = df_census[['ID', 'MSA_ID', 'MSA', 'Year', 'Label_clean', 'Variable', 'Race_Ethnicity', 'Sort', 'Total']]

        if indicator_name in ['Income_1', 'Income_3']:
            df_cpi = pd.read_excel(os.path.join(path_git, 'config', 'CPI Inflation Adjustment Factors.xlsx'), sheet_name = 'BLS_West')
            df_cpi = df_cpi[['Year', 'IAF_' + str(year_end)]]

            df_census = df_census.merge(df_cpi, on = 'Year', how = 'left')
            df_census['Total'] = round(df_census['Total']*df_census['IAF_' + str(year_end)])
            df_census = df_census.drop(['IAF_' + str(year_end)], axis = 1)

        # Some indicators require the roll up to be weighted by population
        # The following step aligns the Race/Ethnicity mappings with the population counts workbook
        if indicator_name in ['Income_3', 'Labor_2']:
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community'
                                            , 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 MSA ACS5.xlsx'), sheet_name = 'MSA')
            df_pop = df_pop[['MSA', 'Year','Race_Ethnicity', 'Population']]
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
            df_census = df_census.merge(df_pop, on = ['MSA', 'Year', 'Race_Ethnicity'], how = 'left')
            df_census = df_census.dropna()


    return df_census

def acs_processing_2(df_census, margin_of_error):

    '''
    User defined function to clean/process ACS margin of error fields and sort the data
    '''
        
    if margin_of_error == 'Yes':
        df_census_me = df_census.copy()
        
        if geography == 'Tracts':
            df_me = df_census_me[df_census_me['Variable'].isna()]
            df_census_me = df_census_me.dropna()
            df_me = df_me[['Table ID', 'Tract ID', 'County Name', 'Year', 'Total']].rename(columns = {'Total':'ME'})
            df_me['Table ID'] = df_me['Table ID'].apply(lambda s : re.sub("M", "E", s))
            df_census_me = df_census_me.merge(df_me, on = ['Table ID', 'Tract ID', 'County Name', 'Year'], how = 'left')
            df_census_me['Year'] = df_census_me['Year'].astype(str)
            df_census = df_census_me.copy()
        
        if geography == 'Counties':
            df_me = df_census_me[df_census_me['Variable'].isna()]
            df_census_me = df_census_me.dropna()
            df_me = df_me[['Table ID', 'County Name', 'Year', 'Total']].rename(columns = {'Total':'ME'})
            df_me['Table ID'] = df_me['Table ID'].apply(lambda s : re.sub("M", "E", s))
            df_census_me = df_census_me.merge(df_me, on = ['Table ID', 'County Name', 'Year'], how = 'left')
            df_census_me['Year'] = df_census_me['Year'].astype(str)
            df_census = df_census_me.copy()

        if geography == 'MSA':
            df_me = df_census_me[df_census_me['Variable'].isna()]
            df_census_me = df_census_me.dropna()
            df_me = df_me[['ID', 'MSA', 'Year', 'Total']].rename(columns = {'Total':'ME'})
            df_me['ID'] = df_me['ID'].apply(lambda s : re.sub("M", "E", s))
            df_census_me = df_census_me.merge(df_me, on = ['ID', 'MSA', 'Year'], how = 'left')
            df_census_me = df_census_me[['ID', 'MSA', 'Year', 'Label_clean', 'Variable', 'Race_Ethnicity', 'Sort', 'Total', 'ME']]
            df_census = df_census_me.copy()

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
    if geography == 'Tracts':
        df_census = df_census.sort_values(by = ['NAME'       , 'Year', 'Race_Ethnicity_sort', 'Sort'], ascending = [True, False, True, True])
    if geography == 'Counties':
        df_census = df_census.sort_values(by = ['County Name', 'Year', 'Race_Ethnicity_sort', 'Sort'], ascending = [True, False, True, True])
    if geography == 'MSA':
        df_census = df_census.sort_values(by = ['MSA'        , 'Year', 'Race_Ethnicity_sort', 'Sort'], ascending = [True, False, True, True])
    df_census = df_census.drop(['Race_Ethnicity_sort', 'Sort'], axis = 1)
    
    return df_census


def acs_processing_3(df_census, indicator_name, geography, percentages, margin_of_error, MOE_thresh, df_fips=None):

    '''
    User defined function to clean/process ACS data for rolling up geography/variable mappings 
    for population/household counts and standard errors and calculates percentages based on
    geography/variable mappings
    '''
        
    if geography == 'Tracts':
        # Merge MPO groupings
        # reorder columns
        # fill missing values (represent a population of 0)
        # Roll up metrics to variable mappings and MPO
        
        df_mpo = df_fips[['County Name', 'MPO']]
        df_census = df_census.merge(df_mpo, on = ['County Name'], how = 'left')
        if margin_of_error == 'Yes':
            if indicator_name in ['Income_3', 'Labor_2']:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'Tract ID', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Population', 'Total', 'ME']
            else:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'Tract ID', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME']
        else:
            if indicator_name in ['Income_3', 'Labor_2']:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'Tract ID', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Population', 'Total']
            else:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'Tract ID', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total']
                
        df_census = df_census[cols]
        df_census['Total'] = df_census['Total'].fillna(0)
        
        # Fill missings with 0, then 1 to make sure nothing gets removed if population is 0
        # create weighted average lambda function
        # roll up to different geographies using population weighted average

        if margin_of_error == 'Yes':
            if indicator_name in ['Income_3', 'Labor_2']:
                # Income_3 and Labor_2 need to be a weighted average by population
                df_census['Population'] = df_census['Population'].fillna(0)
                df_census['Population'] = df_census['Population'].replace(0, 1)
                wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
                df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan

                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm), ME = ('ME', sqrtsumsq))
                df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
                conditions = [
                    (df_census1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_census1['ME_ratio'] <= MOE_thresh
                    , df_census1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_census1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

            else:
                # All other indicators
                df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan
                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
                df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
                conditions = [
                    (df_census1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_census1['ME_ratio'] <= MOE_thresh
                    , df_census1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_census1['Use for Reporting'] = np.select(conditions, choices, default = 'No')


        if margin_of_error == 'No':
            if indicator_name in ['Income_3', 'Labor_2']:
                # Income_3 and Labor_2 need to be a weighted average by population
                df_census['Population'] = df_census['Population'].fillna(0)
                df_census['Population'] = df_census['Population'].replace(0, 1)
                wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm))
                df_census1 = df_census1.sort_values(['MPO', 'NAME', 'Year'], ascending = [True, True, False])
            
            else:
                # All other indicators
                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME', 'Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Total = ('Total', 'sum'))


            df_census1 = df_census1.sort_values(['MPO', 'NAME', 'Year'], ascending = [True, True, False])

    
        # Reshape data to wide format
        df_census2 = df_census1.pivot_table(index = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Tract ID', 'NAME', 'Year', 'Race_Ethnicity']
                                            , columns = 'Variable'
                                            , values = 'Total').reset_index()
        df_census2 = df_census2.sort_values(['MPO', 'County FIPS', 'Year'], ascending = [True, True, False])
    
        # Replace infinite values with NaN
        df_census1 = df_census1.replace([np.inf, -np.inf, 0], np.nan)
        
        # missing values represent a population of 0
        df_census2 = df_census2.fillna(0)
    
        
        ## Check if we want to calculate proportions
        if percentages == 'Yes':
    
            if num_vars == 1:
                df_census1['Percentage'] = 100*df_census1['Total'] / df_census1[df_census1['Race_Ethnicity'] != 'All'].groupby(['NAME', 'Year'])['Total'].transform('sum')
            if num_vars > 1:
                df_census1['Percentage'] = 100*df_census1['Total'] / df_census1.groupby(['NAME', 'Year', 'Race_Ethnicity'])['Total'].transform('sum')
    
            # Reshape data to wide format
            df_census2_pct = df_census1.copy()
            df_census2_pct['Variable'] = df_census2_pct['Variable'].astype(str) + '_pct'
            df_census2_pct = df_census2_pct.pivot_table(index = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Tract ID', 'NAME', 'Year', 'Race_Ethnicity']
                                                        , columns = 'Variable'
                                                        , values = 'Percentage').reset_index()
            df_census2_pct = df_census2_pct.sort_values(['MPO', 'County FIPS', 'Year'], ascending = [True, True, False])
            
            # missing values represent a population of 0
            df_census2_pct = df_census2_pct.fillna(0)

            # merge percentages back onto wide formatted data
            df_census2 = df_census2.merge(df_census2_pct
                                          , on = ['State FIPS', 'MPO', 'County FIPS',  'County Name', 'Tract ID', 'NAME', 'Year', 'Race_Ethnicity']
                                          , how = 'left')
            

        # # Calculate Five-Number Summaries
        # df_census1_summaries = df_census1[df_census1['Race_Ethnicity'] == 'All'].groupby(['County Name', 'Variable', 'Year'], as_index = False)['Total']\
        #                                                                 .describe()\
        #                                                                 .rename(columns = {'25%':'Q1', '50%':'median', '75%':'Q3'})
        # # Set workbook name
        # name_output_summaries_xlsx = [indicator_name, ' MPO ', estimate, ' Summaries.xlsx']
        # name_output_summaries_xlsx = "".join(name_output_summaries_xlsx)
        
        # # Set file path for exporting
        # path_out_xlsx = os.path.join(path_main, report_theme, sp_folder_out, indicator_name + ' ' + folder)
        # # df_census1_summaries.to_excel(os.path.join(path_out_xlsx, name_output_summaries_xlsx), index = False)


    if geography == 'Counties':
        # Merge MPO groupings
        # reorder columns
        # fill missing values (represent a population of 0)
        # Roll up metrics to variable mappings and MPO
        
        df_mpo = df_fips[['County Name', 'MPO']]
        df_census = df_census.merge(df_mpo, on = ['County Name'], how = 'left')
        if margin_of_error == 'Yes':
            if indicator_name in ['Income_3', 'Labor_2']:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Population', 'Total', 'ME']
            else:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME']
        else:
            if indicator_name in ['Income_3', 'Labor_2']:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Population', 'Total']
            else:
                cols = ['Table ID', 'State FIPS', 'MPO', 'County Name', 'County FIPS', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total']
                
        df_census = df_census[cols]
        df_census['Total'] = df_census['Total'].fillna(0)
        
        # Fill missings with 0, then 1 to make sure nothing gets removed if population is 0
        # create weighted average lambda function
        # roll up to different geographies using population weighted average

        if margin_of_error == 'Yes':
            if indicator_name in ['Income_3', 'Labor_2']:
                # Income_3 and Labor_2 need to be a weighted average by population
                df_census['Population'] = df_census['Population'].fillna(0)
                df_census['Population'] = df_census['Population'].replace(0, 1)
                wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
                df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan

                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm), ME = ('ME', sqrtsumsq))
                df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
                conditions = [
                    (df_census1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_census1['ME_ratio'] <= MOE_thresh
                    , df_census1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_census1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

                df_mpo1    = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm), ME = ('ME', sqrtsumsq))
                df_mpo1['ME_ratio'] = df_mpo1['ME']/df_mpo1['Total']*100
                conditions = [
                    (df_mpo1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_mpo1['ME_ratio'] <= MOE_thresh
                    , df_mpo1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_mpo1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

            else:
                # All other indicators
                df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan
                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
                df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
                conditions = [
                    (df_census1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_census1['ME_ratio'] <= MOE_thresh
                    , df_census1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_census1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

                df_mpo1 = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable']
                                             , as_index = False, sort = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
                df_mpo1['ME_ratio'] = df_mpo1['ME']/df_mpo1['Total']*100
                conditions = [
                    (df_mpo1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_mpo1['ME_ratio'] <= MOE_thresh
                    , df_mpo1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_mpo1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

        if margin_of_error == 'No':
            if indicator_name in ['Income_3', 'Labor_2']:
                # Income_3 and Labor_2 need to be a weighted average by population
                df_census['Population'] = df_census['Population'].fillna(0)
                df_census['Population'] = df_census['Population'].replace(0, 1)
                wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm))
                df_mpo1    = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm))
                df_census1 = df_census1.sort_values(['MPO', 'NAME', 'Year'], ascending = [True, True, False])
                df_mpo1    = df_mpo1   .sort_values(['MPO',         'Year'], ascending = [True,       False])
            
            else:
                # All other indicators
                df_census1 = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Total = ('Total', 'sum'))
                df_mpo1    = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable']
                                                , as_index = False, sort = False).agg(Total = ('Total', 'sum'))


            df_census1 = df_census1.sort_values(['MPO', 'NAME', 'Year'], ascending = [True, True, False])
            df_mpo1    = df_mpo1   .sort_values(['MPO',         'Year'], ascending = [True,       False])

    
        # Reshape data to wide format
        df_census2 = df_census1.pivot_table(index = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME', 'Year', 'Race_Ethnicity']
                                            , columns = 'Variable'
                                            , values = 'Total').reset_index()
        df_mpo2    = df_mpo1   .pivot_table(index = ['State FIPS', 'MPO', 'Year', 'Race_Ethnicity']
                                            , columns = 'Variable'
                                            , values = 'Total').reset_index()
        df_census2 = df_census2.sort_values(['MPO', 'County FIPS', 'Year'], ascending = [True, True, False])
        df_mpo2    = df_mpo2   .sort_values(['MPO',                'Year'], ascending = [True,       False])
    
        # Replace infinite values with NaN
        df_census1 = df_census1.replace([np.inf, -np.inf, 0], np.nan)
        df_mpo1    = df_mpo1   .replace([np.inf, -np.inf, 0], np.nan)
        
        # missing values represent a population of 0
        df_census2 = df_census2.fillna(0)
        df_mpo2    = df_mpo2   .fillna(0)
    
        
        ## Check if we want to calculate proportions
        if percentages == 'Yes':
    
            if num_vars == 1:
                df_census1['Percentage'] = 100*df_census1['Total'] / df_census1[df_census1['Race_Ethnicity'] != 'All'].groupby(['NAME', 'Year'])['Total'].transform('sum')
                df_mpo1   ['Percentage'] = 100*df_mpo1   ['Total'] / df_mpo1   [df_mpo1   ['Race_Ethnicity'] != 'All'].groupby(['MPO' , 'Year'])['Total'].transform('sum')
            if num_vars > 1:
                df_census1['Percentage'] = 100*df_census1['Total'] / df_census1.groupby(['NAME', 'Year', 'Race_Ethnicity'])['Total'].transform('sum')
                df_mpo1   ['Percentage'] = 100*df_mpo1   ['Total'] / df_mpo1   .groupby(['MPO' , 'Year', 'Race_Ethnicity'])['Total'].transform('sum')
    
            # Reshape data to wide format
            df_census2_pct = df_census1.copy()
            df_census2_pct['Variable'] = df_census2_pct['Variable'].astype(str) + '_pct'
            df_census2_pct = df_census2_pct.pivot_table(index = ['State FIPS', 'MPO', 'County FIPS',  'County Name', 'NAME', 'Year', 'Race_Ethnicity']
                                                        , columns = 'Variable'
                                                        , values = 'Percentage').reset_index()
            df_census2_pct = df_census2_pct.sort_values(['MPO', 'County FIPS', 'Year'], ascending = [True, True, False])
            
            df_mpo2_pct = df_mpo1.copy()
            df_mpo2_pct['Variable'] = df_mpo2_pct['Variable'].astype(str) + '_pct'
            df_mpo2_pct = df_mpo2_pct.pivot_table(index = ['State FIPS', 'MPO', 'Year', 'Race_Ethnicity']
                                                  , columns = 'Variable'
                                                  , values = 'Percentage').reset_index()
            df_mpo2_pct = df_mpo2_pct.sort_values(['MPO', 'Year'], ascending = [True, False])
            
            # missing values represent a population of 0
            df_census2_pct = df_census2_pct.fillna(0)
            df_mpo2_pct    = df_mpo2_pct   .fillna(0)

            # merge percentages back onto wide formatted data
            df_census2 = df_census2.merge(df_census2_pct
                                          , on = ['State FIPS', 'MPO', 'County FIPS',  'County Name', 'NAME', 'Year', 'Race_Ethnicity']
                                          , how = 'left')
            df_mpo2    = df_mpo2   .merge(df_mpo2_pct
                                          , on = ['State FIPS', 'MPO', 'Year', 'Race_Ethnicity']
                                          , how = 'left')
    
    
    if geography == 'MSA':
        
        # Groupings roll up
        if margin_of_error == 'Yes':
            df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan
            df_census1 = df_census.groupby(['MSA', 'Year', 'Race_Ethnicity', 'Variable']
                                            , as_index = False, sort = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
            df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
            conditions = [
                (df_census1['ME_ratio']  > MOE_thresh) | (df_census1['ME_ratio'] == '') | (df_census1['ME_ratio'].isna())
                , df_census1['ME_ratio'] <= MOE_thresh
            ]
            choices = ['No', 'Yes']
            df_census1['Use for Reporting'] = np.select(conditions, choices)
        if margin_of_error == 'No':
            df_census1 = df_census.groupby(['MSA', 'Year', 'Race_Ethnicity', 'Variable']
                                            , as_index = False, sort = False).agg(Total = ('Total', 'sum'))        
            df_census1 = df_census1.sort_values(['MSA', 'Year'], ascending = [True, False])
    
        # Reshape data to wide format
        df_census2 = df_census1.pivot_table(index = ['MSA', 'Year', 'Race_Ethnicity']
                                            , columns = 'Variable'
                                            , values = 'Total').reset_index()
        df_census2 = df_census2.sort_values(['MSA', 'Year'], ascending = [True, False])
    
        # Replace infinite values with NaN
        df_census1 = df_census1.replace([np.inf, -np.inf, 0], np.nan)
        
        # missing values represent a population of 0
        df_census2 = df_census2.fillna(0)
    
        ## Check if we want to calculate proportions
        if percentages == 'Yes':
    
            # Estimate proportions by groupings
            if num_vars == 1:
                df_census1['Percentage'] = 100*df_census1['Total'] / df_census1[df_census1['Race_Ethnicity'] != 'All'].groupby(['MSA', 'Year'])['Total'].transform('sum')
            if num_vars > 1:
                df_census1['Percentage'] = 100*df_census1['Total'] / df_census1.groupby(['MSA', 'Year', 'Race_Ethnicity'])['Total'].transform('sum')
                
            # Reshape data to wide format
            df_census2_pct = df_census1.copy()
            df_census2_pct['Variable'] = df_census2_pct['Variable'].astype(str) + '_pct'
            df_census2_pct = df_census2_pct.pivot_table(index = ['MSA', 'Year', 'Race_Ethnicity']
                                                        , columns = 'Variable'
                                                        , values = 'Percentage').reset_index()
            df_census2_pct = df_census2_pct.sort_values(['MSA', 'Year'], ascending = [True, False])

            # missing values represent a population of 0
            df_census2_pct = df_census2_pct.fillna(0)

            # merge percentages back onto wide formatted data
            df_census2 = df_census2.merge(df_census2_pct
                                          , on = ['MSA', 'Year', 'Race_Ethnicity']
                                          , how = 'left')

    if geography == 'Counties':
        return df_census1, df_census2, df_mpo1, df_mpo2
    else:
        return df_census1, df_census2
    

group_puma     = ['State FIPS', 'MPO', 'PUMA'       , 'PUMA NAME'  ]
group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
group_msa      = ['State FIPS',        'MSA_ID'     , 'MSA'        ]
group_mpo      = ['State FIPS', 'MPO'                              ]


def rename_census(
        indicator_name, geography, margin_of_error, groups=None,
        df_tracts1=None, df_counties1=None, df_mpo1=None, df_msa1=None, df_puma=None, df_counties=None, df_msa=None, df_mpo=None
        ):
    group_puma     = ['State FIPS', 'MPO', 'PUMA'       , 'PUMA NAME'  ]
    group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
    group_msa      = ['State FIPS',        'MSA_ID'     , 'MSA'        ]
    group_mpo      = ['State FIPS', 'MPO'                              ]
    if margin_of_error == 'Yes':
        if geography == 'Tracts':
            if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
                df_tracts1 = df_tracts1[group_counties + ['Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
            else:
                df_tracts1 = df_tracts1[group_counties + ['Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_tracts1 = df_tracts1.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
        if geography == 'Counties':
            if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
                df_counties1 = df_counties1[group_counties + ['NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
                df_mpo1      = df_mpo1     [group_mpo      + [        'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
            else:
                df_counties1 = df_counties1[group_counties + ['NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
                df_mpo1      = df_mpo1     [group_mpo      + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_counties1 = df_counties1.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_mpo1      = df_mpo1     .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
        if geography == 'MSA':
            if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
                df_msa1 = df_msa1[['MSA', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
            else:
                df_msa1 = df_msa1[['MSA', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_msa1 = df_msa1.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
        if geography == 'PUMA':
            if indicator_name not in ['Cost_6', 'Accessibility_2']:
                groups.reverse()
            if indicator_name == 'Accessibility_4':
                groups = ['RAC1P', 'Income Bracket', 'Travel Time']
            df_puma     = df_puma    [group_puma     + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_counties = df_counties[group_counties + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_msa      = df_msa     [group_msa      + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_puma     = df_puma    .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_counties = df_counties.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_msa      = df_msa     .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_mpo      = df_mpo     .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})

    if margin_of_error == 'No':
        if geography == 'Tracts':
            if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
                df_tracts1 = df_tracts1[group_counties + ['Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total']]
            else:
                df_tracts1 = df_tracts1[group_counties + ['Tract ID', 'NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]
        if geography == 'Counties':
            if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
                df_counties1 = df_counties1[group_counties + ['NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total']]
                df_mpo1      = df_mpo1     [group_mpo      + [        'Year', 'Race_Ethnicity', 'Variable', 'Total']]
            else:
                df_counties1 = df_counties1[group_counties + ['NAME', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]
                df_mpo1      = df_mpo1     [group_mpo      + [        'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]
                
        if geography == 'MSA':
            if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
                df_msa1 = df_msa1[['MSA', 'Year', 'Race_Ethnicity', 'Variable', 'Total']]
            else:
                df_msa1 = df_msa1[['MSA', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]
        if geography == 'PUMA':
            groups.reverse()
            df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total', 'Percentage']]
            df_counties = df_counties[group_counties + ['Year'] + groups + ['Total', 'Percentage']]
            df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total', 'Percentage']]
            df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups + ['Total', 'Percentage']]

    if geography == 'PUMA':
        if table_type == 'P':
            df_puma     = df_puma    .rename(columns = {'Total':'Population'})
            df_counties = df_counties.rename(columns = {'Total':'Population'})
            df_msa      = df_msa     .rename(columns = {'Total':'Population'})
            df_mpo      = df_mpo     .rename(columns = {'Total':'Population'})
        if table_type == 'H':
            df_puma     = df_puma    .rename(columns = {'Total':'Households'})
            df_counties = df_counties.rename(columns = {'Total':'Households'})
            df_msa      = df_msa     .rename(columns = {'Total':'Households'})
            df_mpo      = df_mpo     .rename(columns = {'Total':'Households'})
        df_puma     = df_puma    .sort_values(group_puma     + ['Year'] + groups, ascending = [True, True, True, True, False] + [item in groups for item in groups])
        df_counties = df_counties.sort_values(group_counties + ['Year'] + groups, ascending = [True, True, True, True, False] + [item in groups for item in groups])
        df_msa      = df_msa     .sort_values(group_msa      + ['Year'] + groups, ascending = [True, True, True,       False] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + ['Year'] + groups, ascending = [True, True,             False] + [item in groups for item in groups])


    ## Renaming specifically by indicators
    if indicator_name in ['Income_3']:
        if geography == 'Counties':
            df_mpo_wm = df_mpo1[df_mpo1['Race_Ethnicity'] == 'All'].reset_index(drop = True)
        
            df_counties1 = df_counties1.merge(df_mpo_wm[['Year', 'Total']].rename(columns = {'Total':'Regional Median Household Income'}), on = ['Year'], how = 'left')
            df_mpo1      = df_mpo1     .merge(df_mpo_wm[['Year', 'Total']].rename(columns = {'Total':'Regional Median Household Income'}), on = ['Year'], how = 'left')
        
            df_counties1['Percent of Regional Median Household Income'] = 100*(df_counties1['Total']/df_counties1['Regional Median Household Income'])
            df_mpo1     ['Percent of Regional Median Household Income'] = 100*(df_mpo1     ['Total']/df_mpo1     ['Regional Median Household Income'])
        
            df_counties1 = df_counties1.rename(columns = {'Total':'Median Household Income'})
            df_mpo1      = df_mpo1     .rename(columns = {'Total':'Median Household Income'})

    if indicator_name == 'Income_1':
        if geography == 'Tracts':
            df_tracts1 = df_tracts1.rename(columns = {'Total':'Regional Median Income'})
        if geography == 'Counties':
            df_counties1 = df_counties1.rename(columns = {'Total':'Regional Median Income'})
            df_mpo1    = df_mpo1   .rename(columns = {'Total':'Regional Median Income'})
        if geography == 'MSA':
            df_msa1 = df_msa1.rename(columns = {'Total':'Regional Median Income'})

    if indicator_name in ['Cost_5', 'Income_2', 'Broadband_2']:
        if geography == 'Tracts':
            df_tracts1 = df_tracts1.rename(columns = {'Total':'Households'})
        if geography == 'Counties':
            df_counties1 = df_counties1.rename(columns = {'Total':'Households'})
            df_mpo1      = df_mpo1     .rename(columns = {'Total':'Households'})
        if geography == 'MSA':
            df_msa1 = df_msa1.rename(columns = {'Total':'Households'})
            
    if indicator_name in ['Cost_3']:
        if geography == 'Tracts':
            df_tracts1 = df_tracts1.rename(columns = {'Total':'Housing Units'})
        if geography == 'Counties':
            df_counties1 = df_counties1.rename(columns = {'Total':'Housing Units'})
            df_mpo1      = df_mpo1     .rename(columns = {'Total':'Housing Units'})
        if geography == 'MSA':
            df_msa1 = df_msa1.rename(columns = {'Total':'Housing Units'})

    if indicator_name in ['Pop_3', 'Pop_4', 'Edu_1', 'Labor_1', 'Health_2', 'Income_4', 'Commute_1']:
        if geography == 'Tracts':
            df_tracts1 = df_tracts1.rename(columns = {'Total':'Population'})
        if geography == 'Counties':
            df_counties1 = df_counties1.rename(columns = {'Total':'Population'})
            df_mpo1      = df_mpo1     .rename(columns = {'Total':'Population'})
        if geography == 'MSA':
            df_msa1 = df_msa1.rename(columns = {'Total':'Population'})

    if indicator_name in ['Income_2', 'Accessibility_2', 'Accessibility_4']:
        if indicator_name == 'Accessibility_4':
            factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
            df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
            df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
            df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
            df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)
            
            factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
            df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
            df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
            df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
            df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)

            factor_times = ['No commute (worked from home)', '0 to 15 minutes', '15 to 30 minutes', 'More than 30 minutes']
            df_puma    ['Travel_sort'] = pd.Categorical(df_puma    ['Travel Time'], factor_times)
            df_counties['Travel_sort'] = pd.Categorical(df_counties['Travel Time'], factor_times)
            df_msa     ['Travel_sort'] = pd.Categorical(df_msa     ['Travel Time'], factor_times)
            df_mpo     ['Travel_sort'] = pd.Categorical(df_mpo     ['Travel Time'], factor_times)

            df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, True, True, False, True, True, True])
            df_counties = df_counties.sort_values(by = group_counties + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, True, True, False, True, True, True])
            df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, True, False, True, True, True])
            df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, False, True, True, True])

            df_puma     = df_puma    .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
            df_counties = df_counties.drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
            df_msa      = df_msa     .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
            df_mpo      = df_mpo     .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
                
        if indicator_name == 'Accessibility_2':
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

            df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, True, True, False, True, True])
            df_counties = df_counties.sort_values(by = group_counties + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, True, True, False, True, True])
            df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, True, False, True, True])
            df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, False, True, True])

            df_puma     = df_puma    .drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
            df_counties = df_counties.drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
            df_msa      = df_msa     .drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
            df_mpo      = df_mpo     .drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
            
        if indicator_name == 'Income_2':
            factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
            df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
            df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
            df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
            df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)
            
            df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'Income_sort'], ascending = [True, True, True, True, False, True])
            df_counties = df_counties.sort_values(by = group_counties + ['Year', 'Income_sort'], ascending = [True, True, True, True, False, True])
            df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'Income_sort'], ascending = [True, True, True, False, True])
            df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'Income_sort'], ascending = [True, True, False, True])

            df_puma     = df_puma    .drop(['Income_sort'], axis = 1)
            df_counties = df_counties.drop(['Income_sort'], axis = 1)
            df_msa      = df_msa     .drop(['Income_sort'], axis = 1)
            df_mpo      = df_mpo     .drop(['Income_sort'], axis = 1)

    if geography == 'Tracts':
        return df_tracts1
    if geography == 'Counties':
        return df_counties1, df_mpo1
    if geography == 'MSA':
        return df_msa1
    if geography == 'PUMA':
        return df_puma, df_counties, df_msa, df_mpo



def acs_processing_1(df_census, df_vars, indicator_name, geography, year_end, path_main, path_git):

    '''
    User defined function to clean/process ACS data immediately after query
    Replaces weird missing values with np.nan
    Drops rows with all missing
    Melts data from wide to long
    Merges clean variable mapping, race/ethnicity label, and sorting assignment
    Removes unneeded columns
    Adjusts dollars for inflation as needed
    '''

    print('')
    print('Processing 1...')

    if geography == 'Places':
        geo_ID = ['state', 'place', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['state', 'County Name', 'county', 'tract', 'block group', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['state', 'County Name', 'county', 'tract', 'NAME']
    if geography == 'Counties':
        geo_ID = ['state', 'County Name', 'county', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'NAME']
        df_census = df_census.rename(columns = {'metropolitan statistical area/micropolitan statistical area':'MSA_ID'})

    df_census = df_census.replace('-666666666', np.nan)
    df_census = df_census.replace('-555555555', np.nan)
    df_census = df_census.replace('-999999999.0', np.nan)
    df_census = df_census.replace('null', np.nan)
    df_census = df_census.dropna(axis = 1, how = 'all')
    
    df_census = pd.melt(df_census
                        , id_vars = geo_ID + ['Year']
                        , var_name = 'ID'
                        , value_name = 'Total'
                        )
    df_census = df_census.dropna()
    
    df_census['Total'] = df_census['Total'].apply(pd.to_numeric)
    df_census = df_census.merge(df_vars[['ID', 'Label_clean', 'Variable', 'Race_Ethnicity', 'Sort']], on = 'ID', how = 'left')
    df_census = df_census[['ID'] + geo_ID + ['Year', 'Variable', 'Race_Ethnicity', 'Sort', 'Total']]

    if indicator_name in ['Income_1', 'Income_3']:
        df_cpi = pd.read_excel(os.path.join(path_git, 'config', 'CPI Inflation Adjustment Factors.xlsx'), sheet_name = 'BLS_West')
        df_cpi = df_cpi[['Year', 'IAF_' + str(year_end)]]

        df_census = df_census.merge(df_cpi, on = 'Year', how = 'left')
        df_census['Total'] = round(df_census['Total']*df_census['IAF_' + str(year_end)])
        df_census = df_census.drop(['IAF_' + str(year_end)], axis = 1)

    # Some indicators require the roll up to be weighted by population
    # The following step aligns the Race/Ethnicity mappings with the population counts workbook
    if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
        if geography == 'Places':
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community', 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 Places ACS5.xlsx'      ), sheet_name = 'Places'      )
        if geography == 'Block Groups':
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community', 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 Block Groups ACS5.xlsx'), sheet_name = 'Block Groups')
        if geography == 'Tracts':
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community', 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 Tracts ACS5.xlsx'      ), sheet_name = 'Tracts'      )
        if geography == 'Counties':
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community', 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 Counties ACS5.xlsx'    ), sheet_name = 'Counties'    )
        if geography == 'MSA':
            df_pop = pd.read_excel(os.path.join(path_main, 'Vibrant and Inclusive Places', 'People and Community', 'Pop and Demographics', 'Pop_3 Race', 'Pop_3 MSA ACS5.xlsx'         ), sheet_name = 'MSA'         )

        df_pop = df_pop[['NAME', 'Year','Race_Ethnicity', 'Population']]
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
        df_census = df_census.merge(df_pop, on = ['NAME', 'Year', 'Race_Ethnicity'], how = 'left')
        # df_census = df_census.fillna(0)
        if indicator_name == 'Income_3':
            df_census = df_census.dropna()      


    if geography == 'Places':
        df_census = df_census.rename(columns = {
            'ID':'Estimate ID'
            , 'state':'State FIPS'
            , 'place':'Place ID'
        })
    if geography == 'Block Groups':
        df_census = df_census.rename(columns = {
            'ID':'Estimate ID'
            , 'state':'State FIPS'
            , 'county':'County FIPS'
            , 'tract':'Tract ID'
            , 'block group':'Block Group ID'
        })
    if geography == 'Tracts':
        df_census = df_census.rename(columns = {
            'ID':'Estimate ID'
            , 'state':'State FIPS'
            , 'county':'County FIPS'
            , 'tract':'Tract ID'
        })
    if geography == 'Counties':
        df_census = df_census.rename(columns = {
            'ID':'Estimate ID'
            , 'state':'State FIPS'
            , 'county':'County FIPS'
        })
    if geography == 'MSA':
        df_census = df_census.rename(columns = {
            'ID':'Estimate ID'
            , 'NAME':'MSA'
        })
    

    print('')

    return df_census


def acs_processing_2(df_census, geography, margin_of_error):

    '''
    User defined function to clean/process ACS margin of error fields and sort the data
    '''

    print('')
    print('Processing 2...')

    if geography == 'Places':
        geo_ID = ['State FIPS', 'Place ID', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
    if geography == 'Counties':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'MSA']
        
    if margin_of_error == 'Yes':
        df_census_me = df_census.copy()

        df_me = df_census_me[df_census_me['Variable'].isna()]
        df_census_me = df_census_me.dropna()
        df_me = df_me[['Estimate ID'] + geo_ID + ['Year', 'Total']].rename(columns = {'Total':'ME'})
        df_me['Estimate ID'] = df_me['Estimate ID'].apply(lambda s : re.sub("M", "E", s))
        df_census_me = df_census_me.merge(df_me, on = ['Estimate ID'] + geo_ID + ['Year'], how = 'left')
        df_census_me['Year'] = df_census_me['Year'].astype(str)
        df_census = df_census_me.copy()

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
    
    df_census = df_census.sort_values(by = geo_ID + ['Year', 'Race_Ethnicity_sort', 'Sort'], ascending = [item in geo_ID for item in geo_ID] + [False, True, True])
    df_census = df_census.drop(['Race_Ethnicity_sort', 'Sort'], axis = 1)
    
    print('')
    
    return df_census


def acs_processing_3(df_census, indicator_name, geography, percentages, margin_of_error, MOE_thresh, num_vars, df_fips=None):

    '''
    User defined function to clean/process ACS data for rolling up geography/variable mappings 
    for population/household counts and standard errors and calculates percentages based on
    geography/variable mappings
    '''

    print('')
    print('Processing 3...')

    if geography == 'Places':
        geo_ID = ['State FIPS', 'Place ID', 'NAME']
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
    if geography == 'Counties':
        geo_ID = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME']
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'MSA']


    if geography == 'Counties':
        df_mpo = df_fips[['County Name', 'MPO']]
        df_census = df_census.merge(df_mpo, on = ['County Name'], how = 'left')

    # reorder columns
    # fill missing values (represent a population of 0)
    # Roll up metrics to variable mappings (and MPO if Counties)
        
    if margin_of_error == 'Yes':
        if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
            cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Population', 'Total', 'ME']
        else:
            cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME']
    else:
        if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
            cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Population', 'Total']
        else:
            cols = geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total']
            
    df_census = df_census[cols]
    df_census['Total'] = df_census['Total'].fillna(0)
    
    # Fill missings with 0, then 1 to make sure nothing gets removed if population is 0
    # create weighted average lambda function
    # roll up to different geographies using population weighted average

    if margin_of_error == 'Yes':
        if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
            # Income_3 and Labor_2 need to be a weighted average by population
            df_census['Population'] = df_census['Population'].fillna(0)
            df_census['Population'] = df_census['Population'].replace(0, 1)
            wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
            df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan

            df_census1 = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm), ME = ('ME', sqrtsumsq))
            df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
            conditions = [
                (df_census1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                , df_census1['ME_ratio'] <= MOE_thresh
                , df_census1['ME_ratio']  > MOE_thresh
            ]
            choices = ['Yes', 'Yes', 'No']
            df_census1['Use for Reporting'] = np.select(conditions, choices, default = 'No')
            if geography == 'Counties':
                df_mpo1    = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm), ME = ('ME', sqrtsumsq))
                df_mpo1['ME_ratio'] = df_mpo1['ME']/df_mpo1['Total']*100
                conditions = [
                    (df_mpo1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_mpo1['ME_ratio'] <= MOE_thresh
                    , df_mpo1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_mpo1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

        else:
            # All other indicators
            df_census.loc[df_census['ME'] < 0, 'ME'] = np.nan
            df_census1 = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
            df_census1['ME_ratio'] = df_census1['ME']/df_census1['Total']*100
            conditions = [
                (df_census1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                , df_census1['ME_ratio'] <= MOE_thresh
                , df_census1['ME_ratio']  > MOE_thresh
            ]
            choices = ['Yes', 'Yes', 'No']
            df_census1['Use for Reporting'] = np.select(conditions, choices, default = 'No')
            if geography == 'Counties':
                df_mpo1 = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
                df_mpo1['ME_ratio'] = df_mpo1['ME']/df_mpo1['Total']*100
                conditions = [
                    (df_mpo1['Race_Ethnicity'] == 'All') & (len(df_census['Race_Ethnicity'].unique()) > 1)
                    , df_mpo1['ME_ratio'] <= MOE_thresh
                    , df_mpo1['ME_ratio']  > MOE_thresh
                ]
                choices = ['Yes', 'Yes', 'No']
                df_mpo1['Use for Reporting'] = np.select(conditions, choices, default = 'No')

    if margin_of_error == 'No':
        if indicator_name in ['Income_1', 'Income_3', 'Labor_2']:
            # Income_3 and Labor_2 need to be a weighted average by population
            df_census['Population'] = df_census['Population'].fillna(0)
            df_census['Population'] = df_census['Population'].replace(0, 1)
            wm         = lambda x: np.average(x, weights = df_census.loc[x.index, "Population"]) # weighted average
            df_census1 = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm))
            df_census1 = df_census1.sort_values(geo_ID + ['Year'], ascending = [item in geo_ID for item in geo_ID] + [False])
            if geography == 'Counties':
                df_mpo1 = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Population = ('Population', 'sum'), Total = ('Total', wm))
        
        else:
            # All other indicators
            df_census1 = df_census.groupby(geo_ID + ['Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Total = ('Total', 'sum'))
            if geography == 'Counties':
                df_mpo1 = df_census.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable'], as_index = False, sort = False).agg(Total = ('Total', 'sum'))


        df_census1 = df_census1.sort_values(geo_ID + ['Year'], ascending = [item in geo_ID for item in geo_ID] + [False])
        if geography == 'Counties':
            df_mpo1 = df_mpo1.sort_values(['MPO', 'Year'], ascending = [True, False])


    # Reshape data to wide format
    df_census2 = df_census1.pivot_table(index = geo_ID + ['Year', 'Race_Ethnicity']
                                        , columns = 'Variable'
                                        , values = 'Total').reset_index()
    df_census2 = df_census2.sort_values(geo_ID + ['Year'], ascending = [item in geo_ID for item in geo_ID] + [False])

    if geography == 'Counties':
        df_mpo2 = df_mpo1.pivot_table(index = ['State FIPS', 'MPO', 'Year', 'Race_Ethnicity']
                                            , columns = 'Variable'
                                            , values = 'Total').reset_index()
        df_mpo2 = df_mpo2.sort_values(['MPO', 'Year'], ascending = [True, False])

    # Replace infinite values with NaN
    df_census1 = df_census1.replace([np.inf, -np.inf, 0], np.nan)
    
    # missing values represent a population of 0
    df_census2 = df_census2.fillna(0)

    
    ## Check if we want to calculate proportions
    if percentages == 'Yes':

        if num_vars == 1:
            df_census1['Percentage'] = 100*df_census1['Total'] / df_census1[df_census1['Race_Ethnicity'] != 'All'].groupby(['NAME', 'Year'])['Total'].transform('sum')
            if geography == 'Counties':
                df_mpo1['Percentage'] = 100*df_mpo1['Total'] / df_mpo1[df_mpo1['Race_Ethnicity'] != 'All'].groupby(['State FIPS', 'MPO', 'Year'])['Total'].transform('sum')

        if num_vars > 1:
            df_census1['Percentage'] = 100*df_census1['Total'] / df_census1.groupby(geo_ID + ['Year', 'Race_Ethnicity'])['Total'].transform('sum')
            if geography == 'Counties':
                df_mpo1['Percentage'] = 100*df_mpo1['Total'] / df_mpo1.groupby(['State FIPS', 'MPO', 'Year', 'Race_Ethnicity'])['Total'].transform('sum')

        # Reshape data to wide format
        df_census2_pct = df_census1.copy()
        df_census2_pct['Variable'] = df_census2_pct['Variable'].astype(str) + '_pct'
        df_census2_pct = df_census2_pct.pivot_table(index = geo_ID + ['Year', 'Race_Ethnicity']
                                                    , columns = 'Variable'
                                                    , values = 'Percentage').reset_index()
        df_census2_pct = df_census2_pct.sort_values(geo_ID + ['Year'], ascending = [item in geo_ID for item in geo_ID] + [False])

        if geography == 'Counties':
            df_mpo2_pct = df_mpo1.copy()
            df_mpo2_pct['Variable'] = df_mpo2_pct['Variable'].astype(str) + '_pct'
            df_mpo2_pct = df_mpo2_pct.pivot_table(index = ['State FIPS', 'MPO', 'Year', 'Race_Ethnicity']
                                                    , columns = 'Variable'
                                                    , values = 'Percentage').reset_index()
            df_mpo2_pct = df_mpo2_pct.sort_values(['MPO', 'Year'], ascending = [True, False])

        
        # missing values represent a population of 0
        # merge percentages back onto wide formatted data
        df_census2_pct = df_census2_pct.fillna(0)
        df_census2 = df_census2.merge(df_census2_pct
                                        , on = geo_ID + ['Year', 'Race_Ethnicity']
                                        , how = 'left')
        if geography == 'Counties':
            df_census2_pct = df_census2_pct.fillna(0)
            df_mpo2 = df_mpo2.merge(df_mpo2_pct
                                        , on = ['State FIPS','MPO', 'Year', 'Race_Ethnicity']
                                        , how = 'left')
        

    # # Calculate Five-Number Summaries
    # df_census1_summaries = df_census1[df_census1['Race_Ethnicity'] == 'All'].groupby(['County Name', 'Variable', 'Year'], as_index = False)['Total']\
    #                                                                 .describe()\
    #                                                                 .rename(columns = {'25%':'Q1', '50%':'median', '75%':'Q3'})
    # # Set workbook name
    # name_output_summaries_xlsx = [indicator_name, ' MPO ', estimate, ' Summaries.xlsx']
    # name_output_summaries_xlsx = "".join(name_output_summaries_xlsx)
    
    # # Set file path for exporting
    # path_out_xlsx = os.path.join(path_main, report_theme, sp_folder_out, indicator_name + ' ' + folder)
    # # df_census1_summaries.to_excel(os.path.join(path_out_xlsx, name_output_summaries_xlsx), index = False)

            


    print('')




    if geography == 'Counties':
        return df_census1, df_census2, df_mpo1, df_mpo2
    else:
        return df_census1, df_census2




def pums_processing_1(df_census, df_vars, sample_type, weight):

    print('')
    print('Processing 1...')

    groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
    groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

    if sample_type == 'PUMS':
        df_census['PUMA'] = df_census['PUMA'].astype(str).apply('{:0>5}'.format)
        df_census[weight] = df_census[weight].astype(int)

    if sample_type == 'FOODSEC':
        df_census['Household_ID'] = df_census['HRHHID'].map(str) + '-' + df_census['HRHHID2'].map(str)
        df_census = df_census.drop(['HRHHID', 'HRHHID2'], axis = 1)
        df_census['Householder'] = df_census.groupby(['Household_ID', 'Year'], as_index = False)['PERRP'].transform(min)
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
                                        , columns = 'ID2'
                                        , values = 'Description2'
                                        , aggfunc = lambda x: x).reset_index()
    cols = ['Year', 'Value1'] + groups2
    df_vars2 = df_vars2[cols]

    list_values = []
    for group in groups2:
        list_values = list_values + list(df_census[group].values)
    set_values = set(list_values)

    df_vars2 = df_vars2[df_vars2['Value1'].isin(set_values)]
    df_vars2 = df_vars2.add_suffix('_desc').rename(columns = {'Value1_desc':'Value1', 'Year_desc':'Year'})

    for col in cols[2:]:
        df_census = df_census.merge(df_vars2[['Value1', col+'_desc', 'Year']], left_on = [col, 'Year'], right_on = ['Value1', 'Year'], how = 'inner')
        df_census[col] = df_census[col+'_desc']
        df_census = df_census.drop(['Value1', col+'_desc'], axis = 1)

    return df_census, groups


def pums_processing_2(df_census, groups, indicator_name, dict_fips, path_config0, path_git):
    
    print('')
    print('Processing 2...')

    df_census = df_census.dropna()
    df_census = df_census.rename(columns = {'state':'State FIPS', 'county':'County FIPS'})

    if sample_type == 'PUMS':
        df_fips_pums = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                                        , sheet_name = 'PUMAcodes'
                                        , dtype = {'STATEFP': object, 'COUNTYFP': object, 'TRACTCE': object, 'PUMA5CE': object})
        df_fips_pums = df_fips_pums[df_fips_pums['STATEFP'].isin(list(dict_fips.keys()))]
        df_fips_pums = df_fips_pums[['STATEFP', 'PUMA5CE', 'PUMA NAME', 'COUNTYFP', 'Years']].rename(columns = {'PUMA5CE':'PUMA', 'STATEFP':'State FIPS', 'COUNTYFP':'County FIPS'}).drop_duplicates()

        df_census1 = df_census[df_census['Year'].isin(sequence(2012, 2021, 1))]
        df_census2 = df_census[df_census['Year'].isin(sequence(2022, 2031, 1))]

        df_census1 = df_census1.merge(df_fips_pums[df_fips_pums['Years'] == '2012-2021'], on = ['State FIPS', 'PUMA'], how = 'left')
        df_census2 = df_census2.merge(df_fips_pums[df_fips_pums['Years'] == '2022-2031'], on = ['State FIPS', 'PUMA'], how = 'left')
        df_census = pd.concat([df_census1, df_census2])
        df_census = df_census.drop('Years', axis = 1)

        df_census['County FIPS'] = df_census['County FIPS'].astype(str).apply('{:0>3}'.format)
        df_census = df_census.merge(df_fips[['State FIPS', 'MPO', 'County FIPS', 'County Name', 'MSA_ID', 'MSA_acs']].drop_duplicates()
                                            , on = ['State FIPS', 'County FIPS'])
        df_census = df_census.rename(columns = {'MSA_acs':'MSA'})
        df_census = df_census.set_index(['State FIPS', 'MPO', 'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'Year']).reset_index()
        df_census = df_census.sort_values(['State FIPS', 'PUMA', 'Year'] + groups, ascending = [True, True, False] + [item in groups for item in groups])
    
    if sample_type == 'FOODSEC':
        df_census = df_census.sort_values(['State FIPS', 'MPO', 'County FIPS', 'Year'] + groups, ascending = [True, True, True, False] + [item in groups for item in groups])

    
    if 'HISP' in groups:
        df_census.loc[df_census['HISP'] == 'Hispanic or Latino', 'RAC1P'] = 'Hispanic or Latino'
        df_census = df_census.drop('HISP', axis = 1)
        groups.remove('HISP')

    if 'HHLDRHISP' in groups:
        df_census.loc[df_census['HHLDRHISP'] == 'Hispanic or Latino', 'HHLDRRAC1P'] = 'Hispanic or Latino'
        df_census = df_census.drop('HHLDRHISP', axis = 1)
        groups.remove('HHLDRHISP')

    if 'PEHSPNON' in groups:
        df_census.loc[df_census['PEHSPNON'] == 'Hispanic or Latino', 'PTDTRACE'] = 'Hispanic or Latino'
        df_census = df_census.drop('PEHSPNON', axis = 1)
        groups.remove('PEHSPNON')

    if indicator_name == 'Cost_6':
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
        df_census = df_census.drop(['GRPIP', 'OCPIP'], axis = 1)
        groups = list(map(lambda x: x.replace('GRPIP', 'housing_type'  ), groups))
        groups = list(map(lambda x: x.replace('OCPIP', 'housing_burden'), groups))

    if indicator_name in ['Income_2', 'Accessibility_2', 'Accessibility_4']:
        df_cpi = pd.read_excel(os.path.join(path_config0, 'CPI Inflation Adjustment Factors.xlsx'), sheet_name = 'BLS_West')
        df_cpi = df_cpi[['Year', 'IAF_2023']]

        df_census = df_census.merge(df_cpi, on = 'Year', how = 'left')
        cols = ['HINCP', 'ADJINC']
        df_census[cols] = df_census[cols].astype('float32')
        df_census['HINCP'] = df_census['HINCP']*df_census['ADJINC']*df_census['IAF_2023']
        df_census = df_census.drop(['IAF_2023', 'ADJINC'], axis = 1)

        df_income_brackets = pd.read_excel(os.path.join(path_config0, 'CA State Income Brackets by Household Size.xlsx'), sheet_name = 'Table')
        df_income_brackets['County'].fillna(method='ffill', inplace = True)
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
                                                             , columns = 'Income Bracket'
                                                             , values = 'Income Threshold').reset_index().rename(columns = {'County':'County Name'})
        df_income_brackets['NP'] = df_income_brackets['NP'].astype(str)
        df_census = df_census.merge(df_income_brackets, on = ['County Name', 'NP'], how = 'left')
        df_census.loc[ df_census['HINCP'] <= df_census['Low Income']                                                        , 'Income Bracket'] = 'Low Income'
        df_census.loc[(df_census['HINCP']  > df_census['Low Income']) & (df_census['HINCP'] <= df_census['Moderate Income']), 'Income Bracket'] = 'Moderate Income'
        df_census.loc[ df_census['HINCP']  > df_census['Moderate Income']                                                   , 'Income Bracket'] = 'High Income'
        df_census.loc[ df_census['NP'] == 0                                                                                 , 'Income Bracket'] = 'No data available'
        df_census = df_census.drop(['HINCP', 'NP'], axis = 1)
        groups = ['Income Bracket'] + groups[:-1]
        if indicator_name == 'Accessibility_4':
            df_census = df_census[df_census['JWTRNS'] != 'N/A, not a civillian in the labor force']
            df_census['JWMNP'] = df_census['JWMNP'].astype('float32')
            df_census.loc[(df_census['JWMNP'] ==  0)                             , 'Travel Time'] = 'No commute (worked from home)'
            df_census.loc[(df_census['JWMNP']  >  0) & (df_census['JWMNP'] <= 15), 'Travel Time'] = '0 to 15 minutes'
            df_census.loc[(df_census['JWMNP']  > 15) & (df_census['JWMNP'] <= 30), 'Travel Time'] = '15 to 30 minutes'
            df_census.loc[(df_census['JWMNP']  > 30)                             , 'Travel Time'] = 'More than 30 minutes'
            groups = groups + ['Travel Time']
            df_census = df_census.drop('JWTRNS', axis = 1)
            groups.remove('JWTRNS')

    return df_census, groups


def pums_processing_3(df_census, indicator_name, weight, margin_of_error, MOE_thresh, percentages, groups):

    print('')
    print('Processing 3...')

    df_puma     = df_census.drop([                            'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'SERIALNO'], axis = 1)
    df_counties = df_census.drop([       'PUMA', 'PUMA NAME', 'MSA_ID', 'MSA',                               'SERIALNO'], axis = 1)
    df_msa      = df_census.drop(['MPO', 'PUMA', 'PUMA NAME',                  'County FIPS', 'County Name', 'SERIALNO'], axis = 1)
    df_mpo      = df_census.drop([       'PUMA', 'PUMA NAME', 'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'SERIALNO'], axis = 1)
    
    df_puma     = df_puma    .set_index(group_puma    ).reset_index()
    df_counties = df_counties.set_index(group_counties).reset_index()
    df_msa      = df_msa     .set_index(group_msa     ).reset_index()
    df_mpo      = df_mpo     .set_index(group_mpo     ).reset_index()

    if margin_of_error == 'Yes':
        df_puma    .loc[df_puma    ['ME'] < 0, 'ME'] = np.nan
        df_counties.loc[df_counties['ME'] < 0, 'ME'] = np.nan
        df_msa     .loc[df_msa     ['ME'] < 0, 'ME'] = np.nan
        df_mpo     .loc[df_mpo     ['ME'] < 0, 'ME'] = np.nan
        
        if indicator_name in ['Income_2', 'Accessibility_2', 'Accessibility_4']:
            if indicator_name == 'Accessibility_4':
                df_puma1     = df_puma    .groupby(group_puma     + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_counties1 = df_counties.groupby(group_counties + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_msa1      = df_msa     .groupby(group_msa      + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_mpo1      = df_mpo     .groupby(group_mpo      + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_puma2     = df_puma    .groupby(group_puma     + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_counties2 = df_counties.groupby(group_counties + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_msa2      = df_msa     .groupby(group_msa      + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_mpo2      = df_mpo     .groupby(group_mpo      + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_puma2    .loc[:, 'RAC1P'] = 'All'
                df_counties2.loc[:, 'RAC1P'] = 'All'
                df_msa2     .loc[:, 'RAC1P'] = 'All'
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_puma     = pd.concat([df_puma1    , df_puma2    ])
                df_counties = pd.concat([df_counties1, df_counties2])
                df_msa      = pd.concat([df_msa1     , df_msa2     ])
                df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])
                
            if indicator_name == 'Accessibility_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            
            if indicator_name == 'Income_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))

        elif indicator_name == 'Cost_6':
            df_puma1 = df_puma.groupby(list(df_puma.drop([weight, 'ME'         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_puma2 = df_puma.groupby(list(df_puma.drop([weight, 'ME', 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_puma2.loc[:, 'RAC1P'] = 'All'
            df_puma2 = pd.concat([df_puma1, df_puma2])
            df_puma3 = df_puma2[df_puma2['housing_type'].isin(['Owner', 'Renter'])]
            df_puma3 = df_puma3.groupby(list(df_puma3.drop(['Total', 'ME', 'housing_type'], axis = 1).columns), as_index = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
            df_puma3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_puma = pd.concat([df_puma2, df_puma3])

            df_counties1 = df_counties.groupby(list(df_counties.drop([weight, 'ME'         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_counties2 = df_counties.groupby(list(df_counties.drop([weight, 'ME', 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_counties2.loc[:, 'RAC1P'] = 'All'
            df_counties2 = pd.concat([df_counties1, df_counties2])
            df_counties3 = df_counties2[df_counties2['housing_type'].isin(['Owner', 'Renter'])]
            df_counties3 = df_counties3.groupby(list(df_counties3.drop(['Total', 'ME', 'housing_type'], axis = 1).columns), as_index = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
            df_counties3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_counties = pd.concat([df_counties2, df_counties3])

            df_msa1 = df_msa.groupby(list(df_msa.drop([weight, 'ME'         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_msa2 = df_msa.groupby(list(df_msa.drop([weight, 'ME', 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_msa2.loc[:, 'RAC1P'] = 'All'
            df_msa2 = pd.concat([df_msa1, df_msa2])
            df_msa3 = df_msa2[df_msa2['housing_type'].isin(['Owner', 'Renter'])]
            df_msa3 = df_msa3.groupby(list(df_msa3.drop(['Total', 'ME', 'housing_type'], axis = 1).columns), as_index = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
            df_msa3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_msa = pd.concat([df_msa2, df_msa3])

            df_mpo1 = df_mpo.groupby(list(df_mpo.drop([weight, 'ME'         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_mpo2 = df_mpo.groupby(list(df_mpo.drop([weight, 'ME', 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_mpo2.loc[:, 'RAC1P'] = 'All'
            df_mpo2 = pd.concat([df_mpo1, df_mpo2])
            df_mpo3 = df_mpo2[df_mpo2['housing_type'].isin(['Owner', 'Renter'])]
            df_mpo3 = df_mpo3.groupby(list(df_mpo3.drop(['Total', 'ME', 'housing_type'], axis = 1).columns), as_index = False).agg(Total = ('Total', 'sum'), ME = ('ME', sqrtsumsq))
            df_mpo3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_mpo = pd.concat([df_mpo2, df_mpo3])

            df_puma    ['ME_ratio'] = df_puma    ['ME']/df_puma    ['Total']*100
            df_counties['ME_ratio'] = df_counties['ME']/df_counties['Total']*100
            df_msa     ['ME_ratio'] = df_msa     ['ME']/df_msa     ['Total']*100
            df_mpo     ['ME_ratio'] = df_mpo     ['ME']/df_mpo     ['Total']*100
        
        else:
            df_puma     = df_puma    .groupby(list(df_puma    .drop([weight, 'ME'], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_counties = df_counties.groupby(list(df_counties.drop([weight, 'ME'], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_msa      = df_msa     .groupby(list(df_msa     .drop([weight, 'ME'], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
            df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight, 'ME'], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'), ME = ('ME', sqrtsumsq))
        
        df_puma    ['ME_ratio'] = df_puma    ['ME']/df_puma    ['Total']*100
        df_counties['ME_ratio'] = df_counties['ME']/df_counties['Total']*100
        df_msa     ['ME_ratio'] = df_msa     ['ME']/df_msa     ['Total']*100
        df_mpo     ['ME_ratio'] = df_mpo     ['ME']/df_mpo     ['Total']*100
        
        conditions = [df_puma['ME_ratio'] <= MOE_thresh, df_puma['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_puma['Use for Reporting'] = np.select(conditions, choices, default = 'No')
        
        conditions = [df_counties['ME_ratio'] <= MOE_thresh, df_counties['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_counties['Use for Reporting'] = np.select(conditions, choices, default = 'No')
        
        conditions = [df_msa['ME_ratio'] <= MOE_thresh, df_msa['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_msa['Use for Reporting'] = np.select(conditions, choices, default = 'No')
        
        conditions = [df_mpo['ME_ratio'] <= MOE_thresh, df_mpo['ME_ratio']  > MOE_thresh]
        choices = ['Yes', 'No']
        df_mpo['Use for Reporting'] = np.select(conditions, choices, default = 'No')
    
    if margin_of_error == 'No':
        if indicator_name in ['Income_2', 'Accessibility_2', 'Accessibility_4']:
            if indicator_name == 'Accessibility_4':
                df_puma1     = df_puma    .groupby(group_puma     + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_counties1 = df_counties.groupby(group_counties + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_msa1      = df_msa     .groupby(group_msa      + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_mpo1      = df_mpo     .groupby(group_mpo      + ['Year', 'RAC1P', 'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_puma2     = df_puma    .groupby(group_puma     + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_counties2 = df_counties.groupby(group_counties + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_msa2      = df_msa     .groupby(group_msa      + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_mpo2      = df_mpo     .groupby(group_mpo      + ['Year',          'Income Bracket', 'Travel Time'], as_index = False).agg(Total = (weight, 'sum'))
                df_puma2    .loc[:, 'RAC1P'] = 'All'
                df_counties2.loc[:, 'RAC1P'] = 'All'
                df_msa2     .loc[:, 'RAC1P'] = 'All'
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_puma     = pd.concat([df_puma1    , df_puma2    ])
                df_counties = pd.concat([df_counties1, df_counties2])
                df_msa      = pd.concat([df_msa1     , df_msa2     ])
                df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])
            if indicator_name == 'Accessibility_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket', 'JWTRNS'], as_index = False).agg(Total = (weight, 'sum'))
            
            if indicator_name == 'Income_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket'], as_index = False).agg(Total = (weight, 'sum'))
                
        if indicator_name == 'Cost_6':
            df_puma1 = df_puma.groupby(list(df_puma.drop([weight         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_puma2 = df_puma.groupby(list(df_puma.drop([weight, 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_puma2.loc[:, 'RAC1P'] = 'All'
            df_puma2 = pd.concat([df_puma1, df_puma2])
            df_puma3 = df_puma2[df_puma2['housing_type'].isin(['Owner', 'Renter'])]
            df_puma3 = df_puma3.groupby(list(df_puma3.drop(['Total'], axis = 1).columns), as_index = False).agg(Total = ('Total', 'sum'))
            df_puma3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_puma3['Percentage'] = 100*df_puma3['Total']/df_puma3.groupby(list(df_puma3.drop(['housing_burden', 'Total'], axis = 1).columns))['Total'].transform('sum')
            df_puma = pd.concat([df_puma2, df_puma3])

            df_counties1 = df_counties.groupby(list(df_counties.drop([weight         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_counties2 = df_counties.groupby(list(df_counties.drop([weight, 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_counties2.loc[:, 'RAC1P'] = 'All'
            df_counties2 = pd.concat([df_counties1, df_counties2])
            df_counties3 = df_counties2[df_counties2['housing_type'].isin(['Owner', 'Renter'])]
            df_counties3 = df_counties3.groupby(list(df_counties3.drop(['Total'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_counties3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_counties = pd.concat([df_counties2, df_counties3])

            df_msa1 = df_msa.groupby(list(df_msa.drop([weight         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_msa2 = df_msa.groupby(list(df_msa.drop([weight, 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_msa2.loc[:, 'RAC1P'] = 'All'
            df_msa2 = pd.concat([df_msa1, df_msa2])
            df_msa3 = df_msa2[df_msa2['housing_type'].isin(['Owner', 'Renter'])]
            df_msa3 = df_msa3.groupby(list(df_msa3.drop(['Total'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_msa3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_msa = pd.concat([df_msa2, df_msa3])
            
            df_mpo1 = df_mpo.groupby(list(df_mpo.drop([weight         ], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_mpo2 = df_mpo.groupby(list(df_mpo.drop([weight, 'RAC1P'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_mpo2.loc[:, 'RAC1P'] = 'All'
            df_mpo2 = pd.concat([df_mpo1, df_mpo2])
            df_mpo3 = df_mpo2[df_mpo2['housing_type'].isin(['Owner', 'Renter'])]
            df_mpo3 = df_mpo3.groupby(list(df_mpo3.drop(['Total'], axis = 1).columns), as_index = False).agg(Total = (weight, 'sum'))
            df_mpo3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_mpo = pd.concat([df_mpo2, df_mpo3])

        else:
            df_puma     = df_puma    .groupby(list(df_puma    .drop([weight], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'))
            df_counties = df_counties.groupby(list(df_counties.drop([weight], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'))
            df_msa      = df_msa     .groupby(list(df_msa     .drop([weight], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'))
            df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'))
    
    if percentages == 'Yes':
        if margin_of_error == 'Yes':
            if len(groups) > 1:
                df_puma    ['Percentage'] = 100*df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups[-1:] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = 100*df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups[-1:] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = 100*df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups[-1:] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
                df_mpo     ['Percentage'] = 100*df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups[-1:] + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
            if len(groups) == 1:
                df_puma    ['Percentage'] = 100*df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = 100*df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = 100*df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
                df_mpo     ['Percentage'] = 100*df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups      + ['Total', 'ME', 'ME_ratio', 'Use for Reporting'], axis = 1).columns))['Total'].transform('sum')
        if margin_of_error == 'No':
            if len(groups) > 1:
                df_puma    ['Percentage'] = 100*df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups[-1:] + ['Total'], axis = 1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = 100*df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups[-1:] + ['Total'], axis = 1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = 100*df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups[-1:] + ['Total'], axis = 1).columns))['Total'].transform('sum')
                df_mpo     ['Percentage'] = 100*df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups[-1:] + ['Total'], axis = 1).columns))['Total'].transform('sum')
            if len(groups) == 1:
                df_puma    ['Percentage'] = 100*df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups      + ['Total'], axis = 1).columns))['Total'].transform('sum')
                df_counties['Percentage'] = 100*df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups      + ['Total'], axis = 1).columns))['Total'].transform('sum')
                df_msa     ['Percentage'] = 100*df_msa     ['Total'] / df_msa     .groupby(list(df_mpo     .drop(groups      + ['Total'], axis = 1).columns))['Total'].transform('sum')                
                df_mpo     ['Percentage'] = 100*df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups      + ['Total'], axis = 1).columns))['Total'].transform('sum')

    return df_puma, df_counties, df_msa, df_mpo




def food_processing_3(df_census, weight, percentages, groups):

    print('')
    print('Processing 3...')

    if 'PTDTRACE' in groups:
        groups.remove('PTDTRACE')
        groups_to_drop = groups.copy()
        groups = ['PTDTRACE'] + groups

    df_counties = df_census.drop([                              'Household_ID', 'Householder', 'PERRP'], axis = 1)
    df_mpo      = df_census.drop(['County FIPS', 'County Name', 'Household_ID', 'Householder', 'PERRP'], axis = 1)

    group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
    group_mpo      = ['State FIPS', 'MPO'                              ]

    df_counties = df_counties.set_index(group_counties).reset_index()
    df_mpo      = df_mpo     .set_index(group_mpo     ).reset_index()

    df_counties = df_counties.drop('Year', axis = 1)
    df_mpo      = df_mpo     .drop('Year', axis = 1)

    df_counties[weight] = 1
    df_mpo     [weight] = 1

    df_counties = df_counties.groupby(list(df_counties.drop([weight], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'))
    df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight], axis = 1).columns), as_index = False, sort = False).agg(Total = (weight, 'sum'))

    if percentages == 'Yes':
        df_counties['Percentage'] = 100*df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups_to_drop + ['Total'], axis = 1).columns))['Total'].transform('sum')
        df_mpo     ['Percentage'] = 100*df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups_to_drop + ['Total'], axis = 1).columns))['Total'].transform('sum')

    df_counties['Total'] = round(df_counties['Total'])
    df_mpo     ['Total'] = round(df_mpo     ['Total'])

    df_counties['Total'] = df_counties['Total'].astype(int)
    df_mpo     ['Total'] = df_mpo     ['Total'].astype(int)

    return df_counties, df_mpo, groups




def rename_census(
        indicator_name, geography, sample_type, margin_of_error, percentages=None, groups=None, table_type=None,
        df_places1=None, df_blocks1=None, df_tracts1=None, df_counties1=None, df_mpo1=None, df_msa1=None, df_puma=None, df_counties=None, df_msa=None, df_mpo=None
        ):
    
    if geography == 'Places':
        geo_ID = ['State FIPS', 'Place ID', 'NAME']
        df_org = df_places1.copy()
    if geography == 'Block Groups':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
        df_org = df_blocks1.copy()
    if geography == 'Tracts':
        geo_ID = ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
        df_org = df_tracts1.copy()
    if geography == 'Counties':
        geo_ID = ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME']
        df_org = df_counties1.copy()
    if geography == 'MSA':
        geo_ID = ['MSA_ID', 'MSA']
        df_org = df_msa1.copy()


    if margin_of_error == 'Yes':
        if sample_type in ['ACS', 'SUBJECT']:
            if percentages == 'No':
                df_org = df_org[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
                if geography == 'Counties':
                    df_mpo1 = df_mpo1[['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'ME', 'ME_ratio', 'Use for Reporting']]
            else:
                df_org = df_org[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
                if geography == 'Counties':
                    df_mpo1 = df_mpo1[['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_org = df_org.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            if geography == 'Counties':
                df_mpo1 = df_mpo1.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})

        if sample_type == 'PUMS':
            if indicator_name not in ['Cost_6', 'Accessibility_2']:
                groups.reverse()
            if indicator_name == 'Accessibility_4':
                groups = ['RAC1P', 'Income Bracket', 'Travel Time']
            df_puma     = df_puma    [group_puma     + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_counties = df_counties[group_counties + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_msa      = df_msa     [group_msa      + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups +  ['Total', 'Percentage', 'ME', 'ME_ratio', 'Use for Reporting']]
            df_puma     = df_puma    .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_counties = df_counties.rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_msa      = df_msa     .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})
            df_mpo      = df_mpo     .rename(columns = {'ME':'Margin of Error', 'ME_ratio':'Margin of Error Ratio'})

    if margin_of_error == 'No':
        if sample_type  in ['ACS', 'SUBJECT']:
            if percentages == 'No':
                df_org = df_org[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total']]
                if geography == 'Counties':
                    df_mpo1 = df_mpo1['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total']
            else:
                df_org = df_org[geo_ID + ['Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']]
                if geography == 'Counties':
                    df_mpo1 = df_mpo1['State FIPS', 'MPO', 'Year', 'Race_Ethnicity', 'Variable', 'Total', 'Percentage']

        if sample_type == 'PUMS':
            groups.reverse()
            df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total', 'Percentage']]
            df_counties = df_counties[group_counties + ['Year'] + groups + ['Total', 'Percentage']]
            df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total', 'Percentage']]
            df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups + ['Total', 'Percentage']]
        if sample_type == 'FOODSEC':
            df_counties = df_counties[group_counties + groups + ['Total', 'Percentage']]
            df_mpo      = df_mpo     [group_mpo      + groups + ['Total', 'Percentage']]

    if geography == 'PUMA':
        if table_type == 'P':
            df_puma     = df_puma    .rename(columns = {'Total':'Population'})
            df_counties = df_counties.rename(columns = {'Total':'Population'})
            df_msa      = df_msa     .rename(columns = {'Total':'Population'})
            df_mpo      = df_mpo     .rename(columns = {'Total':'Population'})
        if table_type == 'H':
            df_puma     = df_puma    .rename(columns = {'Total':'Households'})
            df_counties = df_counties.rename(columns = {'Total':'Households'})
            df_msa      = df_msa     .rename(columns = {'Total':'Households'})
            df_mpo      = df_mpo     .rename(columns = {'Total':'Households'})
        df_puma     = df_puma    .sort_values(group_puma     + ['Year'] + groups, ascending = [True, True, True, True, False] + [item in groups for item in groups])
        df_counties = df_counties.sort_values(group_counties + ['Year'] + groups, ascending = [True, True, True, True, False] + [item in groups for item in groups])
        df_msa      = df_msa     .sort_values(group_msa      + ['Year'] + groups, ascending = [True, True, True,       False] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + ['Year'] + groups, ascending = [True, True,             False] + [item in groups for item in groups])
    if sample_type == 'FOODSEC':
        if table_type == 'P':
            df_counties = df_counties.rename(columns = {'Total':'Population'})
            df_mpo      = df_mpo     .rename(columns = {'Total':'Population'})
        if table_type == 'H':
            df_counties = df_counties.rename(columns = {'Total':'Households'})
            df_mpo      = df_mpo     .rename(columns = {'Total':'Households'})
        df_counties = df_counties.sort_values(group_counties + groups, ascending = [True, True, True, True] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + groups, ascending = [True, True,           ] + [item in groups for item in groups])
        if 'PTDTRACE' in groups:
            df_counties = df_counties.set_index(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'PTDTRACE']).reset_index()
            df_mpo      = df_mpo     .set_index(['State FIPS', 'MPO',                               'PTDTRACE']).reset_index()


    ## Renaming specifically by indicators
    if indicator_name in ['Income_3']:
        df_org = df_org.rename(columns = {'Total':'Median Household Income'})
        if geography == 'Counties':
            df_mpo1 = df_mpo1.rename(columns = {'Total':'Median Household Income'})

    if indicator_name == 'Income_1':
        df_org = df_org.rename(columns = {'Total':'Regional Median Income'})
        if geography == 'Counties':
            df_mpo1 = df_mpo1.rename(columns = {'Total':'Regional Median Income'})

    if indicator_name in ['Cost_5', 'Income_2', 'Broadband_2']:
        df_org = df_org.rename(columns = {'Total':'Households'})
        if geography == 'Counties':
            df_mpo1 = df_mpo1.rename(columns = {'Total':'Households'})
            
    if indicator_name in ['Cost_3']:
        df_org = df_org.rename(columns = {'Total':'Housing Units'})
        if geography == 'Counties':
            df_mpo1 = df_mpo1.rename(columns = {'Total':'Housing Units'})

    if indicator_name in ['Pop_3', 'Pop_4', 'Edu_1', 'Labor_1', 'Health_2', 'Income_4', 'Commute_1']:
        df_org = df_org.rename(columns = {'Total':'Population'})
        if geography == 'Counties':
            df_mpo1 = df_mpo1.rename(columns = {'Total':'Population'})

    if indicator_name == 'Accessibility_1':
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

        df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending = [True, True, True, True, False, True, True])
        df_counties = df_counties.sort_values(by = group_counties + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending = [True, True, True, True, False, True, True])
        df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending = [True, True, True, False, True, True])
        df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending = [True, True, False, True, True])

        df_puma     = df_puma    .drop(['RAC1P_sort', 'JWTRNS_sort'], axis = 1)
        df_counties = df_counties.drop(['RAC1P_sort', 'JWTRNS_sort'], axis = 1)
        df_msa      = df_msa     .drop(['RAC1P_sort', 'JWTRNS_sort'], axis = 1)
        df_mpo      = df_mpo     .drop(['RAC1P_sort', 'JWTRNS_sort'], axis = 1)
            
    if indicator_name == 'Accessibility_2':
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

        df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, True, True, False, True, True])
        df_counties = df_counties.sort_values(by = group_counties + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, True, True, False, True, True])
        df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, True, False, True, True])
        df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending = [True, True, False, True, True])

        df_puma     = df_puma    .drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
        df_counties = df_counties.drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
        df_msa      = df_msa     .drop(['Income_sort', 'JWTRNS_sort'], axis = 1)
        df_mpo      = df_mpo     .drop(['Income_sort', 'JWTRNS_sort'], axis = 1)    

    if indicator_name == 'Accessibility_4':
        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)
        
        factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)

        factor_times = ['No commute (worked from home)', '0 to 15 minutes', '15 to 30 minutes', 'More than 30 minutes']
        df_puma    ['Travel_sort'] = pd.Categorical(df_puma    ['Travel Time'], factor_times)
        df_counties['Travel_sort'] = pd.Categorical(df_counties['Travel Time'], factor_times)
        df_msa     ['Travel_sort'] = pd.Categorical(df_msa     ['Travel Time'], factor_times)
        df_mpo     ['Travel_sort'] = pd.Categorical(df_mpo     ['Travel Time'], factor_times)

        df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, True, True, False, True, True, True])
        df_counties = df_counties.sort_values(by = group_counties + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, True, True, False, True, True, True])
        df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, True, False, True, True, True])
        df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending = [True, True, False, True, True, True])

        df_puma     = df_puma    .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
        df_counties = df_counties.drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
        df_msa      = df_msa     .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
        df_mpo      = df_mpo     .drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis = 1)
        
    if indicator_name == 'Income_2':
        factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)
        
        df_puma     = df_puma    .sort_values(by = group_puma     + ['Year', 'Income_sort'], ascending = [True, True, True, True, False, True])
        df_counties = df_counties.sort_values(by = group_counties + ['Year', 'Income_sort'], ascending = [True, True, True, True, False, True])
        df_msa      = df_msa     .sort_values(by = group_msa      + ['Year', 'Income_sort'], ascending = [True, True, True, False, True])
        df_mpo      = df_mpo     .sort_values(by = group_mpo      + ['Year', 'Income_sort'], ascending = [True, True, False, True])

        df_puma     = df_puma    .drop(['Income_sort'], axis = 1)
        df_counties = df_counties.drop(['Income_sort'], axis = 1)
        df_msa      = df_msa     .drop(['Income_sort'], axis = 1)
        df_mpo      = df_mpo     .drop(['Income_sort'], axis = 1)


    if geography == 'Counties':
        if sample_type in ['ACS', 'SUBJECT']:
            return df_org, df_mpo1
        if sample_type == 'FOODSEC':
            return df_counties, df_mpo
    elif geography == 'PUMA':
        return df_puma, df_counties, df_msa, df_mpo
    else:
        return df_org



# Line plot for data visualization
def plot_lines(
    df
     , loop_vars, by_race, race_ethnicity, variable
     , x, y
     , color, line_dash, markers
     , plot_title, plot_name
     , export
):
    if race_ethnicity != None:
        if by_race:
            df = df[df[race_ethnicity] != 'All']
        else:
            df = df[df[race_ethnicity] == 'All'].drop(race_ethnicity, axis = 1)  

    if loop_vars:
        vars = unique(df[variable].values)
        for var in vars:
            df2 = df[df[variable] == var]
            fig = px.line(df2, x = x, y = y, color = color, line_dash = line_dash, markers = markers)
            fig.update_layout(title = plot_title + ' - ' + str(var))
            if export:
                fig.write_html(os.path.join(path_plots, ''.join([indicator_name + '_', plot_name + '_', var + '_', 'line.html'])))
                
            fig.update_layout(autosize=False, width=1050, height=450)
            
    else:
        fig = px.line(df, x = x, y = y, color = color, line_dash = line_dash, markers = markers)
        fig.update_layout(title = plot_title)
        if export:
            fig.write_html(os.path.join(path_plots, ''.join([indicator_name + '_', plot_name + '_', 'line.html'])))

        fig.update_layout(autosize=False, width=1050, height=450)

    return fig.show()









### BLS FUNCTIONS -----------------------------------------------------------------------------------------------------------------


# Create a function to make all of these counties into a dictionary

def dict_maker(df, geography, sector, survey, data_type):
    """
    Given the file: BLS Configuration File.xlsx under the BLS_MSA sheet, we can create a dictionary of 
    all of the MSA counties we want to test. Provide the sector (industry) that you want to pull, and the function will
    return a dictionary of all the MSA series ids formatted for API usage. We must define the first series ID manually,
    but the rest is automated (probably a better way to do it).
    Formula for SMU, CEU Series ID = Prefix + SA + State + Area + Industry + DType.
    Formula for LAU Series ID = Prefix (LAU) + area/county code + DType
    """

    # Making set of keys and vals for future dict
    # keys = []
    # vals = []

    #LAU = survey
    # area_code = CN2810700000000
    # measure = data_type 03 for instance
    if survey == 'LAU':
        keys = []
        vals = list((df.iloc[:,1]))
        for i in range(len(df)):
            # area_code = str(df.iloc[i,2])
            series_id = str(survey) + str(sector[i]) + str(data_type)
            keys.append(series_id)

        

    if survey in ('SMU', 'CEU'):
        keys = []
        vals = []        
        if geography == 'MSA':
            for i in range(len(df)):

                # Loop through each MSA code
                # Construct the Series ID
                # Add Series ID and MSA label to lists

                area_code = str(df.iloc[i, 0])
                state     = str(df.iloc[i, 3])
                series_id = str(survey) + str(state) + str(area_code) + str(sector) + str(data_type)
                keys.append(series_id)
                val = str(df.iloc[i, 1])
                vals.append(val)
            
        if geography == 'National':

            # Pull National level area code
            # Construct the Series ID
            # Add Series ID and National label to lists

            series_id = str(survey) + str(sector) + str(data_type)
            keys.append(series_id)
            val = str(df.iloc[0, 1])
            vals.append(val)


    # Convert list of keys and values to dictionary
    result = {k: v for k, v in zip(keys, vals)}
    return result
        


# Need to update bls_query() so that it doesn't only do the first 10 years
# Let's update bls_query() so that we can make it so that each series is uniform and has 120 rows for all
def bls_query_update(series_dict, dates, api_key):
    """ 
    This function takes a dictionary of series, and a series of dates in the form dates = (start, year) to return
    a dataframe with information regarding employment in the sector that the user prescribes. Because of BLS's 
    query limit of up to 10 years of data being pulled at a time for each series ID, the function loops over a set of 10 or less.
    Meaning that if you supply it with years 2000-2024, it will loop three times subsetting between 2000-2009, 2010-2019, 2020-2024.
    It can also work in year ranges less than 10, so if you want to just pull say 2020-2024, that is totally viable.  
    """

    url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
    key = '?registrationkey={}'.format(api_key)

    # Specify json as content type to return
    headers = {'Content-type': 'application/json'}

    # Initialize an empty dataframe to store our query results
    list_df = []

    # Queries ten years at once
    year_step = 10

    # Loop through the specified range of years in step intervals
    for year_range_start in range(dates[0], dates[1] + 1, year_step):
        year_range_end = min(year_range_start + year_step - 1, dates[1])
        print('')
        print('Pulling data from ' + str(year_range_start) + ' to ' + str(year_range_end))

        df = pd.DataFrame()

        # Used a print statement for troubleshooting
        # print("Querying data for years {}-{}".format(year_range_start, year_range_end))

        # Submit the request for the current date range
        data = json.dumps({
            "seriesid": list(series_dict.keys()),
            "startyear": year_range_start,
            "endyear": year_range_end
            })
        response = requests.post('{}{}'.format(url, key), headers=headers, data=data).json()


        # Adding a function here to alert and halt when we have exceeded daily limit

        if 'status' in response and response['status'] == 'REQUEST_NOT_PROCESSED':
            print(response['message'][0])
            break

        # Extract data from the response and append it to the dataframe
        if 'Results' in response and 'series' in response['Results']:
            print(response['status'])
            for series_data in tqdm(response['Results']['series']):
                series_id = series_data['seriesID']
                if series_id in series_dict:
                    county_name = series_dict[series_id]
                    county_data = {f"{i['year']}-{i['period'][1:]}-01": float(i['value']) if 'value' in i else None for i in series_data['data']}
                    temp_df = pd.DataFrame(index=pd.to_datetime(list(county_data.keys())))
                    temp_df[county_name] = pd.Series(list(county_data.values()), index=temp_df.index)


                    # Concatenate the dataframe to store all of the different years we're testing
                    df = pd.concat([df, temp_df], axis=1)
            list_df.append(df)

    df_final = pd.concat(list_df)

    return df_final

# Now, it should return a single dataframe for a single subsector.
# Additionally, if a MSA doesn't have data for a specific month, that cell should be empty



# Now let's run the final function
def full_bls(key, df, geography, sector_list, dates, survey, data_type):

    """
    This function combines the dict_maker() and bls_query_update() to make a set of Series IDs for multiple MSAs, sectors, and year range, all
    defined by user. We then return the data in a set of dfs, separated by industry in the sector list. Meaning, df[0] will contain information
    only for the first sector in the sector list. 
    """
    if survey in ('SMU', 'CEU'):
        # Initialize an empty list so we can iterate over multiple dictionaries
        sector_chamber = []

        # Initialize empty list for each dataframe we will end up making
        df_chamber = []

        # Loop over each sector we want to test
        print('')
        print('Creating python dictionary of industry IDs')
        print('')
        # if survey in ('SMU', 'CEU'):
        #     for i in tqdm(sector_list):
        #         sector_chamber.append(dict_maker(df, geography, i, survey, data_type))

        # if survey == 'LAU':
        #     for i in tqdm(len(df)):
        #         sector_chamber.append(dict_maker(df, geography, i, survey, data_type))

        for i in tqdm(sector_list):
                sector_chamber.append(dict_maker(df, geography, i, survey, data_type))
        

        # Now with the sector_holders list containing each set of series we want, we can run our query function iteratively
    
        # Iteratively make each dataframe
        print('')
        print('Pulling data for each industry ID by decade')
        print('')
        for sector_dict in sector_chamber:
            print('')
            print(sector_dict)
            df_chamber.append(bls_query_update(sector_dict, dates, api_key = key))

        return(df_chamber)

    if survey == 'LAU':
        df_chamber = []# leaving it like this in case we want to change the code so that it also gets 
        sector = dict_maker(df, geography, sector_list, survey, data_type)
        print(sector)
        df_chamber.append(bls_query_update(sector, dates, api_key = key))
        return(df_chamber)
        #df = bls_query_update(sector, dates, api_key = key)
