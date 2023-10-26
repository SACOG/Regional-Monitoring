import pandas as pd
import requests
from typing import List, Optional
from .mapping import map_county_names
from .helpers import input_processing, census_merge
from .configs import FIPS_DF, COUNTY_TO_MPO

def display_progress_bar(current_step, total_steps, bar_length=50):
    """
    Displays a progress bar in the console to indicate the completion status of a task.

    Parameters:
    - current_step (int): The current completed step.
    - total_steps (int): The total number of steps in the task.
    - bar_length (int, optional): The length of the progress bar, in characters. Defaults to 50.

    Returns:
    None. Prints the progress bar directly to the console.
    
    Example:
    If the function is called with `current_step=3` and `total_steps=10`, 
    it will print a progress bar that's 30% complete.
    """
    progress = (current_step/total_steps)
    arrow = '-' * int(round(progress * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))
    print('\rProgress: [{0}] {1}%'.format(arrow + spaces, int(round(progress * 100))), end='')

def fetch_data_chunk_for_metro(variables_chunk, api_key, data_url, state):
    """
    Fetches a chunk of data for metropolitan areas based on the provided variables.

    Parameters:
    - variables_chunk (list): List of variable names to fetch data for.
    - api_key (str): The API key to authenticate the request.
    - data_url (str): The base URL endpoint to make the API request.
    - state (str): The state code to limit the data fetch.

    Returns:
    - pd.DataFrame: A DataFrame containing the fetched data. Returns None if the API request fails.
    
    Notes:
    - The function sends a GET request to the specified `data_url` with the provided parameters.
    - If the response is successful, it transforms the response into a melted DataFrame for easier analysis.
    - In case of an API error, the error is printed and the function returns None.
    """
    params = {
        'get': 'NAME,' + ','.join(variables_chunk),
        'for': 'metropolitan statistical area/micropolitan statistical area:*',
        'key': api_key,
    }
    response = requests.get(data_url, params=params)
    
    if response.status_code != 200:
        print(f"API call failed with status code {response.status_code}. Message: {response.text}")
        return None
    
    header, *data = response.json()
    df = pd.DataFrame(data, columns=header)
    df_melted = df.melt(id_vars=['NAME','metropolitan statistical area/micropolitan statistical area'], 
                        value_vars=variables_chunk, 
                        var_name='Variable Name', 
                        value_name='Total')
    df_melted = df_melted.rename(columns = {"NAME": "MSA"})
    return df_melted

def fetch_data_chunk_for_county(variables_chunk, api_key, data_url, state):
    """
    Fetches a chunk of data for counties based on the provided variables.

    Parameters:
    - variables_chunk (list): List of variable names to fetch data for.
    - api_key (str): The API key to authenticate the request.
    - data_url (str): The base URL endpoint to make the API request.
    - state (str): The state code to limit the data fetch.

    Returns:
    - pd.DataFrame: A DataFrame containing the fetched data. Returns None if the API request fails.
    
    Notes:
    - The function sends a GET request to the specified `data_url` with the provided parameters.
    - If the response is successful, it transforms the response into a melted DataFrame for easier analysis.
    - In case of an API error, the error is printed and the function returns None.
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

def fetch_data_chunk_for_tract(variables_chunk: List[str], api_key: str, data_url: str, state: str, mpo: Optional[str] = None) -> pd.DataFrame:
    """
    Fetches a chunk of data for census tracts based on the provided variables.

    Parameters:
    - variables_chunk (list): List of variable names to fetch data for.
    - api_key (str): The API key to authenticate the request.
    - data_url (str): The base URL endpoint to make the API request.
    - state (str): The state code to limit the data fetch.

    Returns:
    - pd.DataFrame: A DataFrame containing the fetched data. Returns None if the API request fails.
    
    Notes:
    - The function sends a GET request to the specified `data_url` with the provided parameters.
    - If the response is successful, it transforms the response into a melted DataFrame for easier analysis.
    - In case of an API error, the error is printed and the function returns None.
    """
    if not mpo:
        mpo = 'SACOG'
    
    if not state:
        state = '06'
        
        
    # Create a copy of the filtered DataFrame to avoid the warning
    county_df = FIPS_DF[FIPS_DF['state'] == state].copy()
    county_df['county_name'] = county_df['county_name'].str.replace(" County$", "", regex=True)  
    county_df['MPO'] = county_df['county_name'].map(COUNTY_TO_MPO).fillna('None')
    county_df = county_df[county_df['MPO'] == mpo].reset_index() 
    counties_to_fetch = county_df['county'].to_list()
    
    all_data = []  # Collect all data from each API call here
    for c in counties_to_fetch:
        params = {
            'get': ','.join(variables_chunk),
            'for': f'tract:*',
            'in': f'state:{state} county:{c}',  # Specify the county in the params
            'key': api_key,
        }
    
        response = requests.get(data_url, params=params)    
        if response.status_code != 200:
            print(f"API call failed with status code {response.status_code}. Message: {response.text}")
            continue
        
        header, *data = response.json()
        df = pd.DataFrame(data, columns=header)
        df_melted = df.melt(id_vars=['state', 'county', 'tract'], 
                            value_vars=variables_chunk, 
                            var_name='Variable Name', 
                            value_name='Total')
        
        all_data.append(df_melted)  # Append the melted data to all_data list
    
    # Combine all data into one DataFrame
    result_df = pd.concat(all_data, ignore_index=True)
    return result_df

def get_census_data(df, api_key, data_url, state, fetch_data_chunk_function):
    """
    Retrieves census data for a set of variables by chunking the variable list and fetching data in parts.

    Parameters:
    - df (pd.DataFrame): DataFrame containing the list of variable names to fetch data for.
    - api_key (str): The API key to authenticate the request.
    - data_url (str): The base URL endpoint to make the API request.
    - state (str): The state code to limit the data fetch.
    - fetch_data_chunk_function (function): A function reference to either `fetch_data_chunk_for_metro`, `fetch_data_chunk_for_county`, or `fetch_data_chunk_for_tract`.

    Returns:
    - pd.DataFrame: A concatenated DataFrame with data from all chunks.

    Notes:
    - The function divides the list of variables into chunks and fetches data chunk-by-chunk using the specified fetch_data_chunk_function.
    - All the fetched chunks are concatenated into a final DataFrame which is then returned.
    """
    variables = df['Variable Name']
    # Subtract 3 to account for NAME, state, and county
    variables_chunks = [variables[i:i+40] for i in range(0, len(variables), 40)]
    
    df_list = []
    for chunk in variables_chunks:
        df_chunk = fetch_data_chunk_function(chunk, api_key, data_url, state)
        df_list.append(df_chunk)

    df_final = pd.concat(df_list, ignore_index=True)
    return df_final

def get_census_mappings(df):
    """
    Extracts the mappings for census data products from the input DataFrame.

    Parameters:
    - df (pd.DataFrame): A DataFrame containing columns 'Year' and 'Census Product'.

    Returns:
    - dict: A dictionary mapping census product names ('ACS1', 'ACS5', and 'DEC') to corresponding URLs and filtered DataFrames.

    Notes:
    - This function processes the input DataFrame to extract specific URL endpoints and related data for each census product.
    - The returned dictionary provides a quick lookup for endpoints and related data based on the census product name.
    """

    df['Year'] = df['Year'].astype(str)

    return {
        'ACS1': ('https://api.census.gov/data/{}/acs/acs1', df[df['Census Product'] == 'ACS1']),
        'ACS5': ('https://api.census.gov/data/{}/acs/acs5', df[df['Census Product'] == 'ACS5']),
        'DEC':  ({
            '2000': 'https://api.census.gov/data/{}/dec/sf1',
            '2010': 'https://api.census.gov/data/{}/dec/sf1',
            '2020': 'https://api.census.gov/data/{}/dec/dp'
        }, df[df['Census Product'] == 'DEC'])
    }

def process_each_product(product, url_map, product_df, state, api_key, total_years, current_year_number, fetch_data_chunk_function):
    """
    Process each product for its unique years and fetches the data.
    
    Parameters:
    - product (str): Census product name (e.g., 'ACS1', 'ACS5', 'DEC').
    - url_map (dict/str): Dictionary of year to URL mapping or a string template of the URL.
    - product_df (pd.DataFrame): Filtered DataFrame for the product and years.
    - state (str): The state code.
    - api_key (str): The API key for making requests.
    - total_years (int): Total number of years to fetch across all products.
    - current_year_number (int): Progress counter for the years fetched.
    - fetch_data_chunk_function (function): Function to fetch the data chunk based on geography.

    Returns:
    - dict: A dictionary with keys in format "Year_Product_Census_Data" and values as corresponding data DataFrames.
    """
    dataframes_dict = {}
    unique_years = product_df['Year'].unique()
    for year in unique_years:
        constructed_data_url = (url_map[year] if isinstance(url_map, dict) else url_map).format(year)
        try:
            output_df = get_census_data(product_df[product_df['Year'] == year], api_key, constructed_data_url, state, fetch_data_chunk_function)
            output_df = update_output_dataframe(output_df, year, product)
            key = f"{year}_{product}_Census_Data"
            dataframes_dict[key] = output_df
        except Exception as e:
            print(f"Error fetching data for year {year} with URL {constructed_data_url}: {e}")
        
        current_year_number += 1
        display_progress_bar(current_year_number, total_years)

    return dataframes_dict

def update_output_dataframe(output_df, year, product):
    """
    Updates the output DataFrame with the year and product name.
    
    Parameters:
    - output_df (pd.DataFrame): The DataFrame to update.
    - year (str): The year to add to the DataFrame.
    - product (str): The product name to add to the DataFrame.

    Returns:
    - pd.DataFrame: Updated DataFrame.
    """    
    output_df['Year'] = year
    output_df['Census Product'] = product
    return output_df

def fetch_census_data_for_all_products(data_input, state, api_key, fetch_func, geography):
    """
    Fetches census data for all products specified in the data input.
    
    Parameters:
    - data_input (pd.DataFrame): Input DataFrame with variable names, products, and years.
    - state (str): The state code.
    - api_key (str): The API key for making requests.
    - fetch_func (function): Function to fetch the data chunk based on geography.
    - geography (str): The specified geography (e.g., 'county', 'tract', 'msa').

    Returns:
    - dict: A dictionary with keys in format "Year_Product_Census_Data" and values as corresponding data DataFrames.
    """    
    df = input_processing(data_input)
    census_mappings = get_census_mappings(df)
    
    total_years = sum([len(product_df['Year'].unique()) for _, (_, product_df) in census_mappings.items()])
    current_year_number = 0
    all_dataframes_dict = {}
    
    for product, (url_map, product_df) in census_mappings.items():
        if not product_df.empty:  # Check if there's data left to process
            if product == 'DEC':  # Handle 'DEC' differently since it has a dictionary for URLs
                for year in product_df['Year'].unique():
                    if year not in url_map:  # Skip if the year's URL is not in the mapping
                        continue
                    year_df = product_df[product_df['Year'] == year]
                    dataframes_dict = process_each_product(product, url_map[year], year_df, state, api_key, total_years, current_year_number, fetch_func)
                    all_dataframes_dict.update(dataframes_dict)
                    current_year_number += 1
            else:
                dataframes_dict = process_each_product(product, url_map, product_df, state, api_key, total_years, current_year_number, fetch_func)
                all_dataframes_dict.update(dataframes_dict)
                current_year_number += len(product_df['Year'].unique())
    
    return all_dataframes_dict

def main_fetching_process(data_input, state, api_key, geography:str):
    """
    Main process to fetch census data based on the specified geography.
    
    Parameters:
    - data_input (pd.DataFrame): Input DataFrame with variable names, products, and years.
    - state (str): The state code.
    - api_key (str): The API key for making requests.
    - geography (str): The specified geography (e.g., 'county', 'tract', 'msa').
    

    Returns:
    - dict: A dictionary with keys in format "Year_Product_Census_Data" and values as corresponding data DataFrames.
    """
    data_input = input_processing(data_input)
    

    geo = geography.lower()
    fetch_funcs = {
        'county': fetch_data_chunk_for_county,
        'mpo': fetch_data_chunk_for_county,
        'tract': fetch_data_chunk_for_tract,
        'msa': fetch_data_chunk_for_metro
    }

    if geo == 'tract':
        data_input = data_input[data_input['Census Product'] != 'ACS1']
    elif geo == 'msa':
        data_input = data_input[data_input['Census Product'] != 'DEC']
    
    fetch_func = fetch_funcs.get(geo)
    if fetch_func is None:
        raise ValueError("Invalid geography specified.")

    resulting_data = fetch_census_data_for_all_products(data_input, state, api_key, fetch_func, geography)

    # Passing the fetched dataframes through census_merge
    for key, df in resulting_data.items():
        if df is not None:  # Ensure that the dataframe isn't None
            resulting_data[key] = census_merge(df,data_input)

    return resulting_data

executed_geos = set()

def fetch_and_concatenate_data(data_input, state, api_key, geos_list):
    """
    Fetches and concatenates data for the specified list of geographies.
    
    Parameters:
    - data_input (pd.DataFrame): Input DataFrame with variable names, products, and years.
    - state (str): The state code.
    - api_key (str): The API key for making requests.
    - geos_list (list): A list of specified geographies (e.g., ['county', 'tract', 'msa']).

    Returns:
    - dict: A dictionary with keys as geographies and values as data fetched for those geographies.
    """    
    data_input = input_processing(data_input)
    if geo in executed_geos:
        return  # Already fetched for this geography, no need to refetch
    
    data = main_fetching_process(data_input, state, api_key, geo)
    
    if geo in ['county', 'mpo']:
        executed_geos.add('county')
        executed_geos.add('mpo')
    else:
        executed_geos.add(geo)

    return data

def fetch_and_concatenate_data(data_input, state, api_key, geos_list):
    """
    Fetches and aggregates data for a list of specified geographies.

    The function processes the input data, iterates over the specified geographies,
    and fetches the relevant data chunks. If the geography is 'county' or 'mpo', 
    the fetched data is stored under both keys in the result dictionary due to their 
    overlapping nature.

    Parameters:
    - data_input (pd.DataFrame or other appropriate datatype): Input data containing variable names, 
        products, and years. It undergoes processing using the `input_processing` function.
    - state (str): The state code for which the data should be fetched.
    - api_key (str): The API key used for making requests to the data source.
    - geos_list (list of str): A list of geographies for which data should be fetched. 
        Valid entries include 'county', 'tract', 'mpo', 'msa', etc.

    Returns:
    - dict: A dictionary where each key corresponds to a geography and its value is 
        the data fetched for that geography. If the geography is 'county' or 'mpo', 
        data is duplicated and stored under both keys.

    Note:
    This function makes use of the `input_processing` and 
    `fetch_data_chunk_for_geography` functions, which must be available in the 
    current environment.
    """

    data_input = input_processing(data_input)
    results = {}
    for geo in geos_list:
        data_for_geo = fetch_data_chunk_for_geography(data_input, state, api_key, geo)
        
        # In case we are fetching for 'county' or 'mpo', store the data under both keys
        if geo == 'county':
            results['county'] = data_for_geo
            results['mpo'] = data_for_geo
        elif geo == 'mpo':
            results['mpo'] = data_for_geo
            results['county'] = data_for_geo
        else:
            results[geo] = data_for_geo

    return results