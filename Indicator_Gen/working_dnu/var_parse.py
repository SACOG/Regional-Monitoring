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


### VARIABLE PARSER ###

def variable_parser(json_url, json_variable_path = None):
    """
    This function will take a URL of the JSON containing dicennial census variables and give an output as a dataframe
    showing the year, variable name, and labels for later use. 
    """
    response = requests.get(json_url)
    data = json.loads(response.text)
    parsed_data = [{**value, 'Variable Name': key} for key, value in data['variables'].items()]
    df = pd.DataFrame(parsed_data)
    
    year_match = re.search(r'/(\d{4})/', json_url)
    year_str = year_match.group(1) if year_match else 'Year_not_found'
    df['Year'] = year_str

    return df