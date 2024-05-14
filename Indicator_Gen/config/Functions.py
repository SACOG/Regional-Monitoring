### Packages ###

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





### GENERAL FUNCTIONS ### 



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


def sequence(r1, r2):
    return [item for item in range(r1, r2+1)]






### ACS FUNCTIONS ###

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



