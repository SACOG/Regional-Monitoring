"""

EPA Pre-processing Functions

Functions:
- load_yaml()
- api_request_params()
- set_download_name()

Parallel to Census pre.py for consistent structure

"""

import numpy as np
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
import yaml
from IPython.display import display

# Determine paths (adjust based on your actual structure)
PATH_GIT = Path(__file__).parent.parent.parent
PATH_CODE = PATH_GIT  / 'EPA'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG = PATH_CODE / 'config'
PATH_ORIG = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' / 'Process Revamp' / 'Task 9. Collect new data' / 'EPA'

# Ensure runs directory exists
RUNS_DIR = PATH_CONFIG / 'runs'
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def load_yaml():
    """
    Load EPA indicators configuration from YAML file
    
    Returns:
        dict: Parsed YAML configuration with indicator definitions
    """
    PATH_YAML = PATH_CONFIG / 'epa_indicators.yaml'
    
    try:
        with open(PATH_YAML, 'r') as yaml_file:
            yaml_epa = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {PATH_YAML} does not exist.")
        print(f"Please create epa_indicators.yaml in {PATH_CONFIG}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    
    return yaml_epa


def api_request_params(yaml_epa, rerun=False):
    """
    Get API request parameters either interactively or from previous run
    
    Args:
        yaml_epa (dict): Parsed YAML configuration
        rerun (bool): If True, load from most recent run file; if False, prompt user
    
    Returns:
        tuple: (api_source, indicator, geography, years_to_import, 
                year_start, year_end, pollutants, sp_location, folder,
                root_url, email, data_endpoint, geo_type, available_geos)
    """
    
    print(); print()
    print('EPA API request parameters:')
    print()
    
    if rerun:
        # Load previous run from runs/ folder
        list_files = [str(entry) for entry in RUNS_DIR.iterdir() if entry.is_file()]
        
        if not list_files:
            print("No previous runs found. Proceeding with interactive mode.")
            rerun = False
        else:
            dt_mod = {}
            for file in list_files:
                time_mod = os.path.getmtime(file)
                time_mod = datetime.fromtimestamp(time_mod).strftime("%Y-%m-%d %H:%M:%S")
                dt_mod[time_mod] = file
            
            most_recent = sorted(list(dt_mod.keys()), reverse=True)[0]
            file_run = dt_mod[most_recent]
            
            print(f"Loading previous run from: {most_recent}")
            print()
            
            df_run = pd.read_csv(file_run, sep=': ', names=['Parameter', 'Input'])
            display(df_run)
            print()
            
            def remove_colon(x):
                return x.replace(':', '')
            
            df_run['Parameter'] = df_run['Parameter'].apply(remove_colon)
            api_source = df_run[df_run['Parameter'] == 'API Source']['Input'].values[0]
            indicator = df_run[df_run['Parameter'] == 'Indicator']['Input'].values[0]
            geography = df_run[df_run['Parameter'] == 'Geography']['Input'].values[0]
            years_str = df_run[df_run['Parameter'] == 'Years']['Input'].values[0]
            years_to_import = [int(y.strip()) for y in years_str.split(',')]
            pollutants_str = df_run[df_run['Parameter'] == 'Pollutants']['Input'].values[0]
            pollutants = [p.strip() for p in pollutants_str.split(',')]
    
    if not rerun:
        # Interactive prompts
        
        # Step 1: Select API Source
        print('-----------------------------------------------------------------------')
        print('Available API sources:')
        api_sources = list(yaml_epa['Indicators'].keys())
        for i, source in enumerate(api_sources, 1):
            print(f'  {i}. {source}')
        print()
        
        source_idx = input('Select API source (number): ')
        try:
            api_source = api_sources[int(source_idx) - 1]
        except (IndexError, ValueError):
            print("Invalid selection. Using default: AQI")
            api_source = 'AQI'
        print(f"Selected API source: {api_source}")
        print()
        
        # Step 2: Select Indicator
        print('-----------------------------------------------------------------------')
        print(f'Available indicators for {api_source}:')
        indicators = list(yaml_epa['Indicators'][api_source].keys())
        for i, ind in enumerate(indicators, 1):
            display_name = yaml_epa['Indicators'][api_source][ind].get('display_name', ind)
            print(f'  {i}. {ind}: {display_name}')
        print()
        
        ind_idx = input('Select indicator (number): ')
        try:
            indicator = indicators[int(ind_idx) - 1]
        except (IndexError, ValueError):
            print("Invalid selection. Using default: first indicator")
            indicator = indicators[0]
        print(f"Selected indicator: {indicator}")
        print()
        
        # Step 3: Select Geography
        print('-----------------------------------------------------------------------')
        available_geos = yaml_epa['Indicators'][api_source][indicator]['available_geographies']
        print(f'Available geographies for {indicator}:')
        for i, geo in enumerate(available_geos, 1):
            print(f'  {i}. {geo["name"]} (code: {geo["code"]})')
        print()
        
        geo_selection = input('Enter geography number(s) separated by commas (or leave blank for all): ')
        
        if geo_selection.strip():
            geo_indices = [int(x.strip()) - 1 for x in geo_selection.split(',')]
            selected_geos = [available_geos[i] for i in geo_indices if i < len(available_geos)]
        else:
            selected_geos = available_geos
        
        geography = ', '.join([geo['code'] for geo in selected_geos])
        geography_names = ', '.join([geo['name'] for geo in selected_geos])
        print(f"Selected geographies: {geography_names}")
        print()
        
        # Step 4: Select Years
        print('-----------------------------------------------------------------------')
        year_range = yaml_epa['Indicators'][api_source][indicator]['year_range']
        year_min = year_range['min']
        year_max = year_range['max']
        print(f'Available years: {year_min} to {year_max}')
        print()
        
        year_input = input(f'Enter years (comma-separated, e.g., {year_max-2},{year_max-1},{year_max}): ')
        
        if year_input.strip():
            try:
                years_to_import = sorted([int(y.strip()) for y in year_input.split(',')])
            except ValueError:
                print(f"Invalid year input. Using default: {year_max-2} to {year_max}")
                years_to_import = list(range(year_max-2, year_max+1))
        else:
            print(f"Using default: {year_max-2} to {year_max}")
            years_to_import = list(range(year_max-2, year_max+1))
        
        print(f"Selected years: {years_to_import}")
        print()
        
        # Step 5: Select Pollutants
        print('-----------------------------------------------------------------------')
        available_pollutants = yaml_epa['Indicators'][api_source][indicator]['available_pollutants']
        print(f'Available pollutants for {indicator}:')
        for i, pol in enumerate(available_pollutants, 1):
            print(f'  {i}. {pol["name"]} (code: {pol["code"]})')
        print()
        
        pol_selection = input('Enter pollutant number(s) separated by commas (or leave blank for all): ')
        
        if pol_selection.strip():
            pol_indices = [int(x.strip()) - 1 for x in pol_selection.split(',')]
            selected_pollutants = [available_pollutants[i] for i in pol_indices if i < len(available_pollutants)]
        else:
            selected_pollutants = available_pollutants
        
        pollutants = [pol['code'] for pol in selected_pollutants]
        pollutant_names = ', '.join([pol['name'] for pol in selected_pollutants])
        print(f"Selected pollutants: {pollutant_names}")
        print()
        
        # Save parameters to runs folder
        year_start = np.min(years_to_import)
        year_end = np.max(years_to_import)
        
        df_run = pd.DataFrame({
            'Parameter': [
                'API Source',
                'Indicator',
                'Geography',
                'Years',
                'Pollutants',
                'Year Start',
                'Year End'
            ],
            'Input': [
                api_source,
                indicator,
                geography,
                ', '.join(map(str, years_to_import)),
                ', '.join(pollutants),
                year_start,
                year_end
            ]
        })
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_run = RUNS_DIR / f"{timestamp}_epa_run.csv"
        
        # Save as text file with ': ' delimiter (pandas sep must be single char)
        with open(file_run, 'w') as f:
            for idx, row in df_run.iterrows():
                f.write(f"{row['Parameter']}: {row['Input']}\n")
        
        print(f"Run parameters saved to: {file_run}")
        print()
    
    # Extract configuration for selected indicator
    config = yaml_epa['Indicators'][api_source][indicator]
    sp_location = config['sp_location']
    folder = config['folder']
    root_url = config['root_url']
    email = config['email']
    data_endpoint = config['data_endpoint']
    geo_type = config['geo_type']
    available_geos = config['available_geographies']
    
    year_start = np.min(years_to_import)
    year_end = np.max(years_to_import)
    
    return (api_source, indicator, geography, years_to_import, 
            year_start, year_end, pollutants, sp_location, folder,
            root_url, email, data_endpoint, geo_type, available_geos)


def set_download_name(indicator, api_source, geography, years_to_import):
    """
    Generate filename for raw CSV download
    
    Args:
        indicator (str): Indicator code (e.g., 'Health_3')
        api_source (str): API source (e.g., 'AQI')
        geography (str): Geography selection
        years_to_import (list): Years selected
    
    Returns:
        str: Filename like "Health_3_AQI_40900_1999-2024_raw.csv"
    """
    year_range = f"{min(years_to_import)}-{max(years_to_import)}"
    
    # Clean geography string (remove spaces, take first code if multiple)
    geo_clean = geography.split(',')[0].strip()
    
    filename = f"{indicator}_{api_source}_{geo_clean}_{year_range}_raw.csv"
    
    return filename