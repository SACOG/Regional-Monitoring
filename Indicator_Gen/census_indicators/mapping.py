from typing import Optional, Dict, Union
import pandas as pd
import re

# Constant mappings
COUNTY_TO_MPO = {
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

STATE_TO_FIPS = {
    'Alabama': '01',
    'Alaska': '02',
    'Arizona': '04',
    'Arkansas': '05',
    'California': '06',
    'Colorado': '08',
    'Connecticut': '09',
    'Delaware': '10',
    'District of Columbia': '11',
    'Florida': '12',
    'Georgia': '13',
    'Hawaii': '15',
    'Idaho': '16',
    'Illinois': '17',
    'Indiana': '18',
    'Iowa': '19',
    'Kansas': '20',
    'Kentucky': '21',
    'Louisiana': '22',
    'Maine': '23',
    'Maryland': '24',
    'Massachusetts': '25',
    'Michigan': '26',
    'Minnesota': '27',
    'Mississippi': '28',
    'Missouri': '29',
    'Montana': '30',
    'Nebraska': '31',
    'Nevada': '32',
    'New Hampshire': '33',
    'New Jersey': '34',
    'New Mexico': '35',
    'New York': '36',
    'North Carolina': '37',
    'North Dakota': '38',
    'Ohio': '39',
    'Oklahoma': '40',
    'Oregon': '41',
    'Pennsylvania': '42',
    'Rhode Island': '44',
    'South Carolina': '45',
    'South Dakota': '46',
    'Tennessee': '47',
    'Texas': '48',
    'Utah': '49',
    'Vermont': '50',
    'Virginia': '51',
    'Washington': '53',
    'West Virginia': '54',
    'Wisconsin': '55',
    'Wyoming': '56',
    'American Samoa': '60',
    'Guam': '66',
    'Northern Mariana Islands': '69',
    'Puerto Rico': '72',
    'U.S. Minor Outlying Islands': '74',
    'U.S. Virgin Islands': '78'
}

FIPS_TO_STATE = {
    '01': 'Alabama',
    '02': 'Alaska',
    '04': 'Arizona',
    '05': 'Arkansas',
    '06': 'California',
    '08': 'Colorado',
    '09': 'Connecticut',
    '10': 'Delaware',
    '11': 'District of Columbia',
    '12': 'Florida',
    '13': 'Georgia',
    '15': 'Hawaii',
    '16': 'Idaho',
    '17': 'Illinois',
    '18': 'Indiana',
    '19': 'Iowa',
    '20': 'Kansas',
    '21': 'Kentucky',
    '22': 'Louisiana',
    '23': 'Maine',
    '24': 'Maryland',
    '25': 'Massachusetts',
    '26': 'Michigan',
    '27': 'Minnesota',
    '28': 'Mississippi',
    '29': 'Missouri',
    '30': 'Montana',
    '31': 'Nebraska',
    '32': 'Nevada',
    '33': 'New Hampshire',
    '34': 'New Jersey',
    '35': 'New Mexico',
    '36': 'New York',
    '37': 'North Carolina',
    '38': 'North Dakota',
    '39': 'Ohio',
    '40': 'Oklahoma',
    '41': 'Oregon',
    '42': 'Pennsylvania',
    '44': 'Rhode Island',
    '45': 'South Carolina',
    '46': 'South Dakota',
    '47': 'Tennessee',
    '48': 'Texas',
    '49': 'Utah',
    '50': 'Vermont',
    '51': 'Virginia',
    '53': 'Washington',
    '54': 'West Virginia',
    '55': 'Wisconsin',
    '56': 'Wyoming',
    '60': 'American Samoa',
    '66': 'Guam',
    '69': 'Northern Mariana Islands',
    '72': 'Puerto Rico',
    '74': 'U.S. Minor Outlying Islands',
    '78': 'U.S. Virgin Islands'
}



# Load FIPS data only once
FIPS_URL = 'https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt'
FIPS_DF = pd.read_csv(FIPS_URL, header=None, dtype={1: str, 2: str}, names=['state', 'county', 'county_name', 'class_code'])
FIPS_DF.drop(columns=['class_code'], inplace=True)
FIPS_DF.set_index('county', inplace=True)

### COUNTY NAMES MAPPING ###

def map_county_names(df: pd.DataFrame, county_to_mpo: Optional[Dict[str, str]] = None, state: Optional[str] = None) -> pd.DataFrame:
    if 'county' not in df.columns:
        raise ValueError("'county' column not found in DataFrame")

    state = state if state else '06'
    county_to_mpo = county_to_mpo if county_to_mpo else COUNTY_TO_MPO
    fips_filtered = FIPS_DF[FIPS_DF['state'] == state]

    df['County Name'] = df['county'].map(fips_filtered['county_name']).str.replace(" County", "")
    
    fallback_mpo = f"Rest of {FIPS_TO_STATE.get(state, 'Unknown')}"
    df['MPO'] = df['County Name'].map(county_to_mpo).fillna(fallback_mpo)
    
    df['Total'] = df['Total'].astype(int)
    return df


### RACE GROUP MAPPINGS ###

def map_race_group(df: pd.DataFrame, race_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    df['Race Group'] = 'Other (NH)'
    df.loc[df['Race'].str.contains('hispanic|latino', case=False, na=False), 'Race Group'] = 'Hispanic or Latino'
    df.loc[df['Race'].str.contains('asian', case=False, na=False), 'Race Group'] = 'Asian (NH)'
    df.loc[df['Race'].str.contains('two or more races|two races excluding|population of two or more', case=False, na=False), 'Race Group'] = 'Two + Races (NH)'
    df.loc[df['Race'].str.contains('white', case=False, na=False), 'Race Group'] = 'White (Not Hispanic or NH)'
    df.loc[df['Race'].str.contains('black|african american', case=False, na=False), 'Race Group'] = 'Black (NH)'
    return df


### INCOME GROUP MAPPINGS ###

def _map_income(income: Union[str, None]) -> Union[str, None]:
    if income is None:
        return None

    # Remove all non-digit characters
    digits_only = re.findall(r'\d+', income)
    if not digits_only:
        return None

    # Take the minimum of the range as a proxy
    min_income = int(min(digits_only, key=int))
    
    if min_income < 50000:
        return 'LOW = <$50,000'
    elif 50000 <= min_income < 100000:
        return 'MED = $50,000 TO $99,000'
    elif min_income >= 100000:
        return 'HIGH = $100,000 OR MORE'
    else:
        return None


def map_income_group(df: pd.DataFrame) -> pd.DataFrame:
    if 'Income' not in df.columns:
        raise ValueError("Column 'Income' not found.")
    
    df['Income Group'] = df['Income'].apply(_map_income)
    return df

### AGE GROUP MAPPINGS ###

def _map_age(age: Union[str, None]) -> Union[str, None]:
    if age is None:
        return None
    
    # Check if the age is a special non-numeric value like 'Male', 'Female', etc.
    if not re.search(r'\d', age):
        return None

    # Handle individual ages (e.g., '81 years', '15 years')
    match_single = re.search(r'(\d+) years?', age)
    if match_single:
        age_num = int(match_single.group(1))
        if age_num < 18:
            return 'under 18'
        elif 18 <= age_num <= 64:
            return '18 - 64'
        else:
            return '65+'

    # Handle age ranges (e.g., '15 to 19 years', '65 and 66 years')
    match_range = re.search(r'(\d+)[\s\wtoand]+(\d+)', age)
    if match_range:
        start_age, end_age = map(int, (match_range.group(1), match_range.group(2)))

        # Check upper end of the range for categorization
        if end_age < 18:
            return 'under 18'
        elif 18 <= end_age <= 64:
            return '18 - 64'
        else:
            return '65+'

    return None

def map_age_group(df: pd.DataFrame) -> None:
    if 'Age' not in df.columns:
        raise ValueError("Column 'Age' not found.")
    
    df['Age Group'] = df['Age'].apply(_map_age)

    return df


### AGE GROUP MAPPINGS FOR LABOR FORCE PARTICIPATION ###

def _map_age_lpr(age: Union[str, None]) -> Union[str, None]:
    if age is None:
        return None
    
    # Check if the age is a special non-numeric value like 'Male', 'Female', etc.
    if not re.search(r'\d', age):
        return None

    # Handle individual ages (e.g., '81 years', '15 years')
    match_single = re.search(r'(\d+) years?', age)
    if match_single:
        age_num = int(match_single.group(1))
        if age_num < 64:
            return 'under 65'
        else:
            return '65+'

    # Handle age ranges (e.g., '15 to 19 years', '65 and 66 years')
    match_range = re.search(r'(\d+)[\s\wtoand]+(\d+)', age)
    if match_range:
        start_age, end_age = map(int, (match_range.group(1), match_range.group(2)))

        # Check upper end of the range for categorization
        if end_age < 64:
            return 'under 65'
        else:
            return '65+'

    return None

def map_age_group_lpr(df: pd.DataFrame) -> None:
    if 'Age' not in df.columns:
        raise ValueError("Column 'Age' not found.")
    
    df['Age Group'] = df['Age'].apply(_map_age_lpr)

    return df

### COMMUTE GROUP MAPPING ###

def map_commute_group(df: pd.DataFrame) -> pd.DataFrame:
    transport_mapping = {
        "Public transportation (excluding taxicab)": "Transit",
        "Car, truck, or van - carpooled": "Carpool",
        "Car, truck, or van - drove alone": "Drive Alone",
        "Worked from home": "Work at Home",
        "Taxicab, motorcycle, bicycle, or other means": "Other",
        "Walked": "Walked"
    }

    df['Commute Group'] = df['Mode of Commute'].map(transport_mapping).fillna('Unknown')
    
    return df









