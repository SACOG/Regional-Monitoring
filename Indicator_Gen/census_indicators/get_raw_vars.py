import os
import requests
import pandas as pd
import time
from .var_parse import *
from .configs import CENSUS_CONFIG

def save_to_csv(df, df_name, path, folder):
    directory_path = os.path.join(path, folder)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    df.to_csv(os.path.join(directory_path, df_name + ".csv"))

def fetch_data(product, start_year=None, end_year=None, should_save_csv=False, path=None):
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
    dfs_dict = {}

    if census_products is None:
        census_products = ['acs1', 'acs5', 'dec']

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