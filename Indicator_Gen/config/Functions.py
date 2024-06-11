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
wm         = lambda x: np.average(x, weights = df_acs.loc[x.index, "WEIGHTS"]) # weighted average
sqrtsumsq  = lambda x: np.sqrt(np.sum(x**2))                                   # Square root of the sum of squares (to roll up SE's when +/- random variables)



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




### ACS FUNCTIONS -----------------------------------------------------------------------------------------------------------------


# Main function used to query data
def query_acs(api_Key, estimate, sample, geography, variables, year
              , state=None, county=None, msa=None, puma=None
              ):
        
    '''
    User defined function to import Data from ACS
    User inputs: [api_key, estimate, geography variables, year] to tell ACS that we have access with the API key and
                    what type of sample data to pull, which variables we want to import, what year, 
                    and which state and record type (persons or households)
                    - record type is for PUMS data only
                    - only pulls 1 year at a time (geography IDs, like census tracts, change at the start of each decade)
    '''

    # Assert that inputs for estimate and geography are appropriate
    assert estimate  in ['ACS5' , 'ACS1'  , 'DEC'                    ], "Unacceptable estimate input, requires 'ACS5', 'ACS1', or 'DEC' "
    assert sample    in ['ACS'  , 'DEC'   , 'DHC', 'PUMS_h', 'PUMS_p'], "Unacceptable estimate input, requires 'ACS', 'DEC', 'DHS', 'PUMS_h', or 'PUMS_p'"
    assert geography in ['Tract', 'County', 'MSA', 'PUMA'            ], "Unacceptable geography input, requires 'Tract', 'County', 'MSA', or 'PUMA' "


    ## Construct URL

    # Create rootpath and specify dataset type
    host_ = 'https://api.census.gov/data'
    dataset_ = f'/acs/{estimate.lower()}'

    if estimate == 'DEC':
        dataset_ = f'/{estimate.lower()}'

    # Special conditions for "get" statement, depending on type of estimate or geography we are pulling
    if estimate == 'DEC':
        if year in [2000, 2010]:
            g_ = '/sf1?get='
        if year == 2020:
            if sample == 'DHC':
                g_ = '/dhc?get='
            else:
                g_ = '/dp?get='
        
    elif geography == 'PUMA':
        g_ = '/pums?get='
    else:
        g_ = '?get='
    
    # User inputs for user API key, desired variables and years to import
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)

    # Specify which geography to import
    if geography == 'PUMA':
        if sample == 'PUMS_h':
            location_ =  '&for=public%20use%20microdata%20area:' + puma + '&in=state:' + state# + '&RT=H'
        if sample == 'PUMS_p':
            location_ =  '&for=public%20use%20microdata%20area:' + puma + '&in=state:' + state# + '&RT=P'
    if geography == 'County':
        location_ = '&for=county:' + county + '&in=state:' + state
    if geography == 'Tract':
        location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'MSA':
        location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)

    
    ## Concatenate constructed URL
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    

    ## Call data using URL

    # Use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    

    ## Return
    return df_acs






### BLS FUNCTIONS -----------------------------------------------------------------------------------------------------------------


# Create a function to make all of these counties into a dictionary

def dict_maker(df, sector, pre, data_type):
    """
    Given the file: BLS Configuration File.xlsx under the BLS_MSA sheet, we can create a dictionary of 
    all of the MSA counties we want to test. Provide the sector (industry) that you want to pull, and the function will
    return a dictionary of all the MSA series ids formatted for API usage. We must define the first series ID manually,
    but the rest is automated (probably a better way to do it).
    Formula for Series ID = Prefix + SA + State + Area + Industry + DType
    """

    # Making set of keys and vals for future dict
    keys = []

    # Now empty list for values in the future dict
    vals = []

    for i in range(len(df)):

        # Getting each code
        area_code = str(df.iloc[i, 0])
        state     = str(df.iloc[i, 2])

        # Making each SeriesID
        series_id = str(pre) + str(state) + str(area_code) + str(sector) + str(data_type)

        # Adding to the keylist for future dictionary
        keys.append(series_id)

        val = str(df.iloc[i, 1])

        vals.append(val)

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

        # Extract data from the response and append it to the dataframe
        if 'Results' in response and 'series' in response['Results']:
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
def full_bls(sector_list, df, dates, key, pre, data_type):

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
        sector_chamber.append(dict_maker(df, i, pre, data_type))

    # Now with the sector_holders list containing each set of series we want, we can run our query function iteratively
    
    # Iteratively make each dataframe
    print('')
    print('Pulling data for each industry ID by decade')
    print('')
    for sector_dict in sector_chamber:
        print(sector_dict)
        df_chamber.append(bls_query_update(sector_dict, dates, api_key = key))

    return(df_chamber)
