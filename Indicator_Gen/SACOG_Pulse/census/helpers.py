import re
import os
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Union
import itertools
import logging
from .configs import report_config, acs1_commute_vars, acs5_commute_vars, acs1_2005_commute_vars


"""
This file contains helper functions used throughout the 'census' module for the SACOG_Pulse package.
"""

### DATA PROCESSING HELPER FUNCTIONS ###

def fill_missing_values(df: pd.DataFrame, ref_col: str = 'Variable Name') -> pd.DataFrame:

    """
    This function takes in a dataframe and fills any values in the 'label' or 'concept' colums that may be empty by using the 'Variable Name' as a reference of what values to input. 

    eg. If the input dataframe contains Variable Name abc123 with a concept of def456 in one row, and a label of ghi789 in another but the same variable has a blank concept elsewhere, the 'concept' of the populated Variable Name concept or label row will update accordingly:

    df = 

    |Variable Name | concept | label  |
    +              +         +        +
    |abc123        |def456   |        |
    +              +         +        + ------------> fill_missing_values(df)
    |abc123        |         | ghi789 |
    +              +         +        +

    ***********processed***************

    |Variable Name | concept | label  |
    +              +         +        +
    |abc123        |def456   | ghi789 |
    +              +         +        + 
    |abc123        |def456   | ghi789 |
    +              +         +        +


    """
    
    # Check if 'label' or 'concept' columns are not in DataFrame, return original if not
    if 'label' not in df.columns and 'concept' not in df.columns:
        return df

    if 'concept' in df.columns:
        # Create a dictionary that maps each unique Variable Name to its corresponding non-NaN concept value
        concept_dict = df.dropna(subset=['concept']).groupby(ref_col)['concept'].first().to_dict()
        # Use the dictionary to fill NaN values in the concept column based on Variable Name
        df['concept'] = df.apply(lambda row: concept_dict.get(row[ref_col], np.nan) if (pd.isna(row['concept']) and row[ref_col] in concept_dict) else row['concept'], axis=1)
    
    if 'label' in df.columns:
        # Create a dictionary that maps each unique Variable Name to its corresponding non-NaN label value
        label_dict = df.dropna(subset=['label']).groupby(ref_col)['label'].first().to_dict()
        # Use the dictionary to fill NaN values in the label column based on Variable Name
        df['label'] = df.apply(lambda row: label_dict.get(row[ref_col], np.nan) if (pd.isna(row['label']) and row[ref_col] in label_dict) else row['label'], axis=1)

    return df

def input_processing(data_input):
    """
    This fucntion is the main processing function for the 'census' module for the SACOG_Pulse package.

    This function will:

    1. Take in an input
    2. Ensure it is a df or a dictionary
    3. Perform any processing steps needed
    4. Return a df of the input. 

    example usage:

    data = data_dictionary

    input_processing(data)

    expected output: a dataframe

    """

    if isinstance(data_input, pd.DataFrame):
        df = data_input
    elif isinstance(data_input, dict):
        df = pd.concat(data_input.values(), ignore_index=True)
    else:
        logging.error("Invalid input type. Must be a dictionary or a dataframe.")
    df['Year'] = df['Year'].astype(int)
    return fill_missing_values(df)



def clean_labels(df):
    """
    Helper function to remove colons from label column.
    
    example usage:

    |Variable Name | concept | label  |
    +              +         +        + ------------> clean_labels(df)
    |abc123        |def456   | ghi789:|

    ***********processed***************

    |Variable Name | concept | label  |
    +              +         +        +
    |abc123        |def456   | ghi789 |


    """
    return df.assign(label=df['label'].str.replace(':', ''))

def extract_content_between_excl(text: str, position: int = -1) -> Optional[str]:
    """
    Extract content between the specified set of exclamation marks in a string based on the index position. The defualt index position is -1 (the last one)
    
    eg: 

    text = 'The!!Red!!Fox!!Jumped!!Over!!The!!Brown!!Cat'

    extract_content_between_excl(text, position = -2)

    output: 'Brown'

    """
    matches = re.findall('!!([^!]+)', text)
    if matches:
        return matches[position] if (0 <= position < len(matches)) or (position < 0 and abs(position) <= len(matches)) else None
    return None

def extract_content_between_parentheses(text: str, position: int = -1) -> Optional[str]:
    """
    Extract content between the specified text within a set of parentheses in a string based on the index position. The defualt index position is -1 (the last one)
    
    eg: 

    text = 'The Red (fox) jumped (over) the (brown) cat'

    extract_content_between_parentheses(text, position = -2)

    output: 'over'

    """
    matches = re.findall(r'\(([^)]+)\)', text)
    if matches:
        return matches[position] if (0 <= position < len(matches)) or (position < 0 and abs(position) <= len(matches)) else None
    return None
### CENSUS MERGE ###


def census_merge(resulting_data, filtered_vars):

    """
    This function will take a data frame or dictionary containing fetched census data, and a dataframe or dictionary containing filtered variables and merge them. 
    
    It will also convert particular columns into appropriate types for later operations. 


    """


    df = input_processing(resulting_data)    
    filtered_vars = input_processing(filtered_vars)[['Year', 'Census Product', 'Variable Name', 'label', 'concept']]
    df_merge = pd.merge(df, filtered_vars, on=['Census Product', 'Year', 'Variable Name'])
    
    # Adjust type casting for specific columns
    for col in ['Total', 'Median Income']:
        if col in df_merge.columns:
            if col == 'Total':
                df_merge[col].fillna(0, inplace=True)
                df_merge[col] = df_merge[col].astype(int)
            elif col == 'Median Income':
                df_merge[col].fillna(0, inplace=True)
                df_merge[col] = df_merge[col].astype(np.int64)

    return df_merge



### AGGREGATION GENERATION ###

BASE_GROUP = ['Census Product', 'Year']

# Geography Groups
GEOG_GROUPS = {
    'MPO': ['MPO'],
    'COUNTY': ['County Name'],
    'TRACT': ['MPO', 'County Name', 'tract'],
    'MSA': ['MSA'],
    'METRO': ['MSA'],
    'PUMA': ['PUMA Name']
}

# Demographics Groups
DEMO_GROUPS = {
    'RACE': ['Race Group'],
    'AGE': ['Age Group'],
    'EDUCATION': ['Education Group'],
    'EMPLOYMENT': ['Employment Status'],
    'HOUSEHOLD INCOME': ['Income Group'],
    'COMMUTE': ['Commute Group'],
    'POVERTY': ['Poverty Status'],
    'GENDER':['Gender'],
    'MEDIAN INCOME': ['Median Income'],
    'BROADBAND': ['Broadband']
}


def generate_groups(report_config):

    """
    This function will take a report_config dictionary and generate a dictionary of aggregation levels to be used in indicator calculations. 
    
    The AGG_BY dictionary is powered by this function.
    
    example: 

    eg = {'employment': {
        'geos': ['mpo'],
        'dims': ['age']
    }
    
}
    
    eg. genrate_groups(eg)

    output: 

    {'MPO_EMPLOYMENT': ['Census Product', 'Year', 'MPO', 'Employment Status'],
     'MPO_AGE': ['Census Product', 'Year', 'MPO', 'Age Group'],
     'MPO_EMPLOYMENT_AGE': ['Census Product','Year','MPO','Employment Status','Age Group'],
     'MPO_AGE_EMPLOYMENT': ['Census Product','Year','MPO','Age Group','Employment Status'],
     'MPO': ['Census Product', 'Year', 'MPO']
     }

    """

    agg_by = {}

    # Process each data_group in the report_config
    for data_group, details in report_config.items():

        # All possible dimensions including the data_group itself
        all_dims = [data_group] + details['dims']

        # Create permutations of demographic groups, and iterate over them
        for L in range(1, len(all_dims) + 1):
            for subset in itertools.permutations(all_dims, L):
                subset_key = "_".join(subset).upper()

                # Create the combinations with geography
                for geog in details['geos']:
                    key = f"{geog}_".upper() + subset_key
                    if key not in agg_by:
                        # Calculate the values for this combination
                        geog_group = GEOG_GROUPS[geog.upper()]
                        
                        # Add the base demographic group values
                        demo_values = [item for sublist in [DEMO_GROUPS[x.upper()] for x in subset if x.upper() in DEMO_GROUPS] for item in sublist]
                        
                        agg_by[key] = BASE_GROUP + geog_group + demo_values

        # Also, add the base geographies without any demographic details
        for geog in details['geos']:
            key = f"{geog}_{data_group}".upper()
            if key not in agg_by:
                geog_group = GEOG_GROUPS[geog.upper()]
                demo_group = DEMO_GROUPS[data_group.upper()]
                agg_by[key] = BASE_GROUP + geog_group + demo_group

    # Additional block to add just the base + geography groups
    for geog, group in GEOG_GROUPS.items():
        key = f"{geog}".upper()
        if key not in agg_by:
            agg_by[key] = BASE_GROUP + group

    return agg_by

AGG_BY = generate_groups(report_config)



def group_and_sum(df, group_by_cols):
    """
    
    This function will take in a dataframe, and a list of columns then perform a groupby operation to get the sum of 'Total' for the aggregation level. 


    eg.

    df = 

    |Census Product|Year|MPO|Total|
    +             +    +    +     +
    |ACS1         |2015|MPO1| 100 |
    +             +    +    +     +
    |ACS1         |2015|MPO1| 200 | --------------> group_and_sum(df, ['Census Product', 'Year', 'MPO'])
    +             +    +    +     +
    |ACS5         |2015|MPO2| 300 |
    +             +    +   +      +
    |ACS5         |2015|MPO2| 400 |

    *******after processing********

    |Census Product|Year|MPO|Total|
    +             +    +    +     +
    |ACS1         |2015|MPO1| 300 |
    +             +    +    +     +
    |ACS5         |2015|MPO2| 700 |

    """
    # Filter group by columns that are present in the dataframe
    valid_groupby_cols = [col for col in group_by_cols if col in df.columns]

    # Check if 'Total' column is present
    if 'Total' not in df.columns:
        raise ValueError("The provided dataframe doesn't have a 'Total' column.")

    # Group and sum the total column
    grouped_df = df.groupby(valid_groupby_cols)['Total'].sum()

    return grouped_df

def census_data_aggs(df):

    """
    This function will take in a dataframe and retrieve the range of years, and census products therein to allow for use of a dataframe to determine the fetch_data parameters based on it.


	eg.

    df = 

    |Census Product|Year|MPO|Total|
    +             +    +    +     +
    |ACS1         |2015|MPO1| 100 |
    +             +    +    +     +
    |ACS1         |2015|MPO1| 200 | --------------> census_products, start_year, end_year = census_data_aggs(df)
    +             +    +    +     +
    |ACS5         |2015|MPO2| 300 |
    +             +    +   +      +
    |ACS5         |2020|MPO2| 400 |


	output: 
	
		start_year -> 2015
		end_year -> 2020
		census_products -> ['ACS1', 'ACS5']

    """

    df = input_processing(df)
    census_products = pd.Series(df['Census Product'].unique()).str.lower().tolist()
    years = sorted(df['Year'].unique().tolist())
    # Extract start_year and end_year from the sorted list of years
    start_year = int(years[0])
    end_year = int(years[-1])    
    return census_products, start_year, end_year


### MEDIAN INCOME CALCULATIONS ###



def calculate_weighted_incomes(df, median_income_col, race_group_total_col, geog_agg_col, geog_total_population_col):
    """
    Calculate the weighted incomes for different race groups and geographic levels.
    
    Given a DataFrame and column references, this function computes the weighted income based on
    race group totals and geographic aggregation levels. The function first processes the input DataFrame,
    then calculates two weighted incomes:
    1. Weighted income by race group, calculated as the product of median income and the total population of that race group.
    2. Weighted income by geographic aggregation, calculated as the product of median income and the total population of that geographic level.

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame containing median income, race group totals, and geographic aggregation level details.

    median_income_col : str
        Column name in `df` representing the median income for each group.

    race_group_total_col : str
        Column name in `df` representing the total population for each race group.

    geog_agg_col : str
        The column in `df` used for geographic aggregation.

    geog_total_population_col : str
        Column name in `df` representing the total population for each geographic aggregation unit.

    Returns:
    --------
    pd.DataFrame
        A modified DataFrame containing two new columns:
        1. 'Weighted Income by Race': Weighted income calculated using race group totals.
        2. 'Weighted Income by [geog_agg_col]': Weighted income calculated using geographic aggregation level totals.

    Examples:
    ---------
    >>> data = {
        'Median Income': [50000, 55000, 52000],
        'Race Total': [1000, 800, 1200],
        'City': ['City A', 'City B', 'City C'],
        'City Population': [5000, 4000, 6000]
    }
    >>> df = pd.DataFrame(data)
    >>> calculate_weighted_incomes(df, 'Median Income', 'Race Total', 'City', 'City Population')
    """
    df = input_processing(df)
    df['Weighted Income by Race'] = df[median_income_col] * df[race_group_total_col]
    df[f'Weighted Income by {geog_agg_col}'] = df[median_income_col] * df[geog_total_population_col]
    return df


def income_group_data(df, cols, geog_agg_col, race_group_total_col):
    """
    Aggregate and compute median incomes for racial and geographic groups.

    This function groups the input DataFrame by specified columns and race groups
    to compute aggregated metrics for weighted incomes. Two primary aggregations are made:
    1. Aggregation by race, which computes the median income for each race group.
    2. Aggregation by geographic level, which computes the median income for each geographic aggregation level.

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame containing weighted incomes, race group totals, and geographic aggregation level details.

    cols : list
        List of columns to group by, excluding the 'Race Group' for the racial aggregation.

    geog_agg_col : str
        The column in `df` used for geographic aggregation.

    race_group_total_col : str
        Column name in `df` representing the total population for each race group.

    Returns:
    --------
    tuple of pd.DataFrame
        A tuple containing two DataFrames:
        1. DataFrame aggregated by race, containing columns from `cols`, 'Race Group', 'Weighted Income by Race', and 'Median Income by Race'.
        2. DataFrame aggregated by geographic aggregation level, containing columns from `cols`, f'Weighted Income by {geog_agg_col}', and f'Median Income by {geog_agg_col}'.

    Examples:
    ---------
    >>> data = {
        'Year': [2020, 2020, 2021],
        'Race Group': ['A', 'B', 'A'],
        'Weighted Income by Race': [50000, 60000, 53000],
        'City Population': [1000, 1100, 1020]
    }
    >>> df = pd.DataFrame(data)
    >>> income_group_data(df, ['Year'], 'City', 'City Population')
    """
    grouped_by_race = df.groupby(cols + ['Race Group']).agg({
        'Weighted Income by Race': 'sum',
        race_group_total_col: 'sum'
    }).reset_index()
    grouped_by_race['Median Income by Race'] = grouped_by_race['Weighted Income by Race'] / grouped_by_race[race_group_total_col]
    
    grouped_by_geog = df.groupby(cols).agg({
        f'Weighted Income by {geog_agg_col}': 'sum',
        f'{geog_agg_col} Total Population': 'sum'
    }).reset_index()
    grouped_by_geog[f'Median Income by {geog_agg_col}'] = grouped_by_geog[f'Weighted Income by {geog_agg_col}'] / grouped_by_geog[f'{geog_agg_col} Total Population']
    
    return grouped_by_race, grouped_by_geog


def final_df_compile(grouped_by_race, grouped_by_geog, div_cols, geog_agg_col):
    """
    Merge aggregated racial and geographic median income data and compute income ratio.

    This function takes two DataFrames (grouped by race and geographic level respectively) and merges them
    based on specified division columns. After merging, it computes the income ratio of each race group 
    relative to the geographic aggregation level.

    Parameters:
    -----------
    grouped_by_race : pd.DataFrame
        DataFrame containing aggregated median income data by race group.

    grouped_by_geog : pd.DataFrame
        DataFrame containing aggregated median income data by geographic level.

    div_cols : list
        List of columns on which the two input DataFrames should be merged.

    geog_agg_col : str
        The column representing the geographic aggregation level (e.g., 'City', 'State').

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing merged median incomes by race group and geographic aggregation level,
        along with the computed income ratio for each race group relative to its geographic aggregation level.

    Examples:
    ---------
    >>> race_data = {
        'Year': [2020, 2020],
        'Race Group': ['A', 'B'],
        'Median Income by Race': [50000, 60000]
    }
    >>> geo_data = {
        'Year': [2020, 2020],
        'Median Income by City': [55000, 58000]
    }
    >>> race_df = pd.DataFrame(race_data)
    >>> geo_df = pd.DataFrame(geo_data)
    >>> final_df_compile(race_df, geo_df, ['Year'], 'City')
    """
    median_income_race = input_processing(grouped_by_race)
    median_income_geo = input_processing(grouped_by_geog)
    
    final_df = pd.merge(median_income_race, median_income_geo, on=div_cols)
    final_df[f'Income Ratio Race Group by {geog_agg_col}'] = final_df['Median Income by Race'] / final_df[f'Median Income by {geog_agg_col}'] * 100
    
    return final_df


### FORMATTING ##

def format_agg_ind(agg_ind, geog):
    """
    Format aggregated indicator by removing the geographic component and capitalizing words.
    
    Given an aggregated indicator string (e.g., 'median_income_city'), this function removes
    the geographic component (e.g., 'city') and capitalizes the remaining words, optionally
    adding "by" before the last word if there are multiple components.

    Parameters:
    -----------
    agg_ind : str
        Aggregated indicator string to be formatted.
        
    geog : str
        Geographic component string to be removed from the agg_ind.

    Returns:
    --------
    str
        Formatted aggregated indicator.

    Examples:
    ---------
    >>> format_agg_ind('median_income_city', 'city')
    'MedianIncome'
    
    >>> format_agg_ind('avg_household_size_state', 'state')
    'AvgHouseholdSize'
    """
    components = agg_ind.split('_')
    # Remove the geog component
    components = [comp for comp in components if comp.lower() != geog.lower()]
    components = [comp.capitalize() for comp in components]
    if len(components) > 1:
        components.insert(-1, " by ")
    return "".join(components)


### SAVE REPORTS ###

def save_reports(d, directory_name=None):
    """
    Save dataframes from a dictionary of dictionaries to Excel and CSV files, organized by Census Product.
    
    Parameters:
    -----------
    d : dict
        Dictionary where the outer key is the directory name, and the values are dictionaries. The inner dictionaries 
        should have keys as names for files and values as dataframes to be saved.
    directory_name : str, optional
        Base directory name where the reports will be saved. Defaults to "Census Indicators".
    Returns:
    --------
    None
    Side Effects:
    -------------
    Creates and saves Excel and CSV files in the specified directory within folders named after the main keys and subfolder
    Examples:
    ---------
    >>> data = {
        'race': {
            'county_race_acs1': pd.DataFrame({
                'Census Product': ['ProductA', 'ProductB'],
                'Data': [10, 20]
            })
        }
    }
    >>> save_reports(data, 'Reports_Directory')
    Data saved to Reports_Directory\race\county_race_acs1.xlsx and corresponding CSV files.
    """
    if directory_name is None:
        directory_name = "Census Indicators"
    
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
    for main_key, nested_dict in d.items():
        main_dir = os.path.join(directory_name, main_key)
        # Check if main directory exists, if not, create it
        if not os.path.exists(main_dir):
            os.makedirs(main_dir)
        for dict_key, df in nested_dict.items():
            # Extract subfolder name from the dict key
            key_parts = dict_key.split('_')
            if len(key_parts) < 2:
                print(f"Warning: Key '{dict_key}' does not have an underscore or has only one segment. Skipping...")
                continue
            subfolder_name = key_parts[1]
            subfolder_path = os.path.join(main_dir, subfolder_name)
            # Check if subfolder exists, if not, create it
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)
            excel_filename = os.path.join(subfolder_path, f"{dict_key}.xlsx")
            
            with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
                census_products = df['Census Product'].unique()
                for product in census_products:
                    product_df = df[df['Census Product'] == product]
                    product_df.to_excel(writer, sheet_name=product, index=False)
                    
                    csv_filename = os.path.join(subfolder_path, f"{dict_key}_{product}.csv")
                    product_df.to_csv(csv_filename, index=False)
                
                print(f"Data saved to {excel_filename} and corresponding CSV files.")



def explode_dict(row, valid_variable_names):
    if (row['Variable Name'] in valid_variable_names and 
        isinstance(row['values'], dict) and 
        'item' in row['values'] and 
        isinstance(row['values']['item'], dict)):
        
        return [{'Variable Name': row['Variable Name'],
                 'Values Key': k, 
                 'Values Desc': v, 
                 **row} for k, v in row['values']['item'].items()]
    
    return [row]

def df_explode_dicts(data, var_list):
    df = input_processing(data)
    expanded_data = df.apply(lambda x: explode_dict(x, var_list), axis=1).explode().reset_index(drop=True)
    return pd.DataFrame(expanded_data.tolist())

def append_filtered_dfs(data_dict, column, filter_value):
    """
    Filters dataframes within the nested dictionaries of data_dict on the specified column if it exists,
    appends the filtered dataframe to the main dictionary with the filter_value prefixed to the key.
    
    Args:
    - data_dict (dict): The main dictionary containing nested dictionaries of dataframes.
    - column (str): The column name to filter on.
    - filter_value (str or int): The value to filter the column on.

    Returns:
    - dict: The updated main dictionary with added filtered dataframes nested within the main keys.
    """
    
    # Iterate through main dictionary
    for main_key, nested_dict in data_dict.items():
        temp_dict = {}  # Temporary dictionary to store the new entries
        
        for df_key, df in nested_dict.items():
            # If the specified column exists in the dataframe
            if column in df.columns:
                # Filter the dataframe
                filtered_df = df[df[column] == filter_value]
                # Construct new key
                new_key = f"{filter_value}_{df_key}"
                # Add the filtered dataframe to the temporary dictionary
                temp_dict[new_key] = filtered_df
        
        # Update the nested dictionary with the new entries from the temporary dictionary
        nested_dict.update(temp_dict)
        
        # Update the nested dictionary within the main dictionary
        data_dict[main_key] = nested_dict

    return data_dict



