import pandas as pd
import requests
from tqdm import tqdm
from .mapping import map_county_names

def fetch_data_chunk(variables_chunk, api_key, data_url, state):
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

def get_census_data(df, api_key, data_url, state):
    variables = df['Variable Name']
    variables_chunks = [variables[i:i+50] for i in range(0, len(variables), 50)]
    
    
    
    df_list = []
    for chunk in tqdm(variables_chunks):
        df_chunk = fetch_data_chunk(chunk, api_key, data_url, state)
        df_list.append(df_chunk)
    df_final = pd.concat(df_list, ignore_index=True)
    df_final = map_county_names(df_final)
    return df_final
