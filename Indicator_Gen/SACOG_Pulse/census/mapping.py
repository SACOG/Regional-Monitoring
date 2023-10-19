from typing import Optional, Dict, Union, List
import pandas as pd
import re
import numpy as np
from .helpers import input_processing,extract_content_between_excl
from .configs import *



### MAP COUNTY NAMES ##

def map_county_names(data_input, county_to_mpo: Optional[Dict[str, str]] = None, state: Optional[str] = None) -> pd.DataFrame:
	
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
	df = input_processing(df)
	race_series = df[column_name]
	
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
		return x  # default return value if no match
	
	df['Race Group'] = race_series.apply(map_race)
	return df


### AGE MAPPING ###


def _map_age(age: Union[str, None]) -> Union[str, None]:
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
	df['Age Group'] = df[column_name].apply(_map_age)
	return df


# Compile the regex patterns for each education group
BACHELORS_AND_ABOVE_PATTERN = re.compile(r'graduate degree|bachelor\'s degree|graduate or professional degree', re.IGNORECASE)
SOME_COLLEGE_PATTERN = re.compile(r'some college, no degree|associate\'s degree|some college or associate\'s degree', re.IGNORECASE)
HIGH_SCHOOL_OR_GED_PATTERN = re.compile(r'high school graduate|regular high school diploma|ged or alternative credential|high school graduate, ged, or alternative', re.IGNORECASE)
LESS_THAN_HIGH_SCHOOL_PATTERN = re.compile(r'less than 9th grade|9th to 12th grade, no diploma|less than high school diploma', re.IGNORECASE)

ABOVE_POVERTY_STATUS_PATTERN = re.compile(r'above poverty level', re.IGNORECASE)
BELOW_POVERTY_STATUS_PATTERN = re.compile(r'below poverty level', re.IGNORECASE)

def map_education_level(df: pd.DataFrame, column_name: str) -> pd.DataFrame:

	# Create a new column for 'Education Group' initialized to 'Unknown'
	df['Education Group'] = 'Unknown'
	
	# Use the compiled patterns to map education levels
	df.loc[df[column_name].str.contains(BACHELORS_AND_ABOVE_PATTERN, na=False), 'Education Group'] = 'Bachelors Degree or Higher'
	df.loc[df[column_name].str.contains(SOME_COLLEGE_PATTERN, na=False), 'Education Group'] = 'Some College'
	df.loc[df[column_name].str.contains(HIGH_SCHOOL_OR_GED_PATTERN, na=False), 'Education Group'] = 'High School or GED'
	df.loc[df[column_name].str.contains(LESS_THAN_HIGH_SCHOOL_PATTERN, na=False), 'Education Group'] = 'Less than High School'
	
	return df

### COMMUTE GROUP MAPPING ###

def map_commute_group(df: pd.DataFrame, column_name: str, commute_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
	
	commute_map = commute_map if commute_map else COMMUTE_MAP
	df['Commute Group'] = df[column_name].apply(lambda x: extract_content_between_excl(x, -1)).map(commute_map).fillna('Unknown')
	return df

### MAP PEER MSA ###
def map_peer_msa(df, column_name: str, peer_msa: Optional[List[str]] = None, sacog_msa: Optional[List[str]] = None):

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
	df['Income Group'] = df[column_name].apply(_map_income)
	return df


def _map_age_lpr(age: Union[str, None]) -> Union[str, None]:
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
	pattern = r'(\d{1,2}(?: and \d{1,2} years| to \d{1,2} years| and over| years and over)?)'
	match = re.search(pattern, s)
	return match.group(1) if match else 'Unknown'
	
def map_age_group_labor(data_input, column_name: str):
	df = input_processing(data_input)
	df['Age Group'] = df[column_name].apply(lambda x: _map_age_lpr(get_age(x)))
	return df

def map_poverty_status(data_input, column_name:str):
	df = input_processing(data_input)

	poverty_series = df[column_name]

	poverty_series = poverty_series.apply(lambda x: 'Above Poverty Status' if ABOVE_POVERTY_STATUS_PATTERN.search(x) else x)
	poverty_series = poverty_series.apply(lambda x: 'Below Poverty Status' if BELOW_POVERTY_STATUS_PATTERN.search(x) else x)


	df['Poverty Status'] = poverty_series

	return df
