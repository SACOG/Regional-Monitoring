import pandas as pd
from .configs import *
from .helpers import input_processing 

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

    data_groups_to_process = [data_group] if data_group else VAR_MAPPING.keys()

    for dg in data_groups_to_process:
        for product, vars_list in VAR_MAPPING[dg].items():
            if product in df['Census Product'].unique():
                if product == 'DEC':
                    dec_df = df[df['Census Product'] == 'DEC']
                    for year, group in dec_df.groupby('Year'):
                        # Convert year to integer
                        int_year = int(year)

                        variables_for_year = vars_list.get(int_year, [])
                        if variables_for_year:  # Only process if there are variables for the year
                            key_name = f"{product}{int_year}_{dg}_filtered_vars"  # Key format
                            filtered_results[key_name] = group[group['Variable Name'].isin(variables_for_year)]
                else:
                    key_name = f"{product}_{dg}_filtered_vars"  # Key format
                    filtered_results[key_name] = df[df['Variable Name'].isin(vars_list)]

    return filtered_results



def get_filtered_vars(data_group):
    return lambda data_input: filter_vars(raw_vars, data_group)


