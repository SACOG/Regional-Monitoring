import re
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Union
import itertools
import logging
from .configs import report_config

### DATA PROCESSING HELPER FUNCTIONS ###

def fill_missing_values(df: pd.DataFrame, ref_col: str = 'Variable Name') -> pd.DataFrame:
    
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
    # Ensure we're working with a DataFrame
    if isinstance(data_input, pd.DataFrame):
        df = data_input
    elif isinstance(data_input, dict):
        df = pd.concat(data_input.values(), ignore_index=True)
    else:
        logging.error("Invalid input type. Must be a dictionary or a dataframe.")

    return fill_missing_values(df)



def clean_labels(df):
    """Helper function to remove colons from label column."""
    return df.assign(label=df['label'].str.replace(':', ''))

def extract_content_between_excl(text: str, position: int = -1) -> Optional[str]:
    """Extract content between the specified set of exclamation marks."""
    matches = re.findall('!!([^!]+)', text)
    if matches:
        return matches[position] if (0 <= position < len(matches)) or (position < 0 and abs(position) <= len(matches)) else None
    return None

### CENSUS MERGE ###


def census_merge(resulting_data, filtered_vars):
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
    'METRO': ['MSA']
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
    Group the dataframe by given columns and sum the 'Total' column.
    """
    # Filter group by columns that are present in the dataframe
    valid_groupby_cols = [col for col in group_by_cols if col in df.columns]

    # Check if 'Total' column is present
    if 'Total' not in df.columns:
        raise ValueError("The provided dataframe doesn't have a 'Total' column.")

    # Group and sum the total column
    grouped_df = df.groupby(valid_groupby_cols)['Total'].sum()

    return grouped_df


def extract_content_between_parentheses(text: str, position: int = -1) -> Optional[str]:
    """Extract content between the specified set of parentheses."""
    matches = re.findall(r'\(([^)]+)\)', text)
    return matches[position] if 0 <= position < len(matches) or position == -1 and matches else None


### MEDIAN INCOME CALCULATIONS ###

def census_data_aggs(df):
    df = input_processing(df)
    census_products = pd.Series(df['Census Product'].unique()).str.lower().tolist()
    years = sorted(df['Year'].unique().tolist())
    # Extract start_year and end_year from the sorted list of years
    start_year = int(years[0])
    end_year = int(years[-1])    
    return census_products, start_year, end_year

def calculate_weighted_incomes(df, median_income_col, race_group_total_col, geog_agg_col, geog_total_population_col):
    df = input_processing(df)
    df['Weighted Income by Race'] = df[median_income_col] * df[race_group_total_col]
    df[f'Weighted Income by {geog_agg_col}'] = df[median_income_col] * df[geog_total_population_col]
    return df

def income_group_data(df, cols, geog_agg_col, race_group_total_col):
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
    
    median_income_race = input_processing(grouped_by_race)
    median_income_geo = input_processing(grouped_by_geog)
    
    final_df = pd.merge(median_income_race, median_income_geo, on=div_cols)
    final_df[f'Income Ratio Race Group by {geog_agg_col})'] = final_df['Median Income by Race'] / final_df[f'Median Income by {geog_agg_col}']*100
    
    return final_df


### FORMATTING ##

def format_agg_ind(agg_ind, geog):
    components = agg_ind.split('_')
    # Remove the geog component
    components = [comp for comp in components if comp.lower() != geog.lower()]
    components = [comp.capitalize() for comp in components]
    if len(components) > 1:
        components.insert(-1, "by")
    return "".join(components)

### SAVE REPORTS ###

def save_reports(dict):
    
    # Iterate over dictionary items
    for dict_key, df in dict.items():
        
        # Create an Excel filename using the dict_key
        excel_filename = f"{dict_key}.xlsx"
        
        # Create a writer object to write to Excel file
        with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
            
            # Get unique Census Products from the dataframe
            census_products = df['Census Product'].unique()
            
            for product in census_products:
                # Filter dataframe for the current Census Product
                product_df = df[df['Census Product'] == product]
                
                # Write filtered dataframe to a sheet in Excel file named after the Census Product
                product_df.to_excel(writer, sheet_name=product, index=False)
                
                # Save the filtered dataframe to a CSV file named after the dict key and Census Product
                csv_filename = f"{dict_key}_{product}.csv"
                product_df.to_csv(csv_filename, index=False)
            
            print(f"Data saved to {excel_filename} and corresponding CSV files.")
