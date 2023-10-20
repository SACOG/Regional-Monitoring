import requests
import pandas as pd
import json
import re


def variable_parser(json_url, json_variable_path = None):
    """
    Retrieves and parses decennial census variables from a JSON URL.

    This function fetches JSON data from the provided URL and extracts decennial 
    census variables. It then structures the data as a pandas DataFrame 
    containing year, variable name, and labels.

    Parameters:
    -----------
    json_url : str
        URL pointing to the JSON containing decennial census variables.
        
    json_variable_path : str, optional (default = None)
        (Currently not in use) Path to extract variables from the JSON data. By default, 
        this function assumes a structure where variables are stored under the 'variables' key.

    Returns:
    --------
    DataFrame
        A DataFrame containing columns 'Year', 'Variable Name', and other attributes (e.g., 'label') 
        extracted from the JSON data for each variable.

    Notes:
    ------
    The function will attempt to parse the year from the URL. If unsuccessful, 
    the year column in the output DataFrame will be set to 'Year_not_found'.
    """

    response = requests.get(json_url)
    data = json.loads(response.text)
    parsed_data = [{**value, 'Variable Name': key} for key, value in data['variables'].items()]
    df = pd.DataFrame(parsed_data)
    
    year_match = re.search(r'/(\d{4})/', json_url)
    year_str = year_match.group(1) if year_match else 'Year_not_found'
    df['Year'] = year_str

    return df
