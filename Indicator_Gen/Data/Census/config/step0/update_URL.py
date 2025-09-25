
print(); print(); print()



export=True



# Workspace ------------------------------------------------------------------------------------------------------

import pandas as pd
from pathlib import Path
from IPython.display import display
import urllib.request, json
import sys


path_git = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'Census'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'
path_csv = path_config / 'step0' / 'csv'



def list_combine(l):
    return "/".join(l)


# API key
file_api = path_config / 'api_key.txt'
with open(file_api, 'r') as file:
    api_key = file.read()





# Main ------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':


    with urllib.request.urlopen("https://api.census.gov/data.json") as url:
        dict_acs = json.load(url)

    # Convert information from dictionary format to pandas dataframe
    # Clean certain columns, fill na, ...
    # Combine multiple columns to make one url field
    # Import old URL mapping table and join old assignments

    df_url2 = pd.DataFrame.from_dict(dict_acs['dataset'])
    df_url2 = df_url2[['title', 'c_vintage', 'c_dataset']]
    df_url2['c_dataset'] = df_url2['c_dataset'].apply(list_combine)
    df_url2['c_vintage'] = df_url2['c_vintage'].fillna(0.0).astype(int).replace(0, pd.NA)
    df_url2['c_url'] = 'https://api.census.gov/data' + '/' + df_url2['c_vintage'].astype(str) + '/' + df_url2['c_dataset']
    df_url2 = df_url2.sort_values(['c_dataset', 'c_vintage'], ascending = [True, False])

    file_config = path_config / 'census.xlsx'
    df_url1 = pd.read_excel(file_config, sheet_name='URL')

    df_url = df_url2.merge(df_url1, on = ['title', 'c_vintage', 'c_dataset', 'c_url'], how='left')
    df_url = df_url.sort_values(['c_dataset', 'c_vintage'], ascending=[True, False])

    print('URL table: ')
    display(df_url)

    if export:
        file_csv = path_csv / 'census_url.csv'
        df_url.to_csv(file_csv, index=False)



