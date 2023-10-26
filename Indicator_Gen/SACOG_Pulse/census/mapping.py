from typing import Optional, Dict, Union, List
import pandas as pd
import re
import numpy as np
from .helpers import input_processing,extract_content_between_excl
from .configs import *



### MAP COUNTY NAMES ##

def map_county_names(data_input, county_to_mpo: Optional[Dict[str, str]] = None, state: Optional[str] = None) -> pd.DataFrame:
    """
    Map county names and Metropolitan Planning Organization (MPO) names based on input data.

    Given a DataFrame that contains county or MSA (Metropolitan Statistical Area) data, this function
    maps the appropriate county and MPO names. If neither 'county' nor 'MSA' columns are present in 
    the data, it raises an error. The mapping relies on constants `COUNTY_TO_MPO` and `FIPS_DF`.

    Parameters:
    -----------
    data_input : DataFrame
        Input dataset containing either 'county' or 'MSA' columns, or both.

    county_to_mpo : dict[str, str], optional
        A dictionary mapping county names to MPO names. 
        If not provided, defaults to `COUNTY_TO_MPO`.

    state : str, optional
        Two-digit FIPS code of the state (e.g., '06' for California). 
        If not provided, defaults to '06' (California).

    Returns:
    --------
    DataFrame
        A DataFrame with mapped 'County Name' and 'MPO' columns based on the input data.

    Raises:
    -------
    ValueError
        If neither 'county' nor 'MSA' columns are found in the input data.

    Notes:
    ------
    - The function uses the helper function `input_processing` to pre-process the input data.
    - The 'County Name' column is derived from the `FIPS_DF` constant.
    - In the absence of a county-to-MPO mapping for a county, it defaults to a "Rest of State" label, 
      where "State" is derived from the `FIPS_TO_STATE` constant.

    Examples:
    ---------
    # Given a dataset 'data_df' containing 'county' data for California:
    >>> mapped_df = map_county_names(data_df)
    # This will return a DataFrame with mapped 'County Name' and 'MPO' columns.

    # Given a dataset 'data_df' containing 'county' data for New York (FIPS code '36'):
    >>> mapped_df = map_county_names(data_df, state='36')
    # This will map based on New York counties.
    """

    
    county_to_mpo = county_to_mpo if county_to_mpo else COUNTY_TO_MPO

    df = input_processing(data_input)

    # If only 'MSA' is present but not 'county', return the dataframe as is
    if 'MSA' in df.columns and 'county' not in df.columns:
        return df

    # If 'county' is present (with or without 'MSA'), map the county names and mpo
    elif 'county' in df.columns:
        state = state if state else '06'
        fips_filtered = FIPS_DF[FIPS_DF['state'] == state]

        df['County Name'] = df['county'].map(fips_filtered['county_name']).str.replace(" County", "")
        fallback_mpo = f"Rest of {FIPS_TO_STATE.get(state, 'Unknown')}"
        df['MPO'] = df['County Name'].map(county_to_mpo).fillna(fallback_mpo)
        
        return df
    else:
        # Neither 'county' nor 'MSA' is present
        raise ValueError("No geography column found in dataframe.")

### RACE MAPPING ###
def map_race_group(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Map race values in the given column of the DataFrame to standardized race group names.

    The function uses pre-defined pattern matching (e.g., `WHITE_PATTERN`, `BLACK_PATTERN`, etc.)
    to map the values in the specified column to a set of standardized race group names. 
    If none of the patterns match, the original value in the column remains unchanged.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing race data in the specified column.

    column_name : str
        Name of the column in the input DataFrame containing the race values to be mapped.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Race Group' column containing the standardized race group names.

    Notes:
    ------
    - The function uses the helper function `input_processing` to pre-process the input data.
    - The specific race patterns (e.g., `WHITE_PATTERN`, `BLACK_PATTERN`, etc.) are expected 
      to be defined elsewhere in the codebase.

    Examples:
    ---------
    >>> df = pd.DataFrame({
    ...     'Race Data': ['White Alone', 'Black', 'Asian/Pacific Islander', 'Hispanic', 'Native American']
    ... })
    >>> mapped_df = map_race_group(df, 'Race Data')
    >>> print(mapped_df['Race Group'])
    0                    White (Not Hispanic or NH)
    1             Black or African American (NH)
    2                            Asian (NH)
    3                      Hispanic or Latino
    4                             Other (NH)
    Name: Race Group, dtype: object
    """

    
    
    # Preprocess input using the helper function if it's available
    try:
        df = input_processing(df)
    except NameError:
        # If the function isn't available, just continue without preprocessing
        pass

    # Check if column_name exists
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' does not exist in the DataFrame.")

    def map_race(x):
        if WHITE_PATTERN.search(x):
            return 'White (Not Hispanic or NH)'
        elif BLACK_PATTERN.search(x):
            return 'Black or African American (NH)'
        elif ASIAN_PATTERN.search(x):
            return 'Asian (NH)'
        elif HISPANIC_PATTERN.search(x):
            return 'Hispanic or Latino'
        elif OTHER_PATTERN.search(x):
            return 'Other (NH)'
        return 'UNMATCHED'

    df['Race Group'] = df[column_name].apply(map_race)
    return df


### AGE MAPPING ###


def _map_age(age: Union[str, None]) -> Union[str, None]:

    """
    Map an age or age range to a standard age group.

    Given an age or an age range string, this function maps it to one of the 
    standard age groups: 'under 18', '18 - 64', or '65+'.

    Parameters:
    -----------
    age : str or None
        An age value or age range in string format. E.g., '17', '20-25'.
        If None, the function also returns None.

    Returns:
    --------
    str or None
        The age group corresponding to the provided age or age range.
        Returns None if the age value does not match any pattern.

    Notes:
    ------
    - This function expects the patterns `single_year_pattern` and `range_years_pattern` 
      to be defined elsewhere in the codebase.
    - The age range is assumed to be provided in the format "start_age-end_age".

    Examples:
    ---------
    >>> _map_age('5')
    'under 18'
    >>> _map_age('25-30')
    '18 - 64'
    >>> _map_age('70')
    '65+'
    """
    if age is None:
    	return None

    # Handle individual ages
    match_single = single_year_pattern.search(age)
    if match_single:
        age_num = int(match_single.group(1))
        if age_num < 18:
            return 'under 18'
        elif 18 <= age_num <= 64:
            return '18 - 64'
        else:
            return '65+'

    # Handle age ranges
    match_range = range_years_pattern.search(age)
    if match_range:
        _, end_age = map(int, match_range.groups())
        if end_age < 18:
            return 'under 18'
        elif 18 <= end_age <= 64:
            return '18 - 64'
        else:
            return '65+'

    return None



def map_age_group(df: pd.DataFrame, column_name: str = 'label') -> pd.DataFrame:
    """
    Map age values in a DataFrame column to standard age groups.

    Applies the `_map_age` function to each value in the specified column 
    and adds a new 'Age Group' column to the DataFrame with the resulting age groups.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing age data in the specified column.

    column_name : str, optional
        Name of the column in the input DataFrame containing the age values to be mapped.
        Default is 'label'.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Age Group' column containing the mapped age groups.

    Notes:
    ------
    - The function relies on the helper function `_map_age` to process individual age values.

    Examples:
    ---------
    >>> df = pd.DataFrame({
    ...     'label': ['5', '25-30', '70']
    ... })
    >>> mapped_df = map_age_group(df, 'label')
    >>> print(mapped_df['Age Group'])
    0    under 18
    1    18 - 64
    2         65+
    Name: Age Group, dtype: object
    """

    if age is None:
        return None

    # Handle individual ages
    match_single = single_year_pattern.search(age)
    if match_single:
        age_num = int(match_single.group(1))
        if age_num < 18:
            return 'under 18'
        elif 18 <= age_num <= 64:
            return '18 - 64'
        else:
            return '65+'

    # Handle age ranges
    match_range = range_years_pattern.search(age)
    if match_range:
        _, end_age = map(int, match_range.groups())
        if end_age < 18:
            return 'under 18'
        elif 18 <= end_age <= 64:
            return '18 - 64'
        else:
            return '65+'

    return None

def map_age_group(df: pd.DataFrame, column_name: str = 'label') -> pd.DataFrame:
    """
    Map age values in a DataFrame column to standard age groups.

    Applies the `_map_age` function to each value in the specified column 
    and adds a new 'Age Group' column to the DataFrame with the resulting age groups.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing age data in the specified column.

    column_name : str, optional
        Name of the column in the input DataFrame containing the age values to be mapped.
        Default is 'label'.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Age Group' column containing the mapped age groups.

    Notes:
    ------
    - The function relies on the helper function `_map_age` to process individual age values.

    Examples:
    ---------
    >>> df = pd.DataFrame({
    ...     'label': ['5', '25-30', '70']
    ... })
    >>> mapped_df = map_age_group(df, 'label')
    >>> print(mapped_df['Age Group'])
    0    under 18
    1    18 - 64
    2         65+
    Name: Age Group, dtype: object
    """

    df['Age Group'] = df[column_name].apply(_map_age)
    return df



def map_education_level(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Map education level values in a DataFrame column to standard education groups.

    Given a DataFrame and the name of a column containing education level descriptions,
    this function maps each description to one of the standard education groups:
    'Bachelors Degree or Higher', 'Some College', 'High School or GED', 
    'Less than High School', or 'Unknown'.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing education level data in the specified column.

    column_name : str
        Name of the column in the input DataFrame containing the education level
        descriptions to be mapped.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Education Group' column containing 
        the mapped education groups.

    Notes:
    ------
    - This function expects the patterns `BACHELORS_AND_ABOVE_PATTERN`, `SOME_COLLEGE_PATTERN`,
      `HIGH_SCHOOL_OR_GED_PATTERN`, and `LESS_THAN_HIGH_SCHOOL_PATTERN` to be defined elsewhere in 
      the codebase.
    - All entries that do not match any pattern are labeled as 'Unknown'.

    Examples:
    ---------
    >>> df = pd.DataFrame({
    ...     'Education Description': ['Bachelor of Science', 'Attended College', 'Passed High School', 'Grade 10']
    ... })
    >>> mapped_df = map_education_level(df, 'Education Description')
    >>> print(mapped_df['Education Group'])
    0    Bachelors Degree or Higher
    1                  Some College
    2            High School or GED
    3         Less than High School
    Name: Education Group, dtype: object
    """
    # Create a new column for 'Education Group' initialized to 'Unknown'
    df['Education Group'] = 'Unknown'
    
    # Use the compiled patterns to map education levels
    df.loc[df[column_name].str.contains(BACHELORS_AND_ABOVE_PATTERN, na=False), 'Education Group'] = 'Bachelors Degree or Higher'
    df.loc[df[column_name].str.contains(SOME_COLLEGE_PATTERN, na=False), 'Education Group'] = 'Some College'
    df.loc[df[column_name].str.contains(HIGH_SCHOOL_OR_GED_PATTERN, na=False), 'Education Group'] = 'High School or GED'
    df.loc[df[column_name].str.contains(LESS_THAN_HIGH_SCHOOL_PATTERN, na=False), 'Education Group'] = 'Less than High School'
    
    return df

### COMMUTE GROUP MAPPING ###

def map_commute_group(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Map commute values in the given column of the DataFrame to standardized commute group names.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing commute data in the specified column.

    column_name : str
        Name of the column in the input DataFrame containing the commute values to be mapped.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Commute Group' column containing the standardized commute group names.
    """
    df = input_processing(df)
    commute_series = df[column_name]
    
    def map_commute(x):
        if DRIVE_ALONE_PATTERN.search(x):
            return 'Drive Alone'
        elif CARPOOL_PATTERN.search(x):
            return 'Carpool'
        elif TRANSIT_PATTERN.search(x):
            return 'Transit'
        elif WORK_HOME_PATTERN.search(x):
            return 'Work at Home'
        elif WALKED_PATTERN.search(x):
            return 'Walked'
        elif BICYCLE_PATTERN.search(x):
            return 'Bicycle'
        elif OTHER_MEANS_PATTERN.search(x):
            return 'Other'
        elif TOTAL_PATTERN.search(x):
            return 'Total Commute Trips'
        return 'UNMATCHED'  # default return value if no match
    
    df['Commute Group'] = commute_series.apply(map_commute)
    return df

### MAP PEER MSA ###
def map_peer_msa(df, column_name: str, peer_msa: Optional[List[str]] = None, sacog_msa: Optional[List[str]] = None):
    """
    Classifies the MSAs in the given DataFrame as either 'Peer MSA', 'Sac Region', or 'NA'.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing MSA names.
        
    column_name : str
        Name of the column in the DataFrame containing MSA names.

    peer_msa : Optional[List[str]]
        List of peer MSA names. Default values are provided if not specified.

    sacog_msa : Optional[List[str]]
        List of SACOG MSA names. Default values are provided if not specified.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Is Peer' column containing the classification ('Peer MSA', 'Sac Region', or 'NA').

    """

    if peer_msa is None:
        peer_msa = [
        'Kansas City, MO-KS Metro Area'
        , 'St. Louis, MO-IL Metro Area'
        , 'Cincinnati, OH-KY-IN Metro Area'
        , 'Cleveland, TN Metro Area'
        , 'Columbus, GA-AL Metro Area'
        , 'Columbus, IN Metro Area'
        , 'Columbus, OH Metro Area']


    

    if sacog_msa is None:
        sacog_msa = ['Sacramento--Arden-Arcade--Roseville, CA Metro Area']
    
    combined_msa = peer_msa + sacog_msa

    df = input_processing(df)

    df['Is Peer'] = np.where(df[column_name].isin(peer_msa), "Peer MSA", 
                                  np.where(df[column_name].isin(sacog_msa), "Sac Region", "NA"))

    return df

def filter_peer_msa(df, column_name: str = None, peer_msa: list = None, sacog_msa: list = None):
    """
    Filters the DataFrame based on specified peer and SACOG MSAs.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing MSA names.

    column_name : str, optional (default = 'MSA')
        Name of the column in the DataFrame containing MSA names.

    peer_msa : list, optional
        List of peer MSA names. Default values are provided if not specified.

    sacog_msa : list, optional
        List of SACOG MSA names. Default values are provided if not specified.

    Returns:
    --------
    DataFrame
        A filtered DataFrame containing only the rows that match the specified peer and SACOG MSAs.

    """

    column_name = column_name if column_name else 'MSA'

    if peer_msa is None:
        peer_msa = [
    'Kansas City, MO-KS Metro Area'
    , 'St. Louis, MO-IL Metro Area'
    , 'Cincinnati, OH-KY-IN Metro Area'
    , 'Cleveland, TN Metro Area'
    , 'Columbus, GA-AL Metro Area'
    , 'Columbus, IN Metro Area'
    , 'Columbus, OH Metro Area']

    if sacog_msa is None:
       sacog_msa = ['Sacramento--Arden-Arcade--Roseville, CA Metro Area']
    
    combined_msa = peer_msa + sacog_msa

    df = input_processing(df)
    mask = df[column_name].isin(combined_msa)
    filtered_df = df[mask]

    return filtered_df

### MAP INCOME GROUPS ###

def _map_income(income: Union[str, None]) -> Union[str, None]:
    """
    Categorizes an income string into a predefined income group.

    Parameters:
    -----------
    income : Union[str, None]
        A string containing the income information. 

    Returns:
    --------
    Union[str, None]
        Returns the categorized income group, or None if income information cannot be categorized.

    Notes:
    ------
    This is a helper function and is intended to be used internally.
    """

    if not isinstance(income, str):  # Ensure that income is a string
        return None

    # Extract all income values as sequences and remove commas
    income_values = [int(value.replace(',', '')) for value in INCOME_PATTERN.findall(income)]
    
    if not income_values:
        return None

    # Get the minimum value
    min_income = min(income_values)

    if min_income < 50000:
        return 'LOW = <$50,000'
    elif 50000 <= min_income < 100000:
        return 'MED = $50,000 TO $99,000'
    elif min_income >= 100000:
        return 'HIGH = $100,000 OR MORE'
    else:
        return None

def map_income_group(df: pd.DataFrame, column_name: str = None) -> pd.DataFrame:
    """
    Maps income information in the DataFrame to predefined income groups.

    Parameters:
    -----------
    df : DataFrame
        Input dataset containing income data.
        
    column_name : str, optional (default = None)
        Name of the column containing the income data to be categorized.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Income Group' column containing the mapped income groups.
    """


    df['Income Group'] = df[column_name].apply(_map_income)
    return df


def _map_age_lpr(age: Union[str, None]) -> Union[str, None]:
    """
    Categorizes an age or age range string into a predefined age group.

    Parameters:
    -----------
    age : Union[str, None]
        A string containing age or age range information.

    Returns:
    --------
    Union[str, None]
        Returns the categorized age group, or None if age information cannot be categorized.

    Notes:
    ------
    This is a helper function and is intended to be used internally.
    """

    if age is None:
        return None
    
    # Use regex to extract single ages or age ranges
    match = re.search(r'(\d+)(?:[\s\wtoand]+(\d+))?', age)
    
    if not match:
        return None  # Return None if no age-related information found
    
    # Extract ages from regex match
    age_start = int(match.group(1))
    age_end = int(match.group(2)) if match.group(2) else age_start

    # Categorize based on the higher age in the range
    return 'under 65' if age_end < 64 else '65+'

def get_age(s: str) -> str:
    """
    Extracts age information from a given string.

    Parameters:
    -----------
    s : str
        Input string containing age-related data.

    Returns:
    --------
    str
        Extracted age or age range string, or 'Unknown' if no age-related information is found.
    """

    pattern = r'(\d{1,2}(?: and \d{1,2} years| to \d{1,2} years| and over| years and over)?)'
    match = re.search(pattern, s)
    return match.group(1) if match else 'Unknown'
    
def map_age_group_labor(data_input, column_name: str):
    """
    Maps age information in the DataFrame to predefined labor age groups.

    Parameters:
    -----------
    data_input : variable type (likely DataFrame)
        Input dataset containing age data for labor purposes.

    column_name : str
        Name of the column containing age data to be categorized.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Age Group' column containing the mapped labor age groups.
    """


    df = input_processing(data_input)
    df['Age Group'] = df[column_name].apply(lambda x: _map_age_lpr(get_age(x)))
    return df

def map_poverty_status(data_input, column_name:str):
    """
    Categorizes poverty status in the DataFrame based on provided patterns.

    Parameters:
    -----------
    data_input : variable type (likely DataFrame)
        Input dataset containing poverty status data.

    column_name : str
        Name of the column containing poverty status data to be categorized.

    Returns:
    --------
    DataFrame
        A DataFrame with an additional 'Poverty Status' column containing the categorized poverty statuses.
    """
    df = input_processing(data_input)

    poverty_series = df[column_name]

    poverty_series = poverty_series.apply(lambda x: 'Above Poverty Status' if ABOVE_POVERTY_STATUS_PATTERN.search(x) else x)
    poverty_series = poverty_series.apply(lambda x: 'Below Poverty Status' if BELOW_POVERTY_STATUS_PATTERN.search(x) else x)


    df['Poverty Status'] = poverty_series

    return df
