import os
import requests
import pandas as pd
import time
from .var_parse import *
from .configs import CENSUS_CONFIG

def save_to_csv(df, df_name, path, folder):

    """
    This function allows a user to save a dataframe to a location while specifying its name, path, and folder if needed. 
    
    example usage:
    df = 'a data frame'
    df_name = 'the desired name for the df'
    path = 'the path in which you would like the df to be saved'
    folder = 'the folder or subfolder you would like the df to be saved in'
    
    save_to_csv(df, df_name, path, folder)    
    """    
    directory_path = os.path.join(path, folder)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    df.to_csv(os.path.join(directory_path, df_name + ".csv"))

def fetch_data(product, start_year=None, end_year=None, should_save_csv=False, path=None):

    """
    This helper function allows a user to define:
    1. A census product (like acs1, acs5, or dec)
    2. A start year
    3. An an end year
    4. Whether or not to save the results to a csv. (defaults to no)
    5. Where to save the csv. 

    If no product or start year is provided, the dictionary 'census config' within the configs file will be used as a default reference. 
    If no end year is provided, the current year will be used as the end year. 

    When this function is run, if a census product is not available for a particular year, a statement will be printed informing you of the product, year, and url for which data was unavailable.

    example usage: 

    product  = 'acs1'
    start_year = 2015
    end_year = 2019
    
    data = fetch_data(product, start_year, end_year)

    expected output: A dataframe containing all the data for the specified product whithin the range of start_year and end_year.

    """

    config = CENSUS_CONFIG[product]
    base_urls = config.get('base_urls', [config.get('base_url')])
    folder = config['folder']
    dataframes_dict = {}

    if start_year is None:
        start_year = config['start_year']
    if end_year is None:
        end_year = pd.Timestamp.now().year
    if path is None:
        path = os.path.join("..", "Data", "Raw Data", "ACS", "All JSON Variables")

    # This loop iterates through each year in the range
    for year in range(start_year, end_year + 1):

        # If the product is 'dec' and the year isn't divisible by 10, continue to the next iteration
        if product == 'dec' and year % 10 != 0:
            continue

        for base_url in base_urls:
            url = base_url.format(year)
            response = requests.get(url)
            
            if response.status_code == 200:
                df = variable_parser(url)
                df['Census Product'] = folder
                endpoint = url.split('/')[-2]
                df_name = f"all_{year}_{folder.lower()}_{endpoint}_vars"
                dataframes_dict[df_name] = df
                
                if should_save_csv:
                    save_to_csv(df, df_name, path, folder)
            else:
                print(f"No {folder} data available for {year} at {url}.")
                time.sleep(2)  # To avoid hitting rate limits, especially for 'dec' which has multiple endpoints.
    
    return pd.concat(dataframes_dict.values(), ignore_index=True)

def raw_vars(census_products=None, start_year=None, end_year=None, should_save_csv=False, path=None):

    """
    This function will pull the raw varuables using the 'fetch_data' function. The main difference between the two is that this function allows users to define a list of census products rather than fetching them one by one (eg. [acs1, acs5])
    
    example usage: 

    census_products  = ['acs1', acs5]
    start_year = 2015
    end_year = 2019
    
    all_raw_vars = raw_vars(census_products, start_year, end_year)

    expected output: a dictionary of dataframes named as: start_year_end_year_census_product

    For the above example usage, the dictionary will contain two dataframes:

    2015_2019_acs1 and 2015_2019_acs5

    all_raw_vars -> {
    2015_2019_acs1: dataframe,
    2015_2019_acs5: dataframe    
    }

    """


    dfs_dict = {}

    if census_products is None:
        census_products = ['acs1', 'acs5', 'dec', 'pums1', 'pums5']

    for product in census_products:
        if product in CENSUS_CONFIG:
            config = CENSUS_CONFIG[product]
            base_urls = config.get('base_urls', [config.get('base_url')])
            folder = config['folder']
            
            if start_year is None:
                start_year = config['start_year']
            if end_year is None:
                end_year = pd.Timestamp.now().year
            if path is None:
                path = os.path.join("..", "Data", "Raw Data", "ACS", "All JSON Variables")

            df = fetch_data(product, start_year, end_year, should_save_csv, path)
            dfs_dict[f'{product}_{start_year} - {end_year}'] = df
        else:
            print(f'Invalid census_product: {product}. Available options are: {list(CENSUS_CONFIG.keys())}.')

    return dfs_dict