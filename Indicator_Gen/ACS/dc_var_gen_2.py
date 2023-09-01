import pandas as pd
import re
from typing import Optional, List, Dict, Union


### MAP COUNTY NAMES ###


def map_county_names(df: pd.DataFrame, county_to_mpo: Optional[Dict[str, str]] = None, state: str = 'CA') -> pd.DataFrame:
    """
    Maps county numbers to county names and MPOs.

    Parameters:
        df : pd.DataFrame
            The input DataFrame with a 'county' column.
        county_to_mpo : dict, optional
            A dictionary mapping county names to MPO names.
        state : str
            The state for which county data should be filtered.

    Returns:
        pd.DataFrame : The DataFrame with mapped county names and MPOs.
    """

    if 'county' not in df.columns:
        raise ValueError("'county' column not found in DataFrame")

    if county_to_mpo is None:
        county_to_mpo = {
    'Alameda': 'MTC',
    'Contra Costa': 'MTC',
    'El Dorado': 'SACOG',
    'Fresno': 'SJ VALLEY',
    'Imperial': 'SCAG',
    'Kern': 'SJ VALLEY',
    'Kings': 'SJ VALLEY',
    'Los Angeles': 'SCAG',
    'Madera': 'SJ VALLEY',
    'Marin': 'MTC',
    'Merced': 'SJ VALLEY',
    'Napa': 'MTC',
    'Orange': 'SCAG',
    'Placer': 'SACOG',
    'Riverside': 'SCAG',
    'Sacramento': 'SACOG',
    'San Bernardino': 'SCAG',
    'San Diego': 'SANDAG',
    'San Francisco': 'MTC',
    'San Joaquin': 'SJ VALLEY',
    'San Mateo': 'MTC',
    'Santa Clara': 'MTC',
    'Solano': 'MTC',
    'Sonoma': 'MTC',
    'Stanislaus': 'SJ VALLEY',
    'Sutter': 'SACOG',
    'Ventura': 'SCAG',
    'Yolo': 'SACOG',
    'Yuba': 'SACOG'
    }

    fips_df = pd.read_csv('https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt',
                          header=None,
                          dtype={1: str, 2: str},
                          names=['state', 'county', 'county_name', 'class_code'])

    fips_df = fips_df[fips_df['state'] == state]
    fips_df.drop(columns=['state', 'class_code'], inplace=True)
    fips_df.set_index('county', inplace=True)

    df['County Name'] = df['county'].map(fips_df['county_name'])
    df['County Name'] = df['County Name'].str.replace(" County", "")
    df['MPO'] = df['County Name'].map(county_to_mpo)
    df['MPO'].fillna('Rest of CA', inplace=True)
    df['Total'] = df['Total'].astype(int)

    return df

## RACE MAPPING FUNCTION ##

def map_race_df(df: pd.DataFrame, race_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Maps the values in the 'Race' column based on conditions.
    
    Parameters:
        df: DataFrame to be transformed
        race_mapping: Dictionary used for mapping race values

    Returns:
        DataFrame with the 'Race' column values mapped to 'Race Group'
    """
    
    # Initialize a new column for the mapping result
    df['Race Group'] = 'Other (NH)'
    
    # Mapping conditions
    df.loc[df['Race'].str.contains('hispanic|latino', case=False, na=False), 'Race Group'] = 'Hispanic or Latino'
    df.loc[df['Race'].str.contains('asian', case=False, na=False), 'Race Group'] = 'Asian (NH)'
    df.loc[df['Race'].str.contains('two or more races|two races excluding|population of two or more', case=False, na=False), 'Race Group'] = 'Two + Races (NH)'
    df.loc[df['Race'].str.contains('white', case=False, na=False), 'Race Group'] = 'White (Not Hispanic or NH)'
    df.loc[df['Race'].str.contains('black|african american', case=False, na=False), 'Race Group'] = 'Black (NH)'
    
    # Print out the original and mapped values
    print("Original 'Race' value : Mapped 'Race Group' value")
    for _, row in df.iterrows():
        print(f"{row['Race']} : {row['Race Group']}")
    
    return df

## VARIABLE INPUT FUNCTION ##

def read_csv_or_get_input(df: Optional[pd.DataFrame], csv_path: Optional[str]) -> Union[pd.DataFrame, None, List[str]]:
    """Helper function to read DataFrame from a CSV file or get user input for a variable list."""
    variable_list = None
    
    if df is None and csv_path:
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            print(f"File {csv_path} not found.")
            return None
    
    if df is None:
        try:
            user_input = input("Please enter a list of variables separated by a comma, semi-colon, or pipe: ")
            # Use re.split to split by multiple delimiters
            variable_list = re.split(r'[;|,]\s*', user_input.strip())
            return variable_list
        except Exception as e:
            print(f"Exception occurred: {e}")
            print("Not running in Jupyter Notebook. Please provide either df or csv_path.")
            return None
    
    return df

## PROCESS DATA GROUP FUNCTION ##

def process_data_group(df: pd.DataFrame, data_group: str) -> pd.DataFrame:
    """Process DataFrame based on the given data group."""
    if data_group.lower() == 'race':
        df['Race'] = df['label'].apply(lambda x: x.split('!!')[-1] if pd.notnull(x) else None)
    elif data_group.lower() == 'age':
        df['Age'] = df['label'].apply(lambda x: x.split('!!')[-1] if pd.notnull(x) and ('Male' in x or 'Female' in x) else (x.split('!!')[-1] if any(str(i).isdigit() for i in x.split('!!')[-1]) else None) if pd.notnull(x) else None)
    elif data_group.lower() == 'gender':
        df['Gender'] = df['label'].apply(lambda x: 'Male' if 'Male' in x else ('Female' if 'Female' in x else None) if pd.notnull(x) else None)
    elif data_group.lower() == 'household income by race':
        # Extracting Race from 'concept'
        df['Race'] = df['concept'].apply(lambda x: x.split('(')[-1].split(')')[0].replace(' HOUSEHOLDER', '') if pd.notnull(x) else None)
        # Extracting Income from 'label'
        df['Income'] = df['label'].apply(lambda x: re.sub('[^0-9a-zA-Z,$-]', '', x.split('!!')[-1]) if 'Estimate!!Total:!!' in x else None if pd.notnull(x) else None)
    else:
        df['No Data Group'] = df['Variable Name']
    
    return df


## VARIABLE DF GENERATION FUNCTION ##

def dc_var_gen(df: Optional[pd.DataFrame] = None, 
               csv_path: Optional[str] = None, 
               data_group: Optional[str] = None, 
               variable_list: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    
    if variable_list is None:
        try:
            user_input = input("Please enter a list of variables separated by a comma, semi-colon, or pipe: ")
            variable_list = re.split(r'[;|,]\s*', user_input.strip())
        except Exception as e:
            print(f"Exception occurred: {e}")
            return None
    
    if df is None and csv_path:
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            print(f"File {csv_path} not found.")
            return None

    if df is None:
        print("DataFrame could not be created. Exiting.")
        return None

    if variable_list:
        df = df[df['Variable Name'].isin(variable_list)]
        
    if data_group:
        df = process_data_group(df, data_group)
        
    df = map_race_df(df)
    
    return df
