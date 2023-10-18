import pandas as pd
import copy
import numpy as np
from .helpers import *
from .mapping import *
from .data_group_processing import *
from .configs import report_config, geog_normalization
from .data_group_vars import filter_vars
from .get_raw_vars import raw_vars
from .get_data import main_fetching_process

def agg_by_comp(geog, data_group, *dims):

    # Base aggregation groupby
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

def calculate_indicator_percentage(resulting_data, filtered_vars, data_group, geog, *dims):
    num_cols, div_cols, agg_ind, agg_groupby = agg_by_comp(geog, data_group, *dims)
    ind_total_key = " ".join([geog.capitalize(), format_agg_ind(agg_ind, geog), "Totals"]).replace("  ", " ")
    total_key = " ".join([geog.capitalize(), format_agg_ind(agg_groupby, geog), "Totals"]).replace("  ", " ")


    # Remove double spaces from num_cols and div_cols
    #num_cols = [col.replace("  ", " ") for col in num_cols]
    #div_cols = [col.replace("  ", " ") for col in div_cols]


    if not num_cols or not div_cols:
        # Either num_cols or div_cols wasn't found
        return

    config = {
        'total_key': total_key,
        'ind_total_key': ind_total_key
    }

    df_merged = map_county_names(
       process_data_group(
        census_merge(resulting_data, filtered_vars),
        data_group)
    )

    df = group_and_sum(df_merged, num_cols).reset_index()

    # Creating the column first before checking
    df[config['total_key']] = df.groupby(div_cols)['Total'].transform('sum')
    df = df.rename(columns={'Total': config['ind_total_key']})
    df[f"{AGG_BY[agg_ind][-2]} by {AGG_BY[agg_ind][-1]} % for {geog.capitalize()}" ]= ((df[config['ind_total_key']] / df[config['total_key']]) * 100).round(2)

    # Ensure columns exist in df after creation
    if not set(num_cols).issubset(df.columns):
        raise ValueError(f"The following columns are missing from the DataFrame: {set(num_cols) - set(df.columns)}")

    if not set(div_cols).issubset(df.columns):
        raise ValueError(f"The following columns are missing from the DataFrame: {set(div_cols) - set(df.columns)}")

    return df

def report_agg(raw_variables_df, state, api_key, data_group_name=None, report_config=None):
    
    # Set report_config to a default dict if not provided
    if not report_config:
        report_config = {}
    
    filter_results = {}
    fetch_results = {}
    calculate_results = {}
    geo_cache = {}  # Initialize the geo_cache outside the loop
    
    # If data_group_name is None, process all data groups. Otherwise, process only the specified data group.
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
            cache_key = f"{data_group}_{geog_key}"  # Combined cache key

            # Check if the geographical data for this specific data_group and geog has been fetched
            if cache_key in geo_cache:
                print(f"Using cached census data for {cache_key}...")
                census_data = geo_cache[cache_key]
            else:
                print(f'Fetching census data for {data_group} at the {geog} level...')
                census_data = main_fetching_process(filtered_vars, state, api_key, geog_key)
                geo_cache[cache_key] = census_data

            all_dims = [()] + [tuple(info['dims'][:i+1]) for i in range(len(info['dims']))]
            for dims in all_dims:
                key_calc = f"{geog}_{data_group}" + ("_" + "_".join(dims) if dims else "")
                print(f'Calculating results for {key_calc}...')
                try:
                    if data_group == 'median income':
                        calculate_results[key_calc] = calculate_median_income(census_data, filtered_vars, data_group, geog, *dims)
                    else:
                        calculate_results[key_calc] = calculate_indicator_percentage(census_data, filtered_vars, data_group, geog, *dims)
                except Exception as e:
                    print(f"Error processing {key_calc}: {e}")
                    calculate_results[key_calc] = None

    return filter_results, fetch_results, calculate_results


def race_for_median_income(resulting_data, data_group='race', geog=None, state=None, api_key=None, *dims):
    print (f'Calculating {data_group} variable years...')
    resulting_data = input_processing(resulting_data)
    census_products, start_year, end_year = census_data_aggs(resulting_data)
    
    # Extract unique values from the DataFrame for 'Census Product' and 'Year'

    print(f'Filtering {data_group} variables for {start_year} - {end_year}...')


    # Call filter_vars function with the dynamically populated arguments
    race_filtered_vars = filter_vars(raw_vars(census_products=census_products, start_year=start_year, end_year=end_year), data_group='race')    
    race_census_data = main_fetching_process(race_filtered_vars, state, api_key, geog)
    
    print(f'Generating {data_group} numbers for {geog}...')
    
    race_for_median_income = calculate_indicator_percentage(race_census_data, race_filtered_vars, data_group, geog, *dims)    
    
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

def calculate_median_income(resulting_data, filtered_vars, data_group, state, geog, api_key = None, *dims):

    #race_nums = race_for_median_income(resulting_data = resulting_data, data_group='race', geog=geog, state=state, api_key=api_key)
    num_cols, div_cols, agg_ind, agg_groupby = agg_by_comp(geog, data_group='race')

    resulting_data = input_processing(resulting_data)
    r = race_for_median_income(resulting_data = resulting_data, data_group='race', geog=geog, state=state, api_key=api_key, *dims)

    resulting_data['Total'] = resulting_data['Total'].fillna(0).astype(int)
    resulting_data = resulting_data[resulting_data['Total'] >= 0]
    resulting_data = resulting_data.rename(columns = {'Total': 'Median Income'})
    resulting_data['Median Income'] = resulting_data['Median Income'].fillna(0).astype(np.int64)

    m = map_county_names(
       process_data_group(
        census_merge(resulting_data, filtered_vars),
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
    
    final_df = final_df[div_cols+['Race Group','Median Income by Race',f'Median Income by {geog_agg_col}',f'Income Ratio Race Group by {geog_agg_col})']]
    

    return final_df

def final_report_agg (resulting_data, filtered_vars, data_group, geog, *dims):

    if data_group == 'median income':
        return calculate_median_income(resulting_data, filtered_vars, data_group, geog)
    else:
        return calculate_indicator_percentage(resulting_data, filtered_vars, data_group, geog, *dims)