import pandas as pd
import requests
from .mapping import map_county_names
from .helpers import input_processing

def display_progress_bar(current_step, total_steps, bar_length=50):
	progress = (current_step/total_steps)
	arrow = '-' * int(round(progress * bar_length) - 1) + '>'
	spaces = ' ' * (bar_length - len(arrow))
	print('\rProgress: [{0}] {1}%'.format(arrow + spaces, int(round(progress * 100))), end='')

def fetch_data_chunk_for_metro(variables_chunk, api_key, data_url, state):
	params = {
		'get': 'NAME,' + ','.join(variables_chunk),
		'for': 'metropolitan statistical area/micropolitan statistical area:*',
		'key': api_key,
	}
	response = requests.get(data_url, params=params)
	
	if response.status_code != 200:
		print(f"API call failed with status code {response.status_code}. Message: {response.text}")
		return None
	
	header, *data = response.json()
	df = pd.DataFrame(data, columns=header)
	df_melted = df.melt(id_vars=['NAME','metropolitan statistical area/micropolitan statistical area'], 
						value_vars=variables_chunk, 
						var_name='Variable Name', 
						value_name='Total')
	df_melted = df_melted.rename(columns = {"NAME": "MSA"})
	return df_melted

def fetch_data_chunk_for_county(variables_chunk, api_key, data_url, state):
	params = {
		'get': ','.join(variables_chunk),
		'for': 'county:*',
		'in': f'state:{state}',
		'key': api_key,
	}
	response = requests.get(data_url, params=params)
	
	if response.status_code != 200:
		print(f"API call failed with status code {response.status_code}. Message: {response.text}")
		return None
	
	header, *data = response.json()
	df = pd.DataFrame(data, columns=header)
	df_melted = df.melt(id_vars=['state', 'county'], 
						value_vars=variables_chunk, 
						var_name='Variable Name', 
						value_name='Total')
	return df_melted

def fetch_data_chunk_for_tract(variables_chunk, api_key, data_url, state):
	params = {
		'get': ','.join(variables_chunk),
		'for': 'tract:*',
		'in': f'state:{state}',
		'key': api_key,
	}

	response = requests.get(data_url, params=params)	
	if response.status_code != 200:
		print(f"API call failed with status code {response.status_code}. Message: {response.text}")
		return None
	
	header, *data = response.json()
	df = pd.DataFrame(data, columns=header)
	df_melted = df.melt(id_vars=['state', 'county', 'tract'], 
						value_vars=variables_chunk, 
						var_name='Variable Name', 
						value_name='Total')
	return df_melted

def get_census_data(df, api_key, data_url, state, fetch_data_chunk_function):
	variables = df['Variable Name']
	# Subtract 3 to account for NAME, state, and county
	variables_chunks = [variables[i:i+40] for i in range(0, len(variables), 40)]
	
	df_list = []
	for chunk in variables_chunks:
		df_chunk = fetch_data_chunk_function(chunk, api_key, data_url, state)
		df_list.append(df_chunk)

	df_final = pd.concat(df_list, ignore_index=True)
	return df_final

def get_census_mappings(df):
	return {
		'ACS1': ('https://api.census.gov/data/{}/acs/acs1', df[df['Census Product'] == 'ACS1']),
		'ACS5': ('https://api.census.gov/data/{}/acs/acs5', df[df['Census Product'] == 'ACS5']),
		'DEC':  ({
			2000: 'https://api.census.gov/data/{}/dec/sf1',
			2010: 'https://api.census.gov/data/{}/dec/sf1',
			2020: 'https://api.census.gov/data/{}/dec/dp'
		}, df[df['Census Product'] == 'DEC'])
	}

def process_each_product(product, url_map, product_df, state, api_key, total_years, current_year_number, fetch_data_chunk_function):
	dataframes_dict = {}
	unique_years = product_df['Year'].unique()
	for year in unique_years:
		constructed_data_url = (url_map[year] if isinstance(url_map, dict) else url_map).format(year)
		try:
			output_df = get_census_data(product_df[product_df['Year'] == year], api_key, constructed_data_url, state, fetch_data_chunk_function)
			output_df = update_output_dataframe(output_df, year, product)
			key = f"{year}_{product}_Census_Data"
			dataframes_dict[key] = output_df
		except Exception as e:
			print(f"Error fetching data for year {year} with URL {constructed_data_url}: {e}")
		
		current_year_number += 1
		display_progress_bar(current_year_number, total_years)

	return dataframes_dict

def update_output_dataframe(output_df, year, product):
	output_df['Year'] = year
	output_df['Census Product'] = product
	return output_df

def fetch_census_data_for_all_products(data_input, state, api_key, fetch_func, geography):
	df = input_processing(data_input)
	census_mappings = get_census_mappings(df)
	
	total_years = sum([len(product_df['Year'].unique()) for _, (_, product_df) in census_mappings.items()])
	current_year_number = 0
	all_dataframes_dict = {}
	
	for product, (url_map, product_df) in census_mappings.items():
		if not product_df.empty:  # Check if there's data left to process
			if product == 'DEC':  # Handle 'DEC' differently since it has a dictionary for URLs
				for year in product_df['Year'].unique():
					if year not in url_map:  # Skip if the year's URL is not in the mapping
						continue
					year_df = product_df[product_df['Year'] == year]
					dataframes_dict = process_each_product(product, url_map[year], year_df, state, api_key, total_years, current_year_number, fetch_func)
					all_dataframes_dict.update(dataframes_dict)
					current_year_number += 1
			else:
				dataframes_dict = process_each_product(product, url_map, product_df, state, api_key, total_years, current_year_number, fetch_func)
				all_dataframes_dict.update(dataframes_dict)
				current_year_number += len(product_df['Year'].unique())
	
	return all_dataframes_dict

def main_fetching_process(data_input, state, api_key, geography:str):
	
	data_input = input_processing(data_input)

	geo = geography.lower()
	fetch_funcs = {
		'county': fetch_data_chunk_for_county,
		'mpo': fetch_data_chunk_for_county,
		'tract': fetch_data_chunk_for_tract,
		'msa': fetch_data_chunk_for_metro
	}
	

	if geo == 'tract':
		data_input = data_input[data_input['Census Product'] != 'ACS1']
	elif geo == 'msa':
		data_input = data_input[data_input['Census Product'] != 'DEC']
	
	fetch_func = fetch_funcs.get(geo)
	if fetch_func is None:
		raise ValueError("Invalid geography specified.")

	return fetch_census_data_for_all_products(data_input, state, api_key, fetch_func, geography)


executed_geos = set()

def fetch_data_chunk_for_geography(data_input, state, api_key, geo):
	data_input = input_processing(data_input)
	if geo in executed_geos:
		return  # Already fetched for this geography, no need to refetch
	
	data = main_fetching_process(data_input, state, api_key, geo)
	
	if geo in ['county', 'mpo']:
		executed_geos.add('county')
		executed_geos.add('mpo')
	else:
		executed_geos.add(geo)

	return data

def fetch_and_concatenate_data(data_input, state, api_key, geos_list):
	data_input = input_processing(data_input)
	results = {}
	for geo in geos_list:
		data_for_geo = fetch_data_chunk_for_geography(data_input, state, api_key, geo)
		
		# In case we are fetching for 'county' or 'mpo', store the data under both keys
		if geo == 'county':
			results['county'] = data_for_geo
			results['mpo'] = data_for_geo
		elif geo == 'mpo':
			results['mpo'] = data_for_geo
			results['county'] = data_for_geo
		else:
			results[geo] = data_for_geo

	return results