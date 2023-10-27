import pandas as pd
import copy
import traceback
import numpy as np
from itertools import permutations
from .data_group_vars import all_raw_vars, master_vars 
from .helpers import *
from .mapping import *
from .data_group_processing import *
from .configs import report_config, geog_normalization, COUNTY_TO_MPO
from .data_group_vars import filter_vars
from .get_raw_vars import raw_vars
from .get_data import main_fetching_process


def agg_by_comp(geog, data_group, *dims):
    """
    Constructs aggregation indices based on geography, data group, and additional dimensions.
    
    This function constructs two main indices: `agg_ind` and `agg_groupby`. The `agg_ind` is the full 
    index made up of the geography (`geog`), the data group (`data_group`), and any additional dimensions 
    (`dims`). The `agg_groupby` index is derived from `agg_ind` but may exclude the last dimension based on 
    the number of provided dimensions.

    Parameters:
    -----------
    geog : str
        The geography specifier, e.g., 'state', 'county'. Will be transformed to uppercase in the index.

    data_group : str
        The primary data group specifier, e.g., 'race', 'age'. Will be transformed to uppercase in the index.

    *dims : str(s)
        Additional dimensions for constructing the indices. All dimensions will be transformed to uppercase 
        in the index. The last dimension might be excluded from `agg_groupby` depending on its count.

    Returns:
    --------
    tuple (agg_by_agg_ind, agg_by_agg_groupby, agg_ind, agg_groupby) or (None, None, None, None)
        - agg_by_agg_ind: The aggregation configuration for the `agg_ind` index (from the `AGG_BY` constant).
        - agg_by_agg_groupby: The aggregation configuration for the `agg_groupby` index (from the `AGG_BY` constant).
        - agg_ind: The full constructed index string.
        - agg_groupby: The constructed index string for groupby, which may exclude the last dimension.
        If either `agg_ind` or `agg_groupby` are not valid keys in `AGG_BY`, the function returns four Nones.

    Notes:
    ------
    This function relies on the `AGG_BY` constant, which should be defined elsewhere in the code and contain 
    aggregation configurations for various index combinations.

    Examples:
    ---------
    Assuming AGG_BY contains keys 'STATE_RACE_AGE' and 'STATE_RACE':
    >>> agg_by_comp('state', 'race', 'age')
    # Expected output: (AGG_BY['STATE_RACE_AGE'], AGG_BY['STATE_RACE'], 'STATE_RACE_AGE', 'STATE_RACE')

    >>> agg_by_comp('state', 'race')
    # Expected output: (AGG_BY['STATE_RACE'], AGG_BY['STATE'], 'STATE_RACE', 'STATE')

    If invalid indices are provided:
    >>> agg_by_comp('invalid', 'entries')
    # Prints: "Invalid Aggregation: [INVALID_ENTRIES]"
    # Returns: (None, None, None, None)
    """
    agg_groupby_base = geog.upper() + "_" + data_group.upper()

    # Construct agg_ind using all provided dimensions
    agg_ind = "_".join([geog.upper(), data_group.upper()] + [dim.upper() for dim in dims])

    # If there are no additional dimensions, just use the base for agg_groupby
    if not dims:
        agg_groupby = geog.upper()
    # If there's only one dimension, use the base (with data_group) for agg_groupby
    elif len(dims) == 1:
        agg_groupby = agg_groupby_base
    # Otherwise, exclude the last dimension for agg_groupby
    else:
        agg_groupby = "_".join([agg_groupby_base] + [dim.upper() for dim in dims[:-1]])

    if agg_ind not in AGG_BY:
        print(f"Invalid Aggregation: [{agg_ind}]")
        return None, None

    if agg_groupby not in AGG_BY:
        print(f"Invalid Aggregation: [{agg_groupby}]")
        return None, None

    return (copy.deepcopy(AGG_BY[agg_ind]), 
            copy.deepcopy(AGG_BY[agg_groupby]), 
            agg_ind, 
            agg_groupby)


def generate_agg_data(geog, data_group, *dims):
    combinations = []
    
    # Adding the combination with just the data_group and geog
    combinations.append((geog, data_group))

    for dim in dims:
        # Check to ensure data_group and dim are not the same before appending
        if data_group != dim:
            combinations.append((geog, data_group, dim))
            combinations.append((geog, dim, data_group))

    if len(dims) > 1:
        # Ensure that there are no repeated dimensions
        unique_dims = set(dims)
        if len(unique_dims) == len(dims): 
            combined_dims = "_".join(dims)
            combinations.append((geog, data_group, combined_dims))
            combinations.append((geog, combined_dims, data_group))
    return combinations


def calculate_indicator_percentage(resulting_data, data_group, geog, state: Optional[str] = None, api_key = None, *dims):

    """
    Calculates the percentage representation of an indicator across the specified geography and data group.
    
    This function calculates the percentage of an indicator (derived from `data_group` and other dimensions)
    across a specific geography (`geog`). The indicator percentage is calculated based on the formula:
    (indicator total / total) * 100.
    
    Parameters:
    -----------
    resulting_data : DataFrame
        The main dataset containing raw data for calculations.

    filtered_vars : DataFrame
        Dataset containing filtered variables relevant to the calculations.

    data_group : str
        The primary data group specifier, e.g., 'race', 'age'.

    geog : str
        The geography specifier, e.g., 'state', 'county'.

    *dims : str(s)
        Additional dimensions for constructing the indices. All dimensions will be transformed to uppercase 
        in the index.

    Returns:
    --------
    DataFrame
        The DataFrame with the calculated indicator percentages and relevant columns.

    Notes:
    ------
    This function relies on several helper functions:
        - `agg_by_comp`: Determines aggregation indices based on geography, data group, and additional dimensions.
        - `format_agg_ind`: Formats the aggregation indicator by capitalizing components and removing geog.
        - `map_county_names`: Maps county names (assumed to be another function in the codebase).
        - `process_data_group`: Processes the data group (assumed to be another function in the codebase).
        - `census_merge`: Merges census data (assumed to be another function in the codebase).
        - `group_and_sum`: Groups and sums the data based on the provided columns.

    The function also depends on the `AGG_BY` constant, which should be defined elsewhere in the code and contain 
    aggregation configurations for various index combinations.

    Examples:
    ---------
    # Assuming you have data in 'result_data' and 'filtered_vars':
    >>> df = calculate_indicator_percentage(result_data, filtered_vars, 'race', 'county', 'age')
    # This will return a DataFrame with columns like 'County Age Race %' and other related data.
    """


    final_dfs_dict = {}
    resulting_data = input_processing(resulting_data)
    

    df_merged = map_county_names(resulting_data)
    df_merged = process_data_group(resulting_data,data_group)
    
    # Iterate over each combination of geog, data_group, and dims
    for combo in generate_agg_data(geog, data_group, *dims):
        num_cols, div_cols, agg_ind, agg_groupby = agg_by_comp(*combo)
        ind_total_key = " ".join([geog.capitalize(), format_agg_ind(agg_ind, geog), "Totals"])
        total_key = " ".join([geog.capitalize(), format_agg_ind(agg_groupby, geog), "Totals"])


        if not num_cols or not div_cols:
            # Either num_cols or div_cols wasn't found
            return

        config = {
            'total_key': total_key,
            'ind_total_key': ind_total_key
        }        
        

        df = group_and_sum(df_merged, num_cols).reset_index()

        # Creating the column first before checking
        df[config['total_key']] = df.groupby(div_cols)['Total'].transform('sum')
        df = df.rename(columns={'Total': config['ind_total_key']})
        df[f"{AGG_BY[agg_ind][-2]} by {AGG_BY[agg_ind][-1]} Percentage for {geog.capitalize()}" ]= ((df[config['ind_total_key']] / df[config['total_key']]) * 100).round(2)

        # Ensure columns exist in df after creation
        if not set(num_cols).issubset(df.columns):
            raise ValueError(f"The following columns are missing from the DataFrame: {set(num_cols) - set(df.columns)}")

        if not set(div_cols).issubset(df.columns):
            raise ValueError(f"The following columns are missing from the DataFrame: {set(div_cols) - set(df.columns)}")  
        if 'County Name' in df.columns:
            state = state if state else '06'
            fallback_mpo = f"Rest of {FIPS_TO_STATE.get(state, 'Unknown')}"
            df['MPO'] = df['County Name'].map(COUNTY_TO_MPO).fillna(fallback_mpo)

            # Get the index of the 'County Name' column
            idx = df.columns.get_loc('County Name')

            # Use insert to place 'MPO' right after 'County Name'
            mpo_series = df.pop('MPO')  # Remove 'MPO' from its current location
            df.insert(idx + 1, 'MPO', mpo_series)  # Insert it right after 'County Name'

            final_dfs_dict[agg_ind] = df
        else:

            final_dfs_dict[agg_ind] = df
        
        if 'MSA' in df.columns:
            df = map_peer_msa(df, 'MSA')
            final_dfs_dict[agg_ind] = df
  
    return final_dfs_dict
    

def report_agg(raw_variables_df, state, api_key, data_group_name=None, report_config=None):
    """
    Aggregate and generate a reports based on raw variables, specified geography, and configuration.

    This function processes, fetches, and calculates results for given raw variables and configurations. 
    It operates at various geographical levels (like 'county' or 'mpo') and can be used for different 
    data groups (like 'race' or 'age'). It fetches data from a presumed external source using the provided 
    API key, filters necessary variables, and then calculates aggregated results based on permutations 
    of possible dimensions.

    Parameters:
    -----------
    raw_variables_df : DataFrame
        Raw dataset containing the variables needed for calculations.

    state : str
        The state for which the data should be fetched and processed.

    api_key : str
        The API key required to fetch external data.

    data_group_name : str, optional (default=None)
        The name of the data group to process. If not provided, all data groups in the report_config 
        will be processed.

    report_config : dict, optional (default=None)
        Configuration for processing the data groups. If not provided, an empty dictionary is used. 
        The config should be structured with data groups as keys, and values should be dictionaries 
        containing 'geos' and 'dims' for that data group.

    Returns:
    --------
    tuple
        - filter_results : dict
            Dictionary containing filtered variables for each data group.

        - fetched_results : dict
            Dictionary containing fetched census data for each geographical level and data group.

        - calculate_results : dict
            Dictionary containing calculated results for various dimensions at each geographical level.

    Notes:
    ------
    The function relies on several helper functions:
        - `filter_vars`: Filters necessary variables based on the raw variables dataset.
        - `main_fetching_process`: Fetches data from an external source.
        - `final_report_agg`: Aggregates the final report based on the fetched data, filtered variables, and dimensions.

    A caching mechanism (`geo_cache`) is used to avoid fetching the same data multiple times.

    Examples:
    ---------
    # Given a raw variables dataset 'raw_data', state 'CA', and an API key 'my_api_key':
    >>> filter_results, fetched_results, calculate_results = report_agg(raw_data, 'CA', 'my_api_key', data_group_name='race')
    # This will return dictionaries with processed data based on the provided configuration.
    """   

    # Set report_config to a default dict if not provided
    if not report_config:
        report_config = {}

    filter_results = {}
    fetched_results = {}
    calculate_results = {}  # Outer dict
    geo_cache = {}

    data_groups = [data_group_name] if data_group_name else list(report_config.keys())


    for data_group in data_groups:
        if data_group not in report_config:
            print(f"{data_group} not found in the mapping.")
            continue

        info = report_config[data_group]
        print(f'Filtering variables for {data_group}...')
        filtered_vars = filter_vars(raw_variables_df, data_group)
        filter_results[data_group] = filtered_vars

        for geog in info['geos']:
            geog_key = 'county' if geog.lower() == 'mpo' else geog
            cache_key = f"{data_group}_{geog_key}"

            if cache_key in geo_cache:
                print(f"\nUsing cached census data for {geog}...")
                census_data = geo_cache[cache_key]
            else:
                print(f'Fetching census data for {data_group} at the {geog} level...')
                census_data = main_fetching_process(filtered_vars, state, api_key, geog_key)
                geo_cache[cache_key] = census_data

            fetched_results[cache_key] = census_data
                
            try:
                dims = info.get('dims', [])
                if len(dims) > 1:
                    dims_str = ', '.join(dims[:-1]) + ' and ' + dims[-1]
                else:
                    dims_str = dims[0] if dims else ''

                print(f'\nCalculating {data_group} numbers for {geog} and by {dims_str}')
                calculated_df = final_report_agg(census_data, data_group, geog, state, api_key, *dims)
                key_for_calculated_df = list(calculated_df.keys())[0]

                for key_for_calculated_df in calculated_df.keys():
                        # Update the calculate_results dictionary
                    if data_group not in calculate_results:
                        calculate_results[data_group] = {}
                    calculate_results[data_group][key_for_calculated_df] = calculated_df[key_for_calculated_df]

            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                last_traceback = tb[-1]
                file_name, line_number, func_name, text = last_traceback
                print(f"Error processing {data_group}:\n")
                print(f"Exception type: {type(e).__name__}")
                print(f"Exception message: {e}")
                print(f"In file: {file_name}, line {line_number}, in function: {func_name}")
                print(f"Code at error line: {text}")
                if data_group not in calculate_results:
                    calculate_results[data_group] = {}
                calculate_results[data_group] = None

    return filter_results, fetched_results, calculate_results

def race_for_median_income(resulting_data, data_group, geog, state=None, api_key=None, *dims):


    """
    Computes the race variables for median income and returns a dataframe for specified geographic levels.

    This function processes the input data to calculate the race metrics associated with median income for 
    a given geographical region (like county, MPO, etc.). The function identifies the relevant years for 
    calculation from the resulting data, filters the necessary race variables, fetches external data, and 
    then performs the aggregation.

    Parameters:
    -----------
    resulting_data : DataFrame
        Raw dataset containing the variables needed for calculations.

    data_group : str, optional (default='race')
        The group for which the calculation is to be made. Default is 'race'.

    geog : str, optional
        The geographical level for which the data should be processed. Can be values like 'county', 'mpo', etc.

    state : str, optional
        The state for which the data should be fetched and processed.

    api_key : str, optional
        The API key required to fetch external data.

    *dims : tuple, optional
        Additional dimensions or criteria for the aggregation. 

    Returns:
    --------
    DataFrame
        A DataFrame containing the aggregated race metrics for median income for the specified geographical 
        region with appropriately named columns.

    Notes:
    ------
    The function makes use of several helper functions:
        - `input_processing`: Pre-processes the provided data.
        - `census_data_aggs`: Identifies the available census products and year range.
        - `raw_vars`: Retrieves raw variables for specified parameters.
        - `filter_vars`: Filters necessary variables based on the raw variables dataset.
        - `main_fetching_process`: Fetches data from an external source.
        - `calculate_indicator_percentage`: Calculates the race metrics for median income.

    Examples:
    ---------
    # Given a raw variables dataset 'raw_data', state 'CA', geog 'county', and an API key 'my_api_key':
    >>> df_result = race_for_median_income(raw_data, data_group='race', geog='county', state='CA', api_key='my_api_key')
    # This will return a DataFrame with the aggregated metrics for race related to median income for California counties.
    """

    print (f'Calculating {data_group} variable years...')
    resulting_data = input_processing(resulting_data)
    census_products, start_year, end_year = census_data_aggs(resulting_data)
    
    # Extract unique values from the DataFrame for 'Census Product' and 'Year'

    print(f'Filtering {data_group} variables for {start_year} - {end_year}...')
    
    

    # Call filter_vars function with the dynamically populated arguments
    race_filtered_vars = filter_vars(master_vars, data_group='race')    
    race_census_data = main_fetching_process(race_filtered_vars, state, api_key, geog)
    
    print(f'Generating {data_group} numbers for {geog}...')
    
    race_for_median_income = calculate_indicator_percentage(race_census_data, data_group, geog, *dims)    
    
    dynamic_column_name = [race_for_median_income.columns[-3], race_for_median_income.columns[-2]]
    columns_to_return = AGG_BY[f'{geog.upper()}_{data_group.upper()}'] + dynamic_column_name
    
    df = race_for_median_income[columns_to_return]

    geog_mapping = {
    'mpo': 'MPO',
    'county': 'County Name',
    'msa': 'MSA',
    'metro': 'MSA',
    'tract': 'tract'
    }

    # Normalize the geog
    geog_normalized = geog.lower()
    geog_agg_col = geog_mapping.get(geog_normalized)
    
    current_names = df.columns[-2:].tolist()
    
    #rename = [f'Race Group Total by {geog.capitalize()}', f'{geog.capitalize()} Total Population']
    
    rename = [f'Race Group Total by {geog_agg_col}', f'{geog_agg_col} Total Population']


    rename_dict = dict(zip(current_names, rename))
    df = df.rename(columns=rename_dict)
    
    return df

def calculate_median_income(resulting_data, data_group, geog, state, api_key=None, *dims):

    """
    Computes the median income for specified data groups and geographical levels.

    This function takes in raw data and related variables, and calculates the median income based on the 
    specified data group, state, and geographic region. The calculation is done taking race into consideration,
    and the function returns a DataFrame containing the aggregated median income metrics.

    Parameters:
    -----------
    resulting_data : DataFrame
        Raw dataset containing the data required for calculations.

    filtered_vars : DataFrame
        Data containing the filtered variables relevant to the calculations.

    data_group : str
        The group for which the median income calculation is to be made.

    state : str
        The state for which the data should be processed.

    geog : str
        The geographical level for which the median income should be calculated, such as 'county', 'mpo', etc.

    api_key : str, optional
        The API key required to fetch any external data.

    *dims : tuple, optional
        Additional dimensions or criteria for the calculation. 

    Returns:
    --------
    DataFrame
        A DataFrame containing the aggregated median income metrics for the specified geographical region,
        with columns related to the race group, median income by race, median income by geographical level,
        and the income ratio.

    Notes:
    ------
    The function makes use of several helper functions:
        - `input_processing`: Pre-processes the provided data.
        - `race_for_median_income`: Calculates race-related data for median income.
        - `map_county_names`, `process_data_group`, `census_merge`: Mapping and processing functions.
        - `calculate_weighted_incomes`: Computes weighted incomes based on given parameters.
        - `income_group_data`: Groups the data based on income ranges.
        - `final_df_compile`: Compiles the final DataFrame.

    Examples:
    ---------
    # Given a raw dataset 'raw_data', filtered variables 'filtered_data', a data group 'income',
    # state 'CA', geog 'county', and an API key 'my_api_key':
    >>> df_result = calculate_median_income(raw_data, filtered_data, 'income', 'CA', 'county', api_key='my_api_key')
    # This will return a DataFrame with median income metrics for California counties.
    """
    num_cols, div_cols, agg_ind, agg_groupby = agg_by_comp(geog, data_group='race')

    resulting_data = input_processing(resulting_data)
    r = race_for_median_income(resulting_data = resulting_data, data_group='race', geog=geog, state=state, api_key=api_key, *dims)

    resulting_data['Total'] = resulting_data['Total'].fillna(0).astype(int)
    resulting_data = resulting_data[resulting_data['Total'] >= 0]
    resulting_data = resulting_data.rename(columns = {'Total': 'Median Income'})
    resulting_data['Median Income'] = resulting_data['Median Income'].fillna(0).astype(np.int64)

    m = map_county_names(
       process_data_group(
        resulting_data,
        data_group)
    )
    
    geog_mapping = {
    'mpo': 'MPO',
    'county': 'County Name',
    'msa': 'MSA',
    'metro': 'MSA',
    'tract': 'tract'
    }

    # Normalize the geog
    geog_normalized = geog.lower()
    geog_agg_col = geog_mapping.get(geog_normalized)
    race_group_total_col = f'Race Group Total by {geog_agg_col}'
    
    # Check for invalid geog
    if geog_agg_col is None:
        print('Invalid geog provided')
        exit()  # Exit the script if invalid geog
    
    # Get some values
    merge_cols = AGG_BY[f'{geog.upper()}_RACE']
    race_median_income = pd.merge(r, m, on=merge_cols)
    
    # Define some columns
    median_income_col = 'Median Income'
    geog_total_population_col = f'{geog_agg_col} Total Population'

    print(f'Calculating weighted incomes by race and {geog_agg_col}...')
    race_median_income = calculate_weighted_incomes(race_median_income, median_income_col, race_group_total_col, geog_agg_col,geog_total_population_col)

    print(f'Calculating median incomes by race and {geog_agg_col}...')

    grouped_by_race, grouped_by_geog = income_group_data(race_median_income, div_cols, geog_agg_col ,race_group_total_col)

    print(f'Generating final median incomes by race for {geog_agg_col}...')

    final_df = final_df_compile(grouped_by_race, grouped_by_geog, div_cols, geog_agg_col)
    
    df = final_df[div_cols+['Race Group','Median Income by Race',f'Median Income by {geog_agg_col}',f'Income Ratio Race Group by {geog_agg_col}']]
    
    if 'County Name' in df.columns:
        state = state if state else '06'
        fallback_mpo = f"Rest of {FIPS_TO_STATE.get(state, 'Unknown')}"
        df['MPO'] = df['County Name'].map(COUNTY_TO_MPO).fillna(fallback_mpo)

        # Get the index of the 'County Name' column
        idx = df.columns.get_loc('County Name')

        # Use insert to place 'MPO' right after 'County Name'
        mpo_series = df.pop('MPO')  # Remove 'MPO' from its current location
        df.insert(idx + 1, 'MPO', mpo_series)  # Insert it right after 'County Name'
        return final_df
    else:
        return df

    return final_df

def final_report_agg(resulting_data, data_group, geog, state, api_key=None, *dims):

    if data_group == 'median income':
        return calculate_median_income(resulting_data, data_group, geog, state, api_key, *dims)
    else:
        return calculate_indicator_percentage(resulting_data, data_group, geog, state, api_key, *dims)