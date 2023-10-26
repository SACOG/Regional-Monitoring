import pandas as pd
import re
from typing import Optional, List
from .helpers import *
from .mapping import *


"""
The functions in here process data based on the datagroup/indicator provided. 
"""


def get_default_columns(data_group: str) -> List[str]:
    """
    Retrieve the default columns based on the provided data group.
    
    Parameters:
    - data_group (str): The name of the data group for which the default columns need to be fetched.
    
    Returns:
    - List[str]: A list containing the default column(s) for the specified data group. Returns `['label']` if the data group is not recognized.
    
    Example:
    >>> get_default_columns("race")
    ['label']
    
    >>> get_default_columns("employment")
    ['concept', 'label']
    
    >>> get_default_columns("unknown_data_group")
    ['label']
    """
    default_columns = {
        'race': ['label'],
        'age': ['label'],
        'gender': ['label'],
        'employment': ['concept', 'label'],
        'household income': ['concept', 'label'],
        'education': ['concept', 'label'],
        'poverty': ['concept', 'label'],
        'median income': ['concept', 'label'],
        'broadband': ['concept', 'label'],
        'commute': ['label'],
    }
    return default_columns.get(data_group.lower(), ['label'])

def set_column_defaults(column_names: List[str], data_group: str) -> List[str]:
    """
    Determine the appropriate column names based on the provided column_names and data_group.
    If the provided column_names is empty or incomplete, the function sets defaults based on the data_group.
    
    Parameters:
    - column_names (List[str]): A list containing the column names.
    - data_group (str): The name of the data group for which the columns need to be set.
    
    Returns:
    - List[str]: A list containing the appropriate column names for processing.
    
    Example:
    >>> set_column_defaults([], "race")
    ['label']
    
    >>> set_column_defaults(['label'], "employment")
    ['label', 'concept']
    
    >>> set_column_defaults(['concept'], "race")
    ['concept', 'label']
    
    >>> set_column_defaults(['label', 'concept'], "employment")
    ['label', 'concept']
    """
    default_columns = get_default_columns(data_group)
    
    if not column_names:
        return default_columns
    elif len(column_names) == 1:
        if 'label' in column_names:
            return [column_names[0], 'concept']
        else:
            return [column_names[0], 'label']
    elif 'label' in column_names and column_names[0] == 'label':
        return ['concept', 'label']
    return column_names


def process_race_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process race-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing race data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed race data.
    """
    column_names = set_column_defaults(list(column_names), 'race')
    df = (df
          .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
          .pipe(lambda x: x[x['Race'].str.lower() != 'total'])
          .pipe(map_race_group, 'Race'))
    return df

def process_age_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process age-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing age data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed age data.
    """
    column_names = set_column_defaults(list(column_names), 'age')

    df = (df
          .assign(Age=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
          .pipe(map_age_group))
    return df

def process_gender_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process gender-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing gender data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed gender data.
    """
    column_names = set_column_defaults(list(column_names), 'gender')
    df = df.assign(Gender=lambda x: x[column_names[0]].apply(lambda y: 'Male' if 'Male:' in y else ('Female' if 'Female:' in y else None)))
    return df

def process_employment_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process employment-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing employment data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed employment data.
    """
    column_names = set_column_defaults(list(column_names), 'employment')


    df = df.assign(
        **{"Employment Status": df[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None)}
    ).pipe(map_race_group, column_name=column_names[0]) \
    .pipe(map_age_group_labor, column_name=column_names[1])
    return df

def process_household_income_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process household income-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing household income data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed household income data.
    """
    column_names = set_column_defaults(list(column_names), 'household income')
    
    df = (df
           .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
           .assign(Income=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
           .pipe(lambda x: x[x['Race'].str.lower() != 'total'])
           .pipe(map_race_group, 'Race')
           .pipe(map_income_group, 'Income'))
    return df

def process_education_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process education-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing education data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed education data.
    """
    column_names = set_column_defaults(list(column_names), 'education')


    df = (df
            .pipe(map_race_group, column_name=column_names[0])
            .pipe(map_education_level, column_name=column_names[1]))
    return df

def process_poverty_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process poverty-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing poverty data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed poverty data.
    """
    column_names = set_column_defaults(list(column_names), 'poverty')

    df = (df
        .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
        .assign(Age=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
        .assign(Gender=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -2) if pd.notnull(y) else None))
        .assign(Poverty=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -3) if pd.notnull(y) else None))
        .pipe(map_race_group, 'Race')
        .pipe(map_age_group, 'Age')
        .pipe(map_poverty_status, 'Poverty')
        )
    return df

def process_median_income_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process median income-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing median income data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed median income data.
    """
    column_names = set_column_defaults(list(column_names), 'median income')

    df = (df
        .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
        .pipe(map_race_group, 'Race')
        )
    return df

def process_broadband_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process broadband-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing broadband data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed broadband data.
    """
    column_names = set_column_defaults(list(column_names), 'broadband')

    df = (df
       .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
       .assign(Broadband=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
       .pipe(map_race_group, 'Race')
       )
    return df
        
def process_commute_data(df: pd.DataFrame, *column_names: str) -> pd.DataFrame:
    """
    Process commute-related data from the given DataFrame.
    
    Parameters:
    - df (pd.DataFrame): Input DataFrame containing commute data.
    - *column_names (str): Optional column names for processing. If not provided, defaults will be used.
    
    Returns:
    - pd.DataFrame: DataFrame with processed commute data.
    """
    df = (df
          .assign(Commute=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
          .pipe(map_commute_group, column_name='Commute')
          .query("`Commute Group` != 'Total Commute Trips'")
         )
    
    return df



### PROCESSING DISPATCH MAP ###

processing_dispatch_map = {
        'race': process_race_data,
        'age': process_age_data,
        'gender': process_gender_data,
        'education': process_education_data,
        'employment':process_employment_data,
        'commute':process_commute_data,
        'household income':process_household_income_data,
        'poverty':process_poverty_data,
        'median income':process_median_income_data,
        'broadband':process_broadband_data
        
    }


def process_data_group(data_input, data_group: str, dispatch_map: dict = None, *column_names) -> pd.DataFrame:
    """
    Processes the given data input based on the specified data group and applies the appropriate processing function.
    
    Parameters:
    - data_input: The raw data to be processed. This can be any format, as it will be processed by the 'input_processing' function.
    - data_group (str): The type of data group for which the data needs to be processed, e.g., 'race', 'age', 'gender', etc.
    - dispatch_map (dict): A mapping dictionary where keys are data group names (in lowercase) and values are corresponding processing functions.
    - *column_names: Variable-length argument list of optional column names for processing. If not provided, defaults based on data group will be used.
    
    Returns:
    - pd.DataFrame: A DataFrame with processed data.
    
    Notes:
    - The function first uses 'input_processing' to transform the raw data into a DataFrame.
    - Then, based on the 'data_group', it determines the default columns for processing.
    - The function uses a dispatch map to determine which processing function to call based on the data group.
    - If the specified data group is not in the dispatch map, a warning is printed, and the DataFrame is returned with a 'No Data Group' column.
    """
    df = input_processing(data_input)

    if dispatch_map is None:
        dispatch_map = processing_dispatch_map
    default_columns = get_default_columns(data_group)
    column_names = set_column_defaults(list(column_names), data_group) if column_names else default_columns

    data_group_lower = data_group.lower()

    if data_group_lower in dispatch_map:
        df = dispatch_map[data_group_lower](df, *column_names)
        
        # Checking the geography columns after the data group processing
        lower_columns = [col.lower() for col in df.columns]
        if any(col in lower_columns for col in ['county', 'mpo', 'tract']):
            pass  # Do nothing, just return df as is
        elif 'msa' in lower_columns:
            df = df.pipe(map_peer_msa, 'MSA')
        else:
            print('No valid geography detected. No geog processing was performed.')

    else:
        df['No Data Group'] = df['Variable Name']
        print(f'{data_group} is not a valid data group. No processing was performed.')
    
    return df
