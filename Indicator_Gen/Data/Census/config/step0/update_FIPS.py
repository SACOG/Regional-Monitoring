
print(); print(); print()

export=False


# Workspace -----------------------------------------------------------------------------------------------------------




import pandas as pd
from pathlib import Path
from tqdm import tqdm
import requests
import ast
import time
from IPython.display import display
import sys

PATH_GIT = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_CSV = PATH_CONFIG / 'step0' / 'csv'

FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_API = PATH_CONFIG / 'api_key.txt'

sys.path.append(str(PATH_CONFIG0))
import functions as func

sys.path.append(str(PATH_CONFIG))
import post
        


# Obtain API Key from the following source 
# https://api.census.gov/data/key_signup.html
with open(FILE_API, 'r') as file:
    api_key = file.read()



year_start = 2023
year_end   = 2023
years_to_import = range(year_start, year_end+1)
years_to_import = [2000, 2010, 2020]



counties=True
msa=False
places=False
congressional_districts=False
state_legislative_districts_upper=False
state_legislative_districts_lower=False
puma=False






# Main -----------------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':


    ## The following URL is no longer available due to DOGE (I'm guessing)3
    ## url = "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt"
    ## URL provides the following statement:
    ## "NOTICE: Due to the lapse of federal funding, portions of this website will not be updated.  Any inquiries will not be answered until appropriations are enacted"
    ## I can work around this, only slightly annoying.  Legacy code stored locally

    # Use URL to county fips mapping table
    # Import county FIPS codes by state
    url_fips = "https://www2.census.gov/geo/docs/reference/codes/files/national_cousub.txt"
    df_states = pd.read_csv(url_fips, sep=',', encoding='latin-1', on_bad_lines='skip', engine='python')

    df_states = df_states[['STATE', 'STATEFP']].drop_duplicates()
    df_states.columns = ['State', 'State FIPS']
    df_states = df_states[df_states['State FIPS'] < 60].reset_index(drop=True)
    df_states['State FIPS' ] = df_states['State FIPS'].astype(str).apply('{:0>2}'.format)

    states = df_states['State FIPS'].unique()



    if counties:

        print()
        print('Counties ------------------------------------------------------------------------------------------------------------------------')
        print()

        start_time = time.time()

        print()
        print('Importing County FIPS codes...'); print()

        # Use URL to county fips mapping table
        # Import county FIPS codes by state
        url_fips = "https://www2.census.gov/geo/docs/reference/codes/files/national_cousub.txt"
        df_counties = pd.read_csv(url_fips, sep=',', encoding='latin-1', on_bad_lines='skip', engine='python')
        df_counties = df_counties[['STATE', 'STATEFP', 'COUNTYFP', 'COUNTYNAME']].drop_duplicates().reset_index(drop=True)

        # Clean and subset FIPS file
        # rename columns
        # clean county name
        # reformat FIPS field

        df_counties['COUNTYNAME'] = df_counties['COUNTYNAME'].str.replace(' County', '')
        df_counties = post.clean_fips(df_counties)


        df_config = pd.read_excel(FILE_AREA, sheet_name='CountyFIPS', dtype=str)
        df_config = post.clean_fips(df_config)

        df_counties = df_counties.merge(df_config, on=['STATE', 'STATEFP', 'COUNTYFP', 'COUNTYNAME'], how='outer')
        df_counties = df_counties.sort_values(['STATEFP', 'COUNTYFP']).reset_index(drop=True)
        display(df_counties)


        if export:
            df_counties.to_csv(PATH_CSV / 'CountyFIPS.csv', index=False)


        print()
        print("Finished!!")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all County FIPS codes")
        print()



    if msa:

        print()
        print('MSA ------------------------------------------------------------------------------------------------------------------------')
        print()


        start_time = time.time()

        list_df_census = []

        print(); print('Importing MSA codes for all states...'); print()

        for year in tqdm(years_to_import, position=0):

            # User inputs for user API key, desired variables
            # Specify which geography to import
            # Concatenate constructed URL
            # Call data using URL
            # Use requests package to call out to the API
            # convert parsed response text to pandas df
            # apply year tag
            
            root_ = f'https://api.census.gov/data/{year}/acs/acs5'
            g_ = '?get='
            variables_ = 'NAME'
            location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*'
            api_key_ = f"&key={api_key}"

            query = f"{root_}{g_}{variables_}{location_}{api_key_}"

            response = requests.get(query).text
            response = ast.literal_eval(response)
            
            df_msa = pd.DataFrame(response[1:], columns = response[0])
            df_msa['Year'] = year

            list_df_census.append(df_msa)


        print()
        print('Concatenating all states together...')

        df_msa = pd.concat(list_df_census)




        print("Cleaning...")

        def re_extract_city(x, exp1=',', exp2='-'):
            try:
                x = x.split(exp1, 1)[0]
                x = x.split(exp2, 1)[0]
            except:
                pass
            return x

        def re_extract_state(x, exp=','):
            try:
                x = x.split(exp, 1)[1]
                x = x[1:3]
            except:
                pass
            return x

            
        df_msa['City' ] = df_msa['NAME'].apply(re_extract_city )
        df_msa['State'] = df_msa['NAME'].apply(re_extract_state)
        df_msa['Abbrv'] = df_msa['City'] + ', ' + df_msa['State']

        df_fips = pd.read_excel(FILE_AREA, sheet_name='CountyFIPS', dtype=str)
        df_fips = post.clean_fips(df_fips)

        df_fips = df_fips[['STATE', 'STATEFP']].drop_duplicates()

        df_msa = df_msa.merge(df_fips, on='STATE', how='left')
        df_msa = df_msa.rename(columns = {'NAME':'MSA', 'metropolitan statistical area/micropolitan statistical area':'MSA_ID'})

        peer_msa = [
            'Austin, TX'
            , 'Charlotte, NC'
            , 'Cincinnati, OH'
            , 'Cleveland, OH'
            , 'Columbus, OH'
            , 'Detroit, MI'
            , 'Indianapolis, IN'
            , 'Kansas City, MO'
            , 'Miami, FL'
            , 'Orlando, FL'
            , 'Phoenix, AZ'
            , 'Pittsburgh, PA'
            , 'Portland, OR'
            , 'Riverside, CA'
            , 'Sacramento, CA'
            , 'St. Louis, MO'
            , 'Salt Lake City, UT'
            , 'San Antonio, TX'
            , 'San Diego, CA'
            , 'San Francisco, CA'
            , 'San Jose, CA'
            , 'Tampa, FL'
            , 'Yuba City, CA'
        ]

        df_msa['Peer MSA'] = 'No'
        df_msa.loc[df_msa['Abbrv'].isin(peer_msa), 'Peer MSA'] = 'Yes'

        chamber_study = [
            'Boston, MA'
            , 'Pittsburgh, PA'
            , 'Columbus, OH'
            , 'Nashville, TN'
            , 'Knoxville, TN'
            , 'Dallas, TX'
            , 'Kansas City, MO'
            , 'Madison, WI'
            , 'Sacramento, CA'
            , 'Yuba City, CA'
        ]

        df_msa['Chamber Study'] = 'No'
        df_msa.loc[df_msa['Abbrv'].isin(chamber_study), 'Chamber Study'] = 'Yes'

        df_msa = df_msa[['Year', 'STATEFP', 'STATE', 'MSA_ID', 'MSA', 'Abbrv', 'Peer MSA', 'Chamber Study']]
        df_msa = df_msa.sort_values(['STATEFP', 'Abbrv', 'Year'], ascending=[True, True, False])
        df_msa = df_msa.dropna()

        if export:
            df_msa.to_csv(PATH_CSV / 'MSAcodes.csv')


        print()
        print("Finished!!")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all MSA codes")
        print()






    if places:

        print()
        print('Census Designated Places ------------------------------------------------------------------------------------------------------------------------')
        print()


        start_time = time.time()


        list_df_census = []

        print()
        print('Importing place IDs for all states...')
        print()

        for state in tqdm(states, position=0):
            for year in years_to_import:
                
                # User inputs for user API key, desired variables
                # Specify which geography to import
                # Concatenate constructed URL
                # Call data using URL
                # Use requests package to call out to the API
                # convert parsed response text to pandas df
                # apply year tag
                
                if year in [2000, 2010]:
                    root_ = f'https://api.census.gov/data/{year}/dec/sf1'
                else:
                    root_ = f'https://api.census.gov/data/{year}/dec/dhc'
                g_ = '?get='
                variables_ = 'NAME'
                location_ = '&for=place:*' + '&in=state:' + state
                api_key_ = f"&key={api_key}"

                query = f"{root_}{g_}{variables_}{location_}{api_key_}"
            
                response = requests.get(query).text
                response = ast.literal_eval(response)
                
                df_cdp = pd.DataFrame(response[1:], columns = response[0])
                df_cdp['Year'] = year

                list_df_census.append(df_cdp)


        print()
        print('Concatenating all states together...')

        df_cdp = pd.concat(list_df_census)

        df_cdp = df_cdp.sort_values(['Year', 'state', 'place', 'NAME'], ascending=[False, True, True, True])
        df_cdp = df_cdp.set_index('Year').reset_index()
            
        df_cdp['NAME'] = df_cdp['NAME'].apply(func.remove_post_comma)

        if export:
            df_cdp.to_csv(PATH_CSV / 'CDPcodes.csv', index=False)


        print()
        print("Finished!!")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all Census Designated Places codes")
        print()





    if congressional_districts:

        print()
        print('Congressional Districts ------------------------------------------------------------------------------------------------------------------------')
        print()


        start_time = time.time()


        list_df_census = []

        print()
        print('Importing Congressional Districts for all states...')
        print()

        for year in tqdm(years_to_import, position=0):
            
            # User inputs for user API key and which variables to import
            # Specify which geography to import
            # Concatenate constructed URL
            # Call data using URL
            # Use requests package to call out to the API
            # convert parsed response text to pandas df
            # apply year tag

            root_ = f'https://api.census.gov/data/{year}/acs/acs5'
            g_ = '?get='
            variables_ = 'NAME'
            location_ = '&for=congressional%20district:*'
            api_key_ = f"&key={api_key}"
        
            query = f"{root_}{g_}{variables_}{location_}{api_key_}"

            response = requests.get(query).text
            response = ast.literal_eval(response)
            
            df_cd = pd.DataFrame(response[1:], columns = response[0])
            df_cd['Year'] = year

            list_df_census.append(df_cd)


        print()
        print('Concatenating all states together...')

        df_cd = pd.concat(list_df_census)


        df_cd = df_cd.sort_values(['Year', 'state', 'congressional district'], ascending = [False, True, True])


        if export:
            df_cd.to_csv(PATH_CSV / 'CDcodes.csv')


        print()
        print("Finished!!")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update all Congressional District codes")
        print()







    if state_legislative_districts_upper:

        print()
        print('State Legislative Upper Districts ------------------------------------------------------------------------------------------------------------------------')
        print()




        start_time = time.time()


        print('Importing State Legislative Upper Districts for all states...')
        print()

        list_df_states = []

        for state in tqdm(states):

            list_df_years = []
            
            for year in years_to_import:

                # User inputs for user API key, desired variables and years to import
                # Specify which geography to import
                # Concatenate constructed URL
                # Call data using URL
                # Use requests package to call out to the API
                # convert parsed response text to pandas df
                # apply year tag
                
                root_ = f'https://api.census.gov/data/{year}/acs/acs5'
                g_ = '?get='        
                variables_ = 'NAME'
                location_ = '&for=state%20legislative%20district%20(upper%20chamber):*&in=state:' + str(state)
                api_key_ = f"&key={api_key}"
                
                query = f"{root_}{g_}{variables_}{location_}{api_key_}"
            
                response = requests.get(query).text
                response = ast.literal_eval(response)
                
                df_census = pd.DataFrame(response[1:], columns = response[0])
                
                df_census['Year'] = year
                # df_census['State FIPS Code'] = state
            
                list_df_years.append(df_census)

            try:
                df_state = pd.concat(list_df_years)
                df_state = df_state.reset_index(drop=True)
                list_df_states.append(df_state)
            except: pass

        print()
        print('Concatenating all states together...')

        df_sldu = pd.concat(list_df_states)
        df_sldu  = df_sldu.sort_values(['Year', 'state', 'state legislative district (upper chamber)'], ascending = [False, True, True])

        if export:
            df_sldu.to_csv(PATH_CSV / 'SLDUcodes.csv')

        print()
        print("Finished!!")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- State Legislative Upper District codes")
        print()



    if state_legislative_districts_lower:

        print()
        print('State Legislative Lower Districts ------------------------------------------------------------------------------------------------------------------------')
        print()



        start_time = time.time()


        print('Importing place IDs for all states...')
        print()

        list_df_states = []

        for state in tqdm(states, position=0):

            list_df_years = []
            
            for year in years_to_import:

                try:
                
                    # User inputs for user API key, desired variables and years to import
                    # Specify which geography to import
                    # Concatenate constructed URL
                    # Call data using URL
                    # Use requests package to call out to the API
                    # convert parsed response text to pandas df
                    # apply year tag
                    
                    root_ = f'https://api.census.gov/data/{year}/acs/acs5'
                    g_ = '?get='        
                    variables_ = 'NAME'
                    location_ = '&for=state%20legislative%20district%20(lower%20chamber):*&in=state:' + str(state)
                    api_key_ = f"&key={api_key}"
                    
                    query = f"{root_}{g_}{variables_}{location_}{api_key_}"
                
                    response = requests.get(query).text
                    response = ast.literal_eval(response)
                    
                    df_census = pd.DataFrame(response[1:], columns = response[0])
                    
                    df_census['Year'] = year
                    # df_census['State FIPS Code'] = state
                
                    list_df_years.append(df_census)
                except: pass

            try:
                df_state = pd.concat(list_df_years)
                df_state = df_state.reset_index(drop=True)
                list_df_states.append(df_state)
            except: pass

        print()
        print('Concatenating all states together...')

        df_sldl = pd.concat(list_df_states)
        df_sldl = df_sldl.sort_values(['Year', 'state', 'state legislative district (lower chamber)'], ascending = [False, True, True])


        if export:
            df_sldl.to_csv(PATH_CSV / 'SLDLcodes.csv')


        print()
        print("Finished!!")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update State Legislative Lower District codes")
        print()



    # if puma:

    #     print()
    #     print('PUMAs --------------------------------------------------------------------------------------------------------------------------------------------')
    #     print()


    #     # Use URL to county fips mapping table
    #     # Import county FIPS codes by state
    #     url_puma_2020 = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/2020_Census_Tract_to_2020_PUMA.txt"
    #     url_puma_2010 = "https://www2.census.gov/geo/docs/maps-data/data/rel/2010_Census_Tract_to_2010_PUMA.txt" # NOTICE: Cut due to budgeting

    #     df_puma_2020 = pd.read_csv(url_puma_2020, header=0, sep=',')
    #     df_puma_2010 = pd.read_csv(url_puma_2010, header=0, sep=',')

    #     df_puma_2020['Years'] = '2022-2031'
    #     df_puma_2010['Years'] = '2012-2021'

    #     df_puma = pd.concat([df_puma_2020, df_puma_2010])


    #     df_puma['PUMA5CE' ] = df_puma['PUMA5CE' ].astype(str).apply('{:0>5}'.format)
    #     df_puma['TRACTCE' ] = df_puma['TRACTCE' ].astype(str).apply('{:0>6}'.format)
    #     df_puma['COUNTYFP'] = df_puma['COUNTYFP'].astype(str).apply('{:0>3}'.format)
    #     df_puma['STATEFP' ] = df_puma['STATEFP' ].astype(str).apply('{:0>2}'.format)


    #     df_puma_names_2020 = pd.read_csv(PATH_CSV / '2020_PUMA_Names.csv')
    #     df_puma_names_2010 = pd.read_csv(PATH_CSV / '2010_PUMA_Names.csv')

    #     df_puma_names_2020['Years'] = '2022-2031'
    #     df_puma_names_2010['Years'] = '2012-2021'

    #     df_puma_names = pd.concat([df_puma_names_2020, df_puma_names_2010])

    #     df_puma_names['PUMA5CE'] = df_puma_names['PUMA5CE'].astype(str).apply('{:0>5}'.format)
    #     df_puma_names['STATEFP'] = df_puma_names['STATEFP'].astype(str).apply('{:0>2}'.format)

    #     df_puma = df_puma.merge(df_puma_names, on = ['STATEFP', 'PUMA5CE', 'Years'], how = 'left')


    #     if export:
    #         df_puma.to_csv(PATH_CSV / 'PUMAcodes.csv')


    #     print()
    #     print("Finished!!")
    #     print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes --- to update PUMA codes")


