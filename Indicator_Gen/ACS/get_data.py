import requests
import pandas as pd
import json
import time
from tqdm import tqdm
import concurrent.futures
import warnings
import re
import os
import inspect
warnings.filterwarnings('ignore')
import numpy as np
import matplotlib.pyplot as plt
from arcgis.gis import GIS
from arcgis.mapping import WebMap
from acs_race import *
from cred_ext import *
from var_parse import *
from final_df_gen import *



### DATA RETRIEVAL ###

def fetch_data_chunk(variables_chunk, api_key, data_url, state):
    
    """
    This function will take in a URL for variables, a data url, an api key, and a state and break up data being retrieved
    in batches of 50. This is the max batch size of the census api.
    """
    
    params = {
        'get': ','.join(variables_chunk),
        'for': 'county:*',
        'in': f'state:{state}',
        'key': api_key,
    }
    response = requests.get(data_url, params=params)
    
    if response.status_code != 200:
        print(f"API call failed with status code {response.status_code}. Message: {response.text}")
        return None
    
    header, *data = response.json()
    df = pd.DataFrame(data, columns=header)
    df_melted = df.melt(id_vars=['state', 'county'], 
                        value_vars=variables_chunk, 
                        var_name='Variable Name', 
                        value_name='Total')
    return df_melted

### GET CENSUS DATA ###

def get_census_data(df, api_key, data_url, state, data_group=None):
    """
    This function will take in a dataframe of filtered variables and retrieve the census data for those variables. 
    """
    
    if data_group is None:
        data_group = 'Race'
        
    if state is None:
        state = '06'
    
    # Copying the DataFrame so the original isn't modified
    df_copy = df.copy()
    
    variables = df_copy['Variable Name']
    variables_chunks = [variables[i:i+50] for i in range(0, len(variables), 50)]
    
    df_list = []
    for chunk in tqdm(variables_chunks):
        df_chunk = fetch_data_chunk(chunk, api_key, data_url, state)
        if df_chunk is not None and not df_chunk.empty:  # Checking if the DataFrame is empty
            df_list.append(df_chunk)
    
    df_final = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
    
    # Assuming map_county_names is another function you've defined
    df_final = map_county_names(df_final)
    
    year_match = re.search(r'/(\d{4})/', data_url)
    year_str = year_match.group(1) if year_match else 'Year_not_found'
    
    df_final = map_county_names(df_final, state, data_group)  # Assuming this function takes these parameters

    file_name = f"{year_str}_{data_group}_json_variables.csv"
    
    # Return the modified DataFrame
    return df_final
