import pandas as pd
import pickle
from .configs import *
from .helpers import input_processing
from .get_raw_vars import raw_vars

# Constants for mapping
VAR_MAPPING = {
    'race': {
        'ACS1': acs1_race_vars,
        'ACS5': acs5_race_vars,
        'DEC': {
            2000: dec00_race_vars,
            2010: dec10_race_vars,
            2020: dec20_race_vars
        }
    },
    'age': {
        'ACS1': acs1_age_vars,
        'ACS5': acs5_age_vars,
        'DEC': {
            2000: dec00_age_vars,
            2010: dec10_age_vars,
            2020: dec20_age_vars
        }
    },

    'household income': {
        'ACS1': acs1_income_vars,
        'ACS5': acs5_income_vars
    },

    'median income': {
        'ACS1': acs1_median_income_vars,
        'ACS5': acs5_median_income_vars
    },
    'education': {
        'ACS1': acs1_education_vars,
        'ACS5': acs5_education_vars
    },

    'employment': {
        'ACS1': acs1_employment_vars,
        'ACS5': acs5_employment_vars
    },

    'commute': {
        'ACS1': acs1_commute_vars,
        'ACS1_2005': acs1_2005_commute_vars,
        'ACS5': acs5_commute_vars
    },

    'poverty':{
        'ACS1': poverty_status_vars,
        'ACS5': poverty_status_vars
    },

    'broadband':{
    'ACS1': acs1_broadband_vars,
    'ACS5': acs1_broadband_vars
    }
}


def extract_lists_from_dict(d):
    """Recursively extracts lists from dictionary and its nested dictionaries."""
    result = []
    for value in d.values():
        if isinstance(value, list):
            result.extend(value)
        elif isinstance(value, dict):
            result.extend(extract_lists_from_dict(value))
    return result

def master_raw_vars(d, v=None):
    var_map = v if v else VAR_MAPPING
    f = extract_lists_from_dict(var_map)
    df = input_processing(d)
    return df[df['Variable Name'].isin(f)]


with open('all_raw_vars.pkl', 'rb') as file:
    all_raw_vars = pickle.load(file)
    

master_vars = master_raw_vars(all_raw_vars)

def acs1_05(data, data_group):
    df = input_processing(data)
    if data_group == 'commute':
        
        # Ensure the 'Year' column is of integer type
        df['Year'] = df['Year'].astype(int)
        
        # Isolate rows where Year is 2005 and Census Product is ACS1
        df_5 = df[(df['Year'] == 2005) & (df['Census Product'] == 'ACS1')]
        df_5_p = df_5[df_5['Variable Name'].isin(acs1_2005_commute_vars)]
        
        # Get all the other rows using the index
        df_a = df.drop(df_5.index)
        df_a_p = df_a[df_a['Variable Name'].isin(acs1_commute_vars + acs5_commute_vars)]
        final = pd.concat([df_5_p, df_a_p])
        
    return final

def filter_vars(raw_vars, data_group=None):
    """
    Filter a dataframe of raw variables based on predefined variable mapping.
    
    Given a dataframe of raw Census variables, this function filters and organizes the data based on 
    the `VAR_MAPPING` constant. It processes data either for a specific data group (if provided) 
    or for all data groups in the mapping. The results are categorized by Census Product, year 
    (for DEC product), and data group.

    Parameters:
    -----------
    raw_vars : pandas.DataFrame
        Dataframe containing raw Census variables, expected to have columns 'Census Product', 'Year', 
        and 'Variable Name'.
    
    data_group : str, optional
        Specific data group to process, e.g., 'race', 'age'. If not provided, all groups in 
        `VAR_MAPPING` will be processed.

    Returns:
    --------
    dict
        Dictionary containing filtered variables organized by Census Product, year (if applicable),
        and data group. The dictionary keys follow the format "Product_Year_DataGroup_filtered_vars"
        or "Product_DataGroup_filtered_vars", and the values are filtered dataframes.

    Examples:
    ---------
    >>> raw_data = pd.DataFrame({
        'Census Product': ['ACS1', 'DEC', 'DEC'],
        'Year': [None, 2000, 2010],
        'Variable Name': ['var1', 'var2', 'var3']
    })
    >>> filter_vars(raw_data, 'race')
    # Expected output will depend on the `VAR_MAPPING` constant and the variable lists like 
    # `acs1_race_vars` and so on.
    """
    df = input_processing(raw_vars)
    filtered_results = {}
    
    # If data_group is 'commute', process it uniquely and return
    if data_group == 'commute':
        df_commute = acs1_05(df, 'commute')
        key_name = "ACS1_commute_filtered_vars"
        filtered_results[key_name] = df_commute
        return filtered_results

    # Determine which data groups need to be processed
    data_groups_to_process = [data_group] if data_group else list(set(VAR_MAPPING.keys()) - {'commute'})

    for dg in data_groups_to_process:
        for product, vars_list in VAR_MAPPING[dg].items():
            if product in df['Census Product'].unique():
                df_product = df[df['Census Product'] == product]  # Filter the dataframe by the current Census Product

                if product == 'DEC':
                    for year, group in df_product.groupby('Year'):
                        # Convert year to integer
                        int_year = int(year)

                        variables_for_year = vars_list.get(int_year, [])
                        if variables_for_year:  # Only process if there are variables for the year
                            key_name = f"{product}{int_year}_{dg}_filtered_vars"  # Key format
                            filtered_results[key_name] = group[group['Variable Name'].isin(variables_for_year)]
                else:
                    key_name = f"{product}_{dg}_filtered_vars"  # Key format
                    filtered_results[key_name] = df_product[df_product['Variable Name'].isin(vars_list)]
    return filtered_results



def get_filtered_vars(data_group):
    return lambda data_input: filter_vars(raw_vars, data_group)


