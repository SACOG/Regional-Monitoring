



# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
from pathlib import Path
from tqdm import tqdm
from IPython.display import display
import urllib.request
import json
import sys

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent/'config'))
import help

sys.path.append(str(Path(__file__).parent.parent))
import get

PATH_GIT = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_CSV = PATH_CONFIG / 'step0' / 'csv'

FILE_API = PATH_CONFIG / 'api_key.txt'


def import_dec_vars(year, sample):
    with urllib.request.urlopen(f"https://api.census.gov/data/{year}/dec/{sample}/variables.json") as url:
        dt = json.load(url)
    df = pd.DataFrame.from_dict(dt['variables']).T.reset_index().rename(columns = {'index':'ID'})
    df = df[['ID', 'label', 'concept', 'predicateType', 'group']]
    df['Year'] = year
    df['estimate'] = sample
    df = df.sort_values(['ID'])
    display(df.head())
    return df



# API key
with open(FILE_API, 'r') as file:
    api_key = file.read()




# Main ------------------------------------------------------------------------------------------------------------------------------------------------------




EXPORT=True



ACS=False
PUMS=False
SUBJECT=True
DP=False
DEC=False
LEHD=False
CPS=False


END_YEAR=2024






if __name__ == '__main__':
    
    print('\n'*2)



    if ACS:

        print('\n'*2)
        print('ACS ------------------------------------------------------------------------------------------------------------------------')
        print('\n'*2)

        ## ACS5 ---
        ## Organize list of all variables from all years into one nice table
        # Set which years to import
        # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
        # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

        years_to_import = [2020]
        list_df = []

        for year in tqdm(years_to_import):
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/variables.json") as url:
                dict_acs = json.load(url)
            
            df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
            df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
            df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
            df_vars['Year'] = year

            list_df.append(df_vars)

        df_acs5 = pd.concat(list_df)
        df_acs5 = df_acs5.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
        df_acs5 = df_acs5.reset_index(drop=True)



        ## ACS1 ---
        ## Organize list of all variables from all years into one nice table
        # Set which years to import
        # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
        # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

        years_to_import = help.sequence(2005, END_YEAR, 1)
        years_to_import.remove(2020)
        list_df = []

        for year in tqdm(years_to_import):
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/variables.json") as url:
                dict_acs = json.load(url)
            
            df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
            df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
            df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
            df_vars['Year'] = year

            list_df.append(df_vars)

        df_acs1 = pd.concat(list_df)
        df_acs1 = df_acs1.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
        df_acs1 = df_acs1.reset_index(drop=True)


        ## Combine all ACS variables
        df_acs1 = df_acs1[df_acs1['Year'] != 2020]
        df_acs5 = df_acs5[df_acs5['Year'] == 2020]

        df_acs = pd.concat([df_acs1, df_acs5])
        df_acs = df_acs.sort_values(['Table', 'Year', 'ID'], ascending = [True, False, True])
        df_acs = df_acs.rename(columns={'attributes':'Attributes', 'label':'Label', 'concept':'Table Name'})
        df_acs = df_acs.reset_index(drop=True)

        df_acs['ID_Attributes'] = df_acs['ID'] + ',' + df_acs['Attributes']
        df_acs['ID_Attributes'] = df_acs['ID_Attributes'].apply(get.moe_split)

        display(df_acs.head())


        file_acs = PATH_CONFIG / 'census.xlsx'; sheet_name='ACS'
        df_config = pd.read_excel(file_acs, sheet_name=sheet_name)
        df_config = df_config[['Year', 'ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity', 'ID2', 'ID_Attributes2']]

        df_acs1 = df_acs[df_acs['Year'] == df_acs['Year'].max()]
        df_acs2 = df_acs[df_acs['Year']  < df_acs['Year'].max()]

        df_acs1 = df_acs1.merge(df_config[df_config['Year'] == df_config['Year'].max()].drop('Year', axis=1), on=['ID'], how='left')
        df_acs2 = df_acs2.merge(df_config, on=['Year', 'ID'], how='left')

        df_acs = pd.concat([df_acs1, df_acs2])

        df_acs = df_acs[['Table', 'ID', 'Attributes', 'Label', 'Table Name', 'Year', 'Indicator Name', 'Include', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes', 'ID2', 'ID_Attributes2']]
        df_acs = df_acs.drop_duplicates()
        df_acs = df_acs.sort_values(['Table', 'Indicator Name', 'Year', 'ID'], ascending = [True, True, False, True])
        df_acs = df_acs.reset_index(drop=True)

        display(df_acs.head())

        if EXPORT:
            df_acs.to_csv(PATH_CSV / 'ACS.csv', index=False)





    if PUMS:

        print('\n'*2)
        print('PUMS ------------------------------------------------------------------------------------------------------------------------')
        print('\n'*2)


        ## PUMS1 ---
        # initialize empty list to store data frames
        # iterate through each year
            # pull PUMS variables list from json file found on ACS website
            # convert to dictionary
            # convert to pandas data frame
            # apply year tag
            # append to list
        # concatenate all data frames together

        print('\n'*2)
        print('Importing PUMS variables tables by year...'); print()

        years = help.sequence(2005, END_YEAR, 1)
        years.remove(2020)
        list_df_pums = []


        for year in tqdm(years):

            try:
                with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/pums/variables.json") as url:
            
                    dict_pums = json.load(url)
            
                    df_pums = pd.DataFrame.from_dict(dict_pums['variables']).T.reset_index().rename(columns = {'index':'ID'})
                    df_pums['Year'] = year
                    list_df_pums.append(df_pums)
            except Exception as e: print(e)
            
        df_pums = pd.concat(list_df_pums)
        df_pums = df_pums.dropna(subset=["values"]).reset_index(drop=True)
        print(df_pums.shape)
        display(df_pums.head())



        # create empty list to store data frames
        # iterate through each year
            # create empty list to store data frames
            # subset all variables to year
                # create empty list to store data frames
                    # subset pums variables to one ID at a time
                    # iterate through all key/value combinations in dictionaries that represent the value mappings to make pandas data frames 
                    # store them in list of data frames
                # concatenate specific ID variable mappings together
                # add some labels, clean column names
            # apply year tag
            # convert to pandas data frame
            # store in list of data frames

        # concatenate all data frames together

        print('\n'*2)
        print('Cleaned PUMS variables table:'); print()

        list_df_years = []

        for year in tqdm(years):
            try:
                df_pums_vars = df_pums[df_pums['Year'] == year]
                
                list_df = []
                
                for ID in df_pums_vars['ID'].values:
                    
                    df_ID = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop=True)
                    
                    for key in list(df_ID['values'][0].keys()):

                        if key == 'item':
                            dict_values = {
                                            'Value1'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                        , 'Value2'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                        , 'Description': list(list(df_ID['values'].values)[0]['item'].values())
                                        }
                            df_vars = pd.DataFrame(dict_values)
                            
                        if key == 'range':
                            
                            list_range = []
                
                            for value in df_ID['values'][0]['range']:
                                dict_values = {
                                                'Value1'     : [value['min']]
                                            , 'Value2'     : [value['max']]
                                            , 'Description': [value['description']]
                                            }
                                
                                list_range.append(pd.DataFrame(dict_values))
                                
                            df_vars = pd.concat(list_range)
                            
                        df_vars['ID'] = ID
                        df_vars['Label'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop=True)['label'].values[0]
                        df_vars['Suggested Weight'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop=True)['suggested-weight'].values[0]
                
                        df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]
                
                    list_df.append(df_vars)
                
                df_pums_vars = pd.concat(list_df)
                df_pums_vars['Year'] = year
                
                list_df_years.append(df_pums_vars)
            except Exception as e: print(e)

        df_pums1 = pd.concat(list_df_years)
        df_pums1 = df_pums1.sort_values(['ID', 'Value1', 'Year'], ascending = [True, True, False])
        df_pums1 = df_pums1.reset_index(drop=True)
        display(df_pums1.head())



        ## PUMS5 ---
        # initialize empty list to store data frames
        # iterate through each year
            # pull PUMS variables list from json file found on ACS website
            # convert to dictionary
            # convert to pandas data frame
            # apply year tag
            # append to list
        # concatenate all data frames together

        print('\n'*2)
        print('Importing PUMS variables tables by year...'); print()

        years = help.sequence(2020, 2020, 1)
        list_df_pums = []

        for year in tqdm(years):

            try:
                with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/pums/variables.json") as url:
            
                    dict_pums = json.load(url)
            
                    df_pums = pd.DataFrame.from_dict(dict_pums['variables']).T.reset_index().rename(columns = {'index':'ID'})
                    df_pums['Year'] = year
                    list_df_pums.append(df_pums)
            except Exception as e: print(e)
            
        df_pums = pd.concat(list_df_pums)
        df_pums = df_pums.dropna(subset=["values"]).reset_index(drop=True)
        print(df_pums.shape)
        display(df_pums.head())



        # create empty list to store data frames
        # iterate through each year
            # create empty list to store data frames
            # subset all variables to year
                # create empty list to store data frames
                    # subset pums variables to one ID at a time
                    # iterate through all key/value combinations in dictionaries that represent the value mappings to make pandas data frames 
                    # store them in list of data frames
                # concatenate specific ID variable mappings together
                # add some labels, clean column names
            # apply year tag
            # convert to pandas data frame
            # store in list of data frames

        # concatenate all data frames together

        print('\n'*2)
        print('Cleaned PUMS variables table:'); print()

        list_df_years = []

        for year in tqdm(years):
            try:
                df_pums_vars = df_pums[df_pums['Year'] == year]
                
                list_df = []
                
                for ID in df_pums_vars['ID'].values:
                    
                    df_ID = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop=True)
                    
                    for key in list(df_ID['values'][0].keys()):

                        if key == 'item':
                            dict_values = {
                                            'Value1'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                            , 'Value2'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
                                            , 'Description': list(list(df_ID['values'].values)[0]['item'].values())
                                        }
                            df_vars = pd.DataFrame(dict_values)
                            
                        if key == 'range':
                            
                            list_range = []
                
                            for value in df_ID['values'][0]['range']:
                                dict_values = {
                                                'Value1'   : [value['min']]
                                            , 'Value2'     : [value['max']]
                                            , 'Description': [value['description']]
                                            }
                                
                                list_range.append(pd.DataFrame(dict_values))
                                
                            df_vars = pd.concat(list_range)
                            
                        df_vars['ID'] = ID
                        df_vars['Label'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop=True)['label'].values[0]
                        df_vars['Suggested Weight'] = df_pums_vars[df_pums_vars['ID'] == ID].reset_index(drop=True)['suggested-weight'].values[0]
                
                        df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]
                
                    list_df.append(df_vars)
                
                df_pums_vars = pd.concat(list_df)
                df_pums_vars['Year'] = year
                
                list_df_years.append(df_pums_vars)
            except Exception as e: print(e)

        df_pums5 = pd.concat(list_df_years)
        df_pums5 = df_pums5.sort_values(['ID', 'Value1', 'Year'], ascending = [True, True, False])
        df_pums5 = df_pums5.reset_index(drop=True)



        # Combining

        df_pums1 = df_pums1[df_pums1['Year'] != 2020]
        df_pums5 = df_pums5[df_pums5['Year'] == 2020]

        df_pums = pd.concat([df_pums1, df_pums5])
        df_pums = df_pums.drop_duplicates()
        df_pums['Value1'] = df_pums['Value1'].astype('str')
        df_pums = df_pums.sort_values(['Year', 'ID', 'Value1'], ascending = [False, True, True])
        df_pums = df_pums.reset_index(drop=True)


        file_config = PATH_CONFIG / 'census.xlsx'; sheet_name='PUMS'
        df_config = pd.read_excel(file_config, sheet_name=sheet_name, dtype={'Value1':'str'})
        df_config = df_config[['ID', 'Value1', 'Indicator Name', 'Include', 'ID2', 'Description2', 'Data Type', 'Table Type']]

        df_pums = df_pums.merge(df_config, on=['ID', 'Value1'], how='left')
        df_pums = df_pums.drop_duplicates()
        df_pums = df_pums.set_index('Year').reset_index()
        display(df_pums.head())

        if EXPORT:
            df_pums.to_csv(PATH_CSV / 'PUMS.csv', index=False)






    if SUBJECT:
            
        print('\n'*2)
        print('SUBJECT ------------------------------------------------------------------------------------------------------------------------')
        print('\n'*2)

        ## ACS5 ---
        ## Organize list of all variables from all years into one nice table
        # Set which years to import
        # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
        # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

        years_to_import = [2020]
        list_df = []

        for year in tqdm(years_to_import):
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/subject/variables.json") as url:
                dict_acs = json.load(url)
            
            df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
            df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
            df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
            df_vars['Year'] = year

            list_df.append(df_vars)

        df_acs5 = pd.concat(list_df)
        df_acs5 = df_acs5.sort_values(['Year', 'ID'], ascending = [False, True])
        df_acs5 = df_acs5.reset_index(drop=True)
        print(df_acs5.shape)
        display(df_acs5.head())



        ## ACS1 ---
        ## Organize list of all variables from all years into one nice table
        # Set which years to import
        # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
        # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

        years_to_import = help.sequence(2010, END_YEAR, 1)
        years_to_import.remove(2020)
        list_df = []

        for year in tqdm(years_to_import):
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/subject/variables.json") as url:
                dict_acs = json.load(url)
            
            df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
            df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
            df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
            df_vars['Year'] = year

            list_df.append(df_vars)

        df_acs1 = pd.concat(list_df)
        df_acs1 = df_acs1.sort_values(['Year', 'ID'], ascending = [False, True])
        df_acs1 = df_acs1.reset_index(drop=True)
        print(df_acs1.shape)
        display(df_acs1.head())



        # Combining

        df_acs1 = df_acs1[df_acs1['Year'] != 2020]
        df_acs5 = df_acs5[df_acs5['Year'] == 2020]

        df_acs = pd.concat([df_acs1, df_acs5])
        df_acs = df_acs.sort_values(['Year', 'ID'], ascending = [False, True])
        df_acs = df_acs.rename(columns={'attributes':'Attributes', 'label':'Label', 'concept':'Table Name'})
        df_acs = df_acs.reset_index(drop=True)

        df_acs['ID_Attributes'] = df_acs['ID'] + ',' + df_acs['Attributes']
        df_acs['ID_Attributes'] = df_acs['ID_Attributes'].apply(get.moe_split)

        display(df_acs.head())

        file_config = PATH_CONFIG / 'census.xlsx'; sheet_name='SUBJECT'
        df_config = pd.read_excel(file_config, sheet_name=sheet_name)
        df_config = df_config[['Year', 'ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes2', 'ID2']]

        df_acs1 = df_acs[df_acs['Year'] == df_acs['Year'].max()]
        df_acs2 = df_acs[df_acs['Year']  < df_acs['Year'].max()]

        df_acs1 = df_acs1.merge(df_config[df_config['Year'] == df_config['Year'].max()].drop('Year', axis=1), on=['ID'], how='left')
        df_acs2 = df_acs2.merge(df_config, on=['Year', 'ID'], how='left')

        df_acs = pd.concat([df_acs1, df_acs2])

        df_acs = df_acs[['Table', 'ID', 'Attributes', 'Label', 'Table Name', 'Year', 'Indicator Name', 'Include', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes']]
        df_acs = df_acs.drop_duplicates()
        df_acs = df_acs.sort_values(['Table', 'Year', 'ID'], ascending = [True, False, True])
        df_acs = df_acs.reset_index(drop=True)
        

        display(df_acs.head())


        if EXPORT:
            df_acs.to_csv(PATH_CSV / 'SUBJECT.csv', index=False)








    if DP:

        print('\n'*2)
        print('DP ------------------------------------------------------------------------------------------------------------------------')
        print('\n'*2)

        ## ACS5 ---
        ## Organize list of all variables from all years into one nice table
        # Set which years to import
        # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
        # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

        years_to_import = help.sequence(2020, 2020, 1)
        list_df = []

        for year in tqdm(years_to_import):
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs5/profile/variables.json") as url:
                dict_acs = json.load(url)
            
            df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
            df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
            df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
            df_vars['Year'] = year

            list_df.append(df_vars)

        df_acs5 = pd.concat(list_df)
        df_acs5 = df_acs5.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
        df_acs5 = df_acs5.reset_index(drop=True)



        ## ACS1 ---
        ## Organize list of all variables from all years into one nice table
        # Set which years to import
        # Use urllib package to make request to Census API (requesting for table of all variables sampled on the given year)
        # Do some cleaning, reshaping, etc... to make nice for use in data pipelines

        years_to_import = help.sequence(2005, END_YEAR, 1)
        # years_to_import = help.sequence(2019, 2021, 1)
        years_to_import.remove(2020)
        list_df = []

        for year in tqdm(years_to_import):
            with urllib.request.urlopen(f"https://api.census.gov/data/{year}/acs/acs1/profile/variables.json") as url:
                dict_acs = json.load(url)
            
            df_vars = pd.DataFrame.from_dict(dict_acs['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
            df_vars = df_vars[['group', 'ID', 'attributes', 'label', 'concept']].rename(columns = {'group':'Table'})
            df_vars['Label_clean'] = df_vars['label'].str.replace('Estimate!!', '')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace('!!', ' ')
            df_vars['Label_clean'] = df_vars['Label_clean'].str.replace(':', '')
            df_vars['Year'] = year

            list_df.append(df_vars)

        df_acs1 = pd.concat(list_df)
        df_acs1 = df_acs1.sort_values(['Year', 'Table', 'ID'], ascending = [False, True, True])
        df_acs1 = df_acs1.reset_index(drop=True)


        ## Combine all ACS variables
        df_acs1 = df_acs1[df_acs1['Year'] != 2020]
        df_acs5 = df_acs5[df_acs5['Year'] == 2020]

        df_acs = pd.concat([df_acs1, df_acs5])
        df_acs = df_acs.sort_values(['Table', 'Year', 'ID'], ascending = [True, False, True])
        df_acs = df_acs.rename(columns={'attributes':'Attributes', 'label':'Label', 'concept':'Table Name'})
        df_acs = df_acs.reset_index(drop=True)

        df_acs['ID_Attributes'] = df_acs['ID'] + ',' + df_acs['Attributes']
        df_acs['ID_Attributes'] = df_acs['ID_Attributes'].apply(get.moe_split)

        display(df_acs.head())


        file_acs = PATH_CONFIG / 'census.xlsx'; sheet_name='ACS'
        df_config = pd.read_excel(file_acs, sheet_name=sheet_name)
        df_config = df_config[['Year', 'ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes2', 'ID2']]

        df_acs1 = df_acs[df_acs['Year'] == df_acs['Year'].max()]
        df_acs2 = df_acs[df_acs['Year']  < df_acs['Year'].max()]

        df_acs1 = df_acs1.merge(df_config[df_config['Year'] == df_config['Year'].max()].drop('Year', axis=1), on=['ID'], how='left')
        df_acs2 = df_acs2.merge(df_config, on=['Year', 'ID'], how='left')

        df_acs = pd.concat([df_acs1, df_acs2])

        df_acs = df_acs[['Table', 'ID', 'Attributes', 'Label', 'Table Name', 'Year', 'Indicator Name', 'Include', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity', 'ID_Attributes', 'ID_Attributes2', 'ID2']]
        df_acs = df_acs.drop_duplicates()
        df_acs = df_acs.sort_values(['Table', 'Indicator Name', 'Year', 'ID'], ascending = [True, True, False, True])
        df_acs = df_acs.reset_index(drop=True)

        display(df_acs.head())


        if EXPORT:
            df_acs.to_csv(PATH_CSV / 'DP.csv', index=False)






    if DEC:

        print('\n'*2)
        print('DEC ------------------------------------------------------------------------------------------------------------------------')
        print('\n'*2)



        # Importing

        df_dec_2000_sf1 = import_dec_vars(2000, 'sf1')
        df_dec_2000_sf3 = import_dec_vars(2000, 'sf3')
        df_dec_2010_sf1 = import_dec_vars(2010, 'sf1')
        df_dec_2020_dp  = import_dec_vars(2020,  'dp')
        df_dec_2020_dhc = import_dec_vars(2020, 'dhc')



        # Combining

        df_dec = pd.concat([df_dec_2000_sf1, df_dec_2000_sf3, df_dec_2010_sf1, df_dec_2020_dp, df_dec_2020_dhc])
        df_dec['Label_clean'] = df_dec['label'].str.replace('Estimate!!', '')
        df_dec['Label_clean'] = df_dec['Label_clean'].str.replace('!!', ' ')
        df_dec['Label_clean'] = df_dec['Label_clean'].str.replace(':', '')

        file_config = PATH_CONFIG / 'census.xlsx'; sheet_name='DEC'
        df_config = pd.read_excel(file_config, sheet_name=sheet_name)
        df_config = df_config[['ID', 'Indicator Name', 'Include', 'Variable', 'Sort', 'Race_Ethnicity']]

        df_dec = df_dec.merge(df_config, on=['ID'], how='left')
        df_dec = df_dec.rename(columns={'label':'Label', 'concept':'Table Name', 'group':'Table'})
        df_dec = df_dec[['Year', 'Table', 'ID', 'Label', 'Table Name', 'predicateType', 'Indicator Name', 'Include', 'estimate', 'Label_clean', 'Variable', 'Sort', 'Race_Ethnicity']]

        if EXPORT:
            df_dec.to_csv(PATH_CSV / 'DEC.csv', index=False)



    if LEHD:

        print('\n'*2)
        print('LEHD ------------------------------------------------------------------------------------------------------------------------')
        print('\n'*2)

        # Importing

        with urllib.request.urlopen("https://api.census.gov/data/timeseries/qwi/rh/variables.json") as url:
            dict_lehd_rh = json.load(url)

        with urllib.request.urlopen("https://api.census.gov/data/timeseries/qwi/sa/variables.json") as url:
            dict_lehd_sa = json.load(url)

        with urllib.request.urlopen("https://api.census.gov/data/timeseries/qwi/se/variables.json") as url:
            dict_lehd_se = json.load(url)


        df_vars_rh = pd.DataFrame.from_dict(dict_lehd_rh['variables']).T.reset_index().rename(columns = {'index':'ID'})
        df_vars_sa = pd.DataFrame.from_dict(dict_lehd_sa['variables']).T.reset_index().rename(columns = {'index':'ID'})
        df_vars_se = pd.DataFrame.from_dict(dict_lehd_se['variables']).T.reset_index().rename(columns = {'index':'ID'})

        df_vars_rh['Table'] = 'Race by Ethnicity'
        df_vars_sa['Table'] = 'Sex by Age'
        df_vars_se['Table'] = 'Sex by Education'

        df_vars = pd.concat([df_vars_rh, df_vars_sa, df_vars_se])
        df_vars = df_vars.set_index('Table').reset_index()

        print(df_vars.shape)
        display(df_vars.head())



        # Combining

        file_config = PATH_CONFIG / 'census.xlsx'; sheet_name='LEHD'
        df_config = pd.read_excel(file_config, sheet_name=sheet_name)
        df_config = df_config[['Table', 'ID', 'Indicator Name', 'Include', 'Sample']]

        df_vars = df_vars.merge(df_config, on=['Table', 'ID'], how='left')
        df_vars.head()


        # Exporting to Git

        if EXPORT:
            df_vars.to_csv(PATH_CSV / 'LEHD.csv', index=False)




    # if CPS:

    #     print('\n'*2)
    #     print('CPS ------------------------------------------------------------------------------------------------------------------------')
    #     print('\n'*2)

    #     ## Importing ---

    #     ## CPS ---
    #     # initialize empty list to store data frames
    #     # iterate through each year
    #         # pull PUMS variables list from json file found on ACS website
    #         # convert to dictionary
    #         # convert to pandas data frame
    #         # apply year tag
    #         # append to list
    #     # concatenate all data frames together

    #     print('\n'*2)
    #     print('Importing CPS variables tables by year...'); print()

    #     year_start = 2009
    #     END_YEAR   = END_YEAR
    #     years = range(year_start, END_YEAR+1)

    #     list_df_cps = []

    #     for year in tqdm(years):
    #         try:
    #             if year in [1995, 1997, 1999]:
    #                 url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/apr/variables.json"
    #             if year in [1998]:
    #                 url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/aug/variables.json"
    #             if year in [2000]:
    #                 url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/sep/variables.json"
    #             if year in help.sequence(2001, END_YEAR, 1):
    #                 url_to_import = f"https://api.census.gov/data/{year}/cps/foodsec/dec/variables.json"
                    
    #             with urllib.request.urlopen(url_to_import) as url:
            
    #                 dict_cps = json.load(url)
    #                 df_cps = pd.DataFrame.from_dict(dict_cps['variables']).T.reset_index().rename(columns = {'index':'ID'})
            
    #                 df_cps['Year'] = year
    #                 list_df_cps.append(df_cps)
    #         except Exception as e: print(e)
            
    #     df_cps = pd.concat(list_df_cps)
    #     df_cps = df_cps.reset_index(drop=True)
    #     print(df_cps.shape)
    #     display(df_cps.head())


    #     # create empty list to store data frames
    #     # iterate through each year
    #         # create empty list to store data frames
    #         # subset all variables to year
    #             # create empty list to store data frames
    #                 # subset pums variables to one ID at a time
    #                 # iterate through all key/value combinations in dictionaries that represent the value mappings to make pandas data frames 
    #                 # store them in list of data frames
    #             # concatenate specific ID variable mappings together
    #             # add some labels, clean column names
    #         # apply year tag
    #         # convert to pandas data frame
    #         # store in list of data frames

    #     # concatenate all data frames together


    #     print('\n'*2)
    #     print('Cleaned CPS variables table:'); print()

    #     list_df_years = []

    #     for year in tqdm(years):
    #         df_cps_vars = df_cps[df_cps['Year'] == year]
            
    #         list_df = []
            
    #         for ID in df_cps_vars['ID'].values:
                
    #             df_ID = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)

    #             if df_ID['values'][0] is np.nan:
    #                 df_vars = pd.DataFrame()
    #                 df_vars['Value1'] = np.nan
    #                 df_vars['Value2'] = np.nan
    #                 df_vars['Description'] = np.nan
    #                 df_vars['ID'] = ID
    #                 df_vars['Label'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['label'].values[0]
    #                 df_vars['Suggested Weight'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['suggested-weight'].values[0]
    #                 df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]

    #             else:
                
    #                 for key in list(df_ID['values'][0].keys()):
                        
    #                     if key == 'item':
    #                         dict_values = {
    #                                         'Value1'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
    #                                     , 'Value2'     : list(list(df_ID['values'].values)[0]['item'].keys()  )
    #                                     , 'Description': list(list(df_ID['values'].values)[0]['item'].values())
    #                                     }
    #                         df_vars = pd.DataFrame(dict_values)
                            
            
    #                     if key == 'range':
                            
    #                         list_range = []
                
    #                         for value in df_ID['values'][0]['range']:
    #                             dict_values = {
    #                                             'Value1'     : [value['min']]
    #                                         , 'Value2'     : [value['max']]
    #                                         , 'Description': [value['description']]
    #                                         }
                                
    #                             list_range.append(pd.DataFrame(dict_values))
                                
    #                         df_vars = pd.concat(list_range)
                            
    #                     df_vars['ID'] = ID
    #                     df_vars['Label'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['label'].values[0]
    #                     df_vars['Suggested Weight'] = df_cps_vars[df_cps_vars['ID'] == ID].reset_index(drop=True)['suggested-weight'].values[0]
                
    #                     df_vars = df_vars[['Label', 'ID', 'Value1', 'Value2', 'Description', 'Suggested Weight']]
                
    #             list_df.append(df_vars)
            
            
    #         df_cps_vars = pd.concat(list_df)
    #         df_cps_vars['Year'] = year
            
    #         list_df_years.append(df_cps_vars)

    #     df_cps = pd.concat(list_df_years)
    #     df_cps = df_cps.sort_values(['Year', 'ID', 'Value1'], ascending = [False, True, True])
    #     df_cps = df_cps.reset_index(drop=True)
    #     display(df_cps.head())


    #     ## Combining ---


    #     file_config = path_config / 'census.xlsx'
    #     sheet_name='FOODSEC'
    #     df_config = pd.read_excel(file_config, sheet_name=sheet_name)
    #     df_config = df_config[['ID', 'Indicator Name', 'Include', 'ID2', 'Description2', 'Data Type', 'Table Type']]

    #     df_cps = df_cps.merge(df_config, on=['ID'], how='left')
    #     df_cps.head()



    #     ## Exporting to Git ---
    #     if EXPORT:
    #         file_out = path_csv / 'CPS.csv'
    #         df_cps.to_csv(file_out, index=False)


