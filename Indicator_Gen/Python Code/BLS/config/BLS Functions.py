

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





def dict_maker(survey, geography, seasonal, df=None, list_sectors=None, data_type=None, measure_code=None):
    """
    Given the file: BLS Configuration File.xlsx under the BLS_MSA sheet, we can create a dictionary of 
    all of the MSA counties we want to test. Provide the sector (industry) that you want to pull, and the function will
    return a dictionary of all the MSA series ids formatted for API usage. We must define the first series ID manually,
    but the rest is automated (probably a better way to do it).
    Formula for SM, CE Series ID = Prefix + SA + State + Area + Industry + DType.
    Formula for LA Series ID = Prefix + SA + area/county code + DType
    """

    keys = []
    vals = []

    if geography == 'MSA': 
        
        # Loop through each MSA code
        # Construct the Series ID
        # Add Series ID and MSA label to lists
        
        for i in range(len(df)):
            
            area_code = str(df.loc[i, 'area_code'])
    
            if survey in ['LA']:
                series_id = [str(survey) + str(seasonal) + str(area_code)  + str(measure_code)]

            if survey in ['SM', 'CE']:
                state     = str(df.loc[i, 'State FIPS'])
                series_id = list(map(lambda sector: str(survey) + str(seasonal) + str(state) + str(area_code) + str(sector) + str(data_type), list_sectors))
                
            keys.append(str(df.loc[i, 'area_text']))
            vals.append(series_id)
        
    if geography == 'National':

        # Pull National level area code
        # Construct the Series ID
        # Add Series ID and National label to lists

        if survey in ['LA']:
                series_id = str(survey) + str(seasonal) + str(area_code)  + str(measure_code)
        if survey in ['SM', 'CE']:
            series_id = list(map(lambda sector: str(survey) + str(seasonal) + str(sector) + str(data_type), list_sectors))
                
        keys.append('National')
        vals.append(series_id)


    # Convert list of keys and values to dictionary
    result = {k: v for k, v in zip(keys, vals)}
    return result

        


# Need to update bls_query() so that it doesn't only do the first 10 years
# Let's update bls_query() so that we can make it so that each series is uniform and has 120 rows for all
def bls_query_update(api_key, series_dict, dates):
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
    year_step = 20

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
def full_bls(api_key, survey, geography, seasonal, dates, df=None, sector_list=None, data_type=None, measure_code=None):

    """
    This function combines the dict_maker() and bls_query_update() to make a set of Series IDs for multiple MSAs, sectors, and year range, all
    defined by user. We then return the data in a set of dfs, separated by industry in the sector list. Meaning, df[0] will contain information
    only for the first sector in the sector list. 
    """

    sector_chamber = []
    df_chamber = []

    if survey in ['CE']:
        # Initialize an empty list so we can iterate over multiple dictionaries
        # Initialize empty list for each dataframe we will end up making
        # Loop over each sector we want to test

        print('')
        print('Creating python dictionary of industry IDs')
        print('')

        for i in tqdm(sector_list):
            sector_chamber.append(dict_maker(survey=survey, geography=geography, seasonal=seasonal, sector=i, data_type=data_type))
        
        # Now with the sector_holders list containing each set of series we want, we can run our query function iteratively
        # Iteratively make each dataframe

        print('')
        print('Pulling data for each industry ID by decade')
        print('')

        for sector_dict in sector_chamber:
            print('')
            print(sector_dict)
            df_chamber.append(bls_query_update(api_key=api_key, series_dict=sector_dict, dates=dates))
            
            
    if survey in ['SM']:
        # Initialize an empty list so we can iterate over multiple dictionaries
        # Initialize empty list for each dataframe we will end up making
        # Loop over each sector we want to test

        print('')
        print('Creating python dictionary of industry IDs')
        print('')

        for i in tqdm(sector_list):
            sector_chamber.append(dict_maker(survey=survey, geography=geography, seasonal=seasonal, df=df, sector=i, data_type=data_type))

        # Now with the sector_holders list containing each set of series we want, we can run our query function iteratively
        # Iteratively make each dataframe

        print('')
        print('Pulling data for each industry ID by decade')
        print('')

        for sector_dict in sector_chamber:
            print('')
            print(sector_dict)
            df_chamber.append(bls_query_update(api_key=api_key, series_dict=sector_dict, dates=dates))


    if survey in ['LA']:
        # Organize unemployment survey codes into dictionary format
        # Pull data using dictionary of codes
        sector_dict = dict_maker(survey=survey, geography=geography, seasonal=seasonal, df=df, measure_code=measure_code)
        print(sector_dict)
        df_chamber.append(bls_query_update(api_key=api_key, series_dict=sector_dict, dates=dates))


    return df_chamber





