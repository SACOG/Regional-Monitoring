def print2(): print(); print()


'''

Functions:

get_data()
read_inputs_file()
read_vars_file()
moe_split()
prep_request_special()
get_acs()
get_pums()
get_dp()
get_subject()
get_dec()
get_lehd()
get_data_any()


'''





import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import functools as ft
import json
import requests
from IPython.display import display


PATH_GIT = Path(__file__).parent.parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'BLS'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BLS')

FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_CONFIG = PATH_CONFIG / 'bls.xlsx'



# Prep ---------------------------------------------------------------------------------------------------------------------------------------------------------------


def read_area(indicator, survey):
    df = pd.read_excel(FILE_CONFIG, sheet_name='area_codes', dtype={'County FIPS':str, 'MSA_ID':str})
    df = df[df['Survey'] == survey]
    df = df[df['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
    df = df[df['Include'] == 'Yes']
    df['area_text'] = df['area_text'].str.strip()
    return df

def read_industries(indicator, survey):
    df = pd.read_excel(FILE_CONFIG, sheet_name='industry_codes', dtype={'industry_code':str})
    df = df[df['Survey'] == survey]
    df = df[df['Include'] == 'Yes']
    df = df[df['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
    return df

def read_datatypes(survey):
    df = pd.read_excel(FILE_CONFIG, sheet_name='datatype_codes', dtype=str)
    df = df[df['Survey'].str.contains(survey)]
    df['data_type_text'] = df['data_type_text'].str.lower()
    return df

def read_sizes(survey):
    df = pd.read_excel(FILE_CONFIG, sheet_name='size_codes', dtype=str)
    df = df[df['Survey'].str.contains(survey)]
    df['size_code_text'] = df['size_code_text'].str.lower()
    return df

def read_owners(survey):
    df = pd.read_excel(FILE_CONFIG, sheet_name='owner_codes', dtype=str)
    df = df[df['Survey'].str.contains(survey)]
    df['owner_code_text'] = df['owner_code_text'].str.lower()
    return df

def read_measures(survey):
    df = pd.read_excel(FILE_CONFIG, sheet_name='measure_codes', dtype=str)
    df = df[df['Survey'].str.contains(survey)]
    df['measure_type_text'] = df['measure_type_text'].str.lower()
    return df


def construct_series_id(survey, geography, seasonal, df=None, list_sectors=None, data_type=None, size_code=None, owner_code=None, measure_code=None):

    
    """
    User defined function to organize Series ID's into structure that the BLS API can understand https://www.bls.gov/developers/api_signature_v2.htm
    Using the workbook "BLS Configuration File.xlsx", we create a dictionary of all Series ID's and what years we want to request data for.  The
    structure of the Series ID depends on the survey we want data from https://www.bls.gov/help/hlpforma.htm#EN.
    """

    keys = []
    vals = []

    if geography == 'Counties':
        
        # Loop through each County code
        # Construct the Series ID
        # Add Series ID and County label to lists
        
        for i in range(len(df)):
            area_code = str(df.loc[i, 'area_code'])
            if survey in ['LA']:
                series_id = [str(survey) + str(seasonal) + str(area_code)  + str(measure_code)]
            if survey in ['EN']:
                series_id =  list(map(lambda sector: str(survey) + str(seasonal) + str(area_code) + str(data_type) + str(size_code) + str(owner_code) + str(sector), list_sectors))
            keys.append(str(df.loc[i, 'area_text']))
            vals.append(series_id)

    if geography == 'MSA':
        
        # Loop through each MSA code
        # Construct the Series ID
        # Add Series ID and MSA label to lists
        
        for i in range(len(df)):
            
            area_code = str(df.loc[i, 'area_code'])
            if survey in ['LA']:
                series_id = [str(survey) + str(seasonal) + str(area_code)  + str(measure_code)]
            if survey in ['EN']:
                series_id =  list(map(lambda sector: str(survey) + str(seasonal) + str(area_code) + str(data_type) + str(size_code) + str(owner_code) + str(sector), list_sectors))
            if survey in ['SM', 'CE']:
                state     = str(df.loc[i, 'State FIPS'])
                series_id = list(map(lambda sector: str(survey) + str(seasonal) + str(state) + str(area_code) + str(sector) + str(data_type), list_sectors))
            keys.append(str(df.loc[i, 'area_text']))
            vals.append(series_id)
        
    if geography == 'National':

        # Pull National level area code
        # Construct the Series ID
        # Add Series ID and National label to lists

        if survey in ['LA']:
                series_id = str(survey) + str(seasonal) + str(area_code)  + str(measure_code)
        if survey in ['SM', 'CE']:
            series_id = list(map(lambda sector: str(survey) + str(seasonal) + str(sector) + str(data_type), list_sectors))
        keys.append('National')
        vals.append(series_id)


    # Convert list of keys and values to dictionary
    result = {k: v for k, v in zip(keys, vals)}
    
    return result

        


def create_series_dictionary(dt_params, yaml_bls):

    print('Bureau of Labor Statistics importing parameters:')
    print()


    print()
    print('Series ID construction for API request:')
    print()

    indicator         = dt_params['Indicator'    ]
    survey            = dt_params['Survey'       ]
    geography         = dt_params['Geography'    ]
    seasonal_code     = dt_params['Seasonal Code']
    data_type_text    = dt_params['Data Type'    ]
    size_code_text    = dt_params['Size Code'    ]
    owner_code_text   = dt_params['Owner Code'   ]
    measure_type_text = dt_params['Measure Type' ]

    state_code     = yaml_bls['Surveys'][survey]['state_code'    ]
    area_code      = yaml_bls['Surveys'][survey]['area_code'     ]
    industry_code  = yaml_bls['Surveys'][survey]['industry_code' ]
    data_type_code = yaml_bls['Surveys'][survey]['data_type_code']
    size_code      = yaml_bls['Surveys'][survey]['size_code'     ]
    owner_code     = yaml_bls['Surveys'][survey]['owner_code'    ]
    measure_code   = yaml_bls['Surveys'][survey]['measure_code'  ]

    dt_series = {}

    print('Survey prefix: ' + survey)
    print()

    print('Seasonal code: ' + seasonal_code)
        
    if area_code:
        df_area = read_area(indicator, survey)
        if geography == 'MSA':
            df_area = df_area[df_area['area_type_code'] == 'B']
            if state_code:
                file_area = PATH_CONFIG0 / 'area_codes.xlsx'
                df_states = pd.read_excel(file_area, sheet_name='MSAcodes', dtype={'State FIPS':str, 'MSA_ID':str})
                df_states = df_states[['MSA_ID', 'State FIPS', 'MSA']].drop_duplicates()
                df_area['MSA_ID'] = df_area['MSA_ID'].astype(str)
                df_area = df_area.merge(df_states, on = 'MSA_ID', how = 'left')
                df_area = df_area[['State FIPS', 'area_code', 'area_text', 'MSA', 'MSA_ID']]
            else:
                df_area = df_area[['area_code', 'area_text', 'MSA_ID']]
        if geography == 'Counties':
            df_area = df_area[df_area['area_type_code'] == 'F']
            if state_code:
                file_area = PATH_CONFIG0 / 'area_codes.xlsx'
                df_states = pd.read_excel(file_area, sheet_name = 'CountyFIPS', dtype = {'State FIPS':str, 'County FIPS':str})
                df_states = df_states[['County FIPS', 'State FIPS', 'County Name']].drop_duplicates()
                df_area = df_area.merge(df_states, on = 'County FIPS', how = 'left')
                df_area = df_area[['State FIPS', 'area_code', 'area_text', 'County Name']]
            else: 
                df_area = df_area[['area_code', 'area_text']]
        df_area = df_area.reset_index(drop=True)
        print('Area codes table: ')
        display(df_area.head())

    if industry_code:
        df_industries = read_industries(indicator, survey)
        list_sectors = list(df_industries['industry_code'].values)
        list_sectors = [str(sector) for sector in list_sectors]
        print('Industry codes: ')
        print(list_sectors)
    if data_type_code:
        df_datatypes = read_datatypes(survey)
        data_type_text_sub = data_type_text.lower()
        df_datatypes = df_datatypes[df_datatypes['data_type_text'] == data_type_text_sub]
        data_type_code = df_datatypes['data_type_code'].values[0]
        print('Data type code: ' + data_type_code)
    if size_code:
        df_sizes = read_sizes(survey)
        size_code_text_sub = size_code_text.lower()
        df_sizes = df_sizes[df_sizes['size_code_text'] == size_code_text_sub]
        size_code = df_sizes['size_code'].values[0]
        print('Employer size code: ' + data_type_code)
    if owner_code:
        df_owners = read_owners(survey)
        owner_code_text_sub = owner_code_text.lower()
        df_owners = df_owners[df_owners['owner_code_text'] == owner_code_text_sub]
        owner_code = df_owners['owner_code'].values[0]
        print('Ownership type code: ' + owner_code)
    if measure_code:
        df_measures = read_measures(survey)
        measure_type_text_sub = measure_type_text.lower()
        df_measures = df_measures[df_measures['measure_type_text'] == measure_type_text_sub]
        measure_code = df_measures['measure_code'].values[0]
        print('Measure code: ' + measure_code)

    print()
    print('Series IDs organized by geography: ')
    print()

    if survey == 'SM':
        dt_series = construct_series_id(survey         = survey
                                        , geography    = geography
                                        , seasonal     = seasonal_code
                                        , df           = df_area
                                        , list_sectors = list_sectors
                                        , data_type    = data_type_code)
    if survey == 'CE':
        dt_series = construct_series_id(survey         = survey
                                        , geography    = geography
                                        , seasonal     = seasonal_code
                                        , list_sectors = list_sectors
                                        , data_type    = data_type_code)
    if survey == 'EN':
        dt_series = construct_series_id(survey         = survey
                                        , geography    = geography
                                        , seasonal     = seasonal_code
                                        , df           = df_area
                                        , data_type    = data_type_code
                                        , size_code    = size_code
                                        , owner_code   = owner_code
                                        , list_sectors = list_sectors)
    if survey == 'LA':
        dt_series = construct_series_id(survey         = survey
                                        , geography    = geography
                                        , seasonal     = seasonal_code
                                        , df           = df_area
                                        , measure_code = measure_code)
    display(dt_series)


    print()
    print('Geography to Series ID mapping table: ')
    print()

    df_series_area = pd.melt(
        pd.DataFrame.from_dict(dt_series)
        , var_name = 'area_text'
        , value_name = 'seriesID'
    )
    df_series_area = df_series_area.drop_duplicates().reset_index(drop=True)
        
    if survey in ['SM', 'LA']:
        if geography == 'MSA':
            area_id = 'MSA_ID'
        if geography == 'Counties':
            area_id = 'County FIPS'
        df_series_area = df_series_area.merge(df_area[['area_text', 'area_code', area_id]], on='area_text')
    if survey == 'SM':
        df_series_area['industry_code'] = df_series_area['seriesID'].str[10:18]
        df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on='industry_code', how='left')
    if survey == 'CE':
        df_series_area['industry_code'] = df_series_area['seriesID'].str[3:11]
        df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on='industry_code', how='left')
        df_series_area['area_code'] = '000000'

    df_series_area = df_series_area.drop_duplicates().reset_index(drop=True)
    display(df_series_area.head())

    print()
    print('Series ID groupings for API request (50 at a time): ')
    print()

    list_series_all = []
    for i in dt_series.keys():
        list_series_all.extend(dt_series[i])

    list_series_all = [list_series_all[x:x+50] for x in range(0, len(list_series_all), 50)]
    display(list_series_all)


    return list_series_all, df_series_area, dt_series










# Get -------------------------------------------------------------------------------------------------------------------------------------------------------------------------



def get_data_any(api_key, dt_params, yaml_bls):

    ## Keep track of time amounted while requesting data
    start_time = time.time()

    year_start = np.min(dt_params['Years'])
    year_end   = np.max(dt_params['Years'])

    list_series_all, df_series_area, dt_series = create_series_dictionary(dt_params, yaml_bls)

    print('Importing BLS data using user inputs...')
    print2()

    list_df_years = []
    year_step = 20


    # Loop through the specified range of years in step intervals
    for year_range_start in range(year_start, year_end + 1, year_step):
        year_range_end = min(year_range_start + year_step - 1, year_end)
        print()
        print('Requesting data from ' + str(year_range_start) + ' to ' + str(year_range_end))

        list_df_series = []

        # Iterate through 50 Series ID at a time

        for list_series in list_series_all:

            list_df = []

            # Set up BLS API request
            url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
            url_key = '?registrationkey={}'.format(api_key)
            headers = {'Content-type': 'application/json'}

            data = json.dumps({"seriesid": list_series,"startyear": int(year_range_start),"endyear": int(year_range_end),"registrationkey": api_key})

            # API request
            response = requests.post('{}{}'.format(url, url_key), headers=headers, data=data).json()

            # Translate information from dictionary results into pandas dataframe
            for i in tqdm(list_series):
                try:
                    df = pd.DataFrame.from_dict(response['Results']['series'])
                    df = pd.DataFrame.from_dict(df[df['seriesID'] == i]['data'].values[0])
                    df = df[['year', 'periodName', 'value']]
                    df = df.rename(columns = {'value': i})
                    list_df.append(df)
                except Exception as e: print(i); print(e)

            # Combine all column df's together for each set of 50 Series ID's
            df_series = ft.reduce(lambda left, right: pd.merge(left, right, on = ['year', 'periodName'], how = 'left'), list_df)
            list_df_series.append(df_series)

        # Combine all sets of 50 series ID df's
        df_years = ft.reduce(lambda left, right: pd.merge(left, right, on = ['year', 'periodName'], how = 'left'), list_df_series)
        list_df_years.append(df_years)

    # Combine all data from all years together
    df_bls = pd.concat(list_df_years)
    df_bls = df_bls.drop_duplicates()
    df_bls = df_bls.reset_index(drop = True)


    ## Calculate time amounted while requesting data
    print()
    print("Finished!!")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
    print()


    ## Summary of data quality
    print()
    print('Summary of data quality: ')
    print()
    print("Count of '-555555555'   values in dataframe: " + str((df_bls.values == '-555555555'  ).sum()))
    print("Count of '-666666666'   values in dataframe: " + str((df_bls.values == '-666666666'  ).sum()))
    print("Count of '-222222222'   values in dataframe: " + str((df_bls.values == '-222222222'  ).sum()))
    print("Count of '-999999999.0' values in dataframe: " + str((df_bls.values == '-999999999.0').sum()))
    print("Count of 'null'         values in dataframe: " + str((df_bls.values == 'null'        ).sum()))
    print("Count of '-'            values in dataframe: " + str((df_bls.values == '-'           ).sum()))
    print("Count of ''             values in dataframe: " + str((df_bls.values == ''            ).sum()))
    print("Count of NaN            values in dataframe: " + str(df_bls.isna().sum()              .sum()))
    print()


    ## View result
    print()
    print('Number of rows/columns: ')
    print(df_bls.shape)
    display(df_bls)

    return df_bls