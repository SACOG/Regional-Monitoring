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





### CENSUS FUNCTIONS -----------------------------------------------------------------------------------------------------------------


# Split attributes string
def ME_split(text):
    return ",".join(text.split(',')[0:3:2])


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
    if geography == 'Tracts':
        location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'MSA':
        location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)
    
    
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



# Line plot for data visualization
def plot_lines(
    df
     , loop_vars, by_race, race_ethnicity, variable
     , x, y
     , color, line_dash, markers
     , plot_title, plot_name
     , export
):
    
    if by_race == True:
        df = df[df[race_ethnicity] != 'All']
    else:
        df = df[df[race_ethnicity] == 'All'].drop(race_ethnicity, axis = 1)

    if loop_vars == True:
        vars = unique(df[variable].values)
        for var in vars:
            df2 = df[df[variable] == var]
            fig = px.line(df2, x = x, y = y, color = color, line_dash = line_dash, markers = markers)
            fig.update_layout(title = plot_title + ' - ' + str(var))
            if export == True:
                fig.write_html(os.path.join(path_plots, ''.join([indicator_name + '_', plot_name + '_', var + '_', 'line.html'])))
                
            fig.update_layout(autosize=False, width=1050, height=450)
            
    else:
        fig = px.line(df, x = x, y = y, color = color, line_dash = line_dash, markers = markers)
        fig.update_layout(title = plot_title)
        if export == True:
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
    Formula for Series ID = Prefix + SA + State + Area + Industry + DType
    """

    # Making set of keys and vals for future dict
    keys = []
    vals = []


    if geography == 'MSA':

        for i in range(len(df)):

            # Loop through each MSA code
            # Construct the Series ID
            # Add Series ID and MSA label to lists

            area_code = str(df.iloc[i, 0])
            state     = str(df.iloc[i, 2])
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

        if 'status' in response and response['status'] == 'REQUEST_LIMIT_EXCEEDED':
            print("Daily API Query Limit Reached")
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
    
    # Initialize an empty list so we can iterate over multiple dictionaries
    sector_chamber = []

    # Initialize empty list for each dataframe we will end up making
    df_chamber = []

    # Loop over each sector we want to test
    print('')
    print('Creating python dictionary of industry IDs')
    print('')
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
