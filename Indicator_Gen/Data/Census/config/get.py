

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

'''





import numpy as np
import pandas as pd
from pathlib import Path
import time
from tqdm import tqdm
import functools as ft
import re
import requests
import ast
from IPython.display import display
import traceback
import sys


sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'config'))
import functions as func


# Main function used to get data with API request
def get_data(
        df_urls
        , api_key, estimate, sample, geography, variables, year
        , state=None, county=None, msa=None, puma=None, ZIPcode=None
    ):
        
    '''
    User defined function to import Data from the Census Bureau
    User inputs: [api_key, estimate, geography variables, year] to tell Census Bureau that we have access with the API key and
                    what type of sample data to pull, which variables we want to import, what year, and which state
    The "df_urls" object pulls the "URL" tab from the "Census Configuration File.xlsx", which contains the root URL needed for any API request available here https://api.census.gov/data.html         
    Only pulls 1 year at a time (geography IDs, like census tracts, sometimes change at the start of each decade)
    '''

    # Assert that inputs for estimate and geography are appropriate
    assert estimate  in ['ACS5', 'ACS1', 'DEC', 'CPS' , 'RH', 'SA', 'SE'], "Unacceptable estimate input, requires 'ACS5', 'ACS1', 'DEC', 'LEHD', or 'CPS' "
    assert sample    in ['ACS', 'DP', 'DEC', 'DHC', 'PUMS', 'FOODSEC' , 'SUBJECT', 'LEHD'], "Unacceptable sample type input, requires 'ACS', 'DEC', 'DHS', 'PUMS', 'FOODSEC', 'SUBJECT', 'RH', 'SA', or 'SE'"
    assert geography in ['Places', 'Block Groups', 'Tracts', 'Counties', 'MSA', 'PUMA', 'ZIP Codes', 'Congressional Districts', 'State Legislative Upper Districts', 'State Legislative Lower Districts', 'States', 'National'], "Unacceptable geography input, requires 'Places', 'Block Groups', 'Tracts', 'Counties', 'MSA', or 'PUMA' "


    ## Construct URL
    df_url = df_urls[
          (df_urls['Sample'   ] == sample  )
        & (df_urls['Estimate' ] == estimate)
        & (df_urls['c_vintage'] == year    )
        ]

    # Create rootpath and specify dataset type
    root_ = df_url['c_url'].values[0]
    g_ = '?get='

    if sample == 'LEHD':
        root_ = re.sub('<NA>/', '', root_)

    # User inputs for user API key, desired variables and years to import
    api_key_ = f"&key={api_key}"
    variables_ = variables

    # Specify which geography to import
    if geography == 'ZIP Codes':
        location_ = '&for=zip%20code%20tabulation%20area:' + ZIPcode
    if geography == 'Congressional Districts':
        location_ = '&for=congressional%20district:*' + '&in=state:' + state
    if geography == 'State Legislative Upper Districts':
        location_ = '&for=state%20legislative%20district%20(upper%20chamber):*' + '&in=state:' + state
    if geography == 'State Legislative Lower Districts':
        location_ = '&for=state%20legislative%20district%20(lower%20chamber):*' + '&in=state:' + state
    if geography == 'Places':
        location_ = '&for=place:*' + '&in=state:' + state
    if geography == 'Block Groups':
        location_ = '&for=block%20group:*' + '&in=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'Tracts':
        location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'Counties':
        if year == 'timeseries':
            location_ = '&for=county:' + county + '&in=state:' + state + '&time=from 2000-Q1 to 2023-Q4'
        else:
            location_ = '&for=county:' + county + '&in=state:' + state
            # location_ = '&for=county:*' + '&in=state:' + state
    if geography == 'MSA':
        if sample in ['LEHD']:
            if year == 'timeseries':
                location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa) + '&in=state:' + state + '&time=from 2000-Q1 to 2024-Q4'
            else:
                location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa) + '&in=state:' + state
        else:
            # location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)
            location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*'
    if geography == 'PUMA':
        location_ =  '&for=public%20use%20microdata%20area:' + puma + '&in=state:' + state
    if geography == 'States':
        location_ = '&for=state:' + state
    if geography == 'National':
        location_ = '&for=us:*'
    
    ## Concatenate constructed URL
    request = f"{root_}{g_}{variables_}{location_}{api_key_}"
    
    ## Call data using URL

    # Use requests package to call out to the API
    response = requests.get(request).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_census = pd.DataFrame(response[1:], columns=response[0])
    
    # apply year tag
    if sample != 'LEHD':
        df_census['Year'] = year

    ## Return
    return df_census






# Prep ---------------------------------------------------------------------------------------------------------------------------------------------------------------



def read_inputs_file(import_tab):

    file_area = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'
    file_inputs = Path(__file__).parent / 'census.xlsx'

    print()
    print()
    print("API request inputs:")
    print()

    df_inputs = pd.read_excel(file_inputs, sheet_name=import_tab)

    return df_inputs, file_inputs, file_area




def read_vars_file(file_inputs, sample_type, indicator, years_to_import, estimate):

    df_vars = pd.read_excel(file_inputs, sheet_name=sample_type)
    df_vars = df_vars[(df_vars['Indicator Name'].str.contains(f'{indicator}$', regex=True).replace(np.nan, False)) | (df_vars['Indicator Name'].str.contains(f'{indicator},', regex=True).replace(np.nan, False))]
    df_vars = df_vars[df_vars['Include'] == 'Yes']
    df_vars = df_vars[df_vars['Year'].isin(years_to_import)]

    if sample_type == 'LEHD':
        df_vars[df_vars['Sample'] == estimate]

    return df_vars


def read_fips_file_pums(import_tab):
    
    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype={'State FIPS':str, 'County FIPS':str})
    df_fips_pums = pd.read_excel(file_area, sheet_name='PUMAcodes', dtype = {'STATEFP':str, 'COUNTYFP':str, 'TRACTCE':str, 'PUMA5CE':str})
    df_fips_pums = df_fips_pums.rename(columns={'STATEFP':'State FIPS', 'COUNTYFP':'County FIPS'})

    df_fips = df_fips.merge(df_fips_pums[['State FIPS', 'County FIPS', 'PUMA5CE']].drop_duplicates(), on = ['State FIPS', 'County FIPS'])
    df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values)) & (df_fips['County Name'].isin(df_inputs['counties'].values))]

    dt_fips = df_fips[['State FIPS', 'PUMA5CE']].drop_duplicates().reset_index(drop=True).groupby('State FIPS')['PUMA5CE'].apply(list).to_dict()
    for key in list(dt_fips.keys()):
        dt_fips[key] = ",".join(dt_fips[key])

    return df_fips, dt_fips





def prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate):

    def moe_split(text):
        try:
            estimates = text.split(',')
            pattern = re.compile('.*E$|.*M$')
            text = ','.join([est for est in estimates if pattern.match(est)])
            return text
        except:
            return text

    df_vars = read_vars_file(file_inputs, sample_type, indicator, years_to_import, estimate)

    if margin_of_error == 'Yes':
        df_vars['ID_Attributes2'] = df_vars['ID_Attributes2'].apply(moe_split)
        list_vars = ['NAME'] + list(set(df_vars['ID_Attributes2'].to_list()))
    else:
        list_vars = ['NAME'] + list(set(df_vars['ID2'].to_list()))

    if sample_type in ['ACS', 'DP']:
        tables = df_vars['Table'].unique()
        print()
        print("Tables set to import:")
        print(tables)

    if import_tab == 'Counties':
        
        df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype={'State FIPS':str, 'County FIPS':str})
        df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values)) & (df_fips['County Name'].isin(df_inputs['counties'].values))]

        dt_fips = df_fips[['State FIPS', 'County FIPS']].drop_duplicates().reset_index(drop=True).groupby('State FIPS')['County FIPS'].apply(list).to_dict()
        for key in list(dt_fips.keys()):
            dt_fips[key] = ",".join(dt_fips[key])
    
        print()
        print('Counties set to import by state:')
        print(dt_fips)
        print()
        

    if import_tab == 'MSA':
    
        msa_to_import = list(df_inputs['msa'].values)
        df_fips = pd.read_excel(file_area, sheet_name='MSAcodes', dtype={'MSA_ID':object})
        df_fips = df_fips[['Year', 'MSA_ID', 'MSA', 'Abbrv']].drop_duplicates().reset_index(drop=True)
        df_fips = df_fips[df_fips['Abbrv'].isin(msa_to_import)]
    
        print()
        print("MSA set to import:")
        print(msa_to_import)
        print()
        print("MSA IDs:")
        display(df_fips)

    if import_tab == 'States':
    
        # Set MSAs to import
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing

        df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype={'State FIPS':object, 'County FIPS':object})
        df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values))]
        states_to_import = [str(state) for state in df_fips['State FIPS'].unique()]
        
        print()
        print("States set to import:")
        print(states_to_import)

    if import_tab == 'National':
        print("Setting to import data at a national level")

    print()
    print('Variables set to import:')
    print(list_vars)
    print()
    print('Variable Mapping table:')
    display(df_vars.head(3))

    
    if import_tab == 'Counties':
        if sample_type in ['ACS', 'DP']:
            return df_vars, df_fips, dt_fips, tables
        else:
            return df_vars, df_fips, dt_fips
    if import_tab == 'MSA':
        if sample_type in ['ACS', 'DP']:
            return df_vars, df_fips, msa_to_import, tables
        else:
            return df_vars, df_fips, msa_to_import
    if import_tab == 'States':
        if sample_type in ['ACS', 'DP']:
            return df_vars, df_fips, states_to_import, tables
        else:
            return df_vars, df_fips, states_to_import
    if import_tab == 'National':
        if sample_type in ['ACS', 'DP']:
            return df_vars, tables
        else:
            return df_vars





# Get -------------------------------------------------------------------------------------------------------------------------------------------------------------------------




# ACS ---

def get_acs(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab):

    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    if import_tab == 'Counties':
        df_vars, df_fips, dt_fips, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'MSA':
        df_vars, df_fips, msa_to_import, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'States':
        df_vars, df_fips, states_to_import, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'National':
        df_vars, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)

    if geography == 'Places':
        geo_id = ['NAME', 'state', 'place']
    if geography == 'Block Groups':
        geo_id = ['NAME', 'state', 'county', 'tract', 'block group']
    if geography == 'Tracts':
        geo_id = ['NAME', 'state', 'county', 'tract']
    if geography == 'Counties':
        geo_id = ['NAME', 'state', 'county']
    if geography == 'MSA':
        geo_id = ['NAME', 'metropolitan statistical area/micropolitan statistical area']
    if geography == 'States':
        geo_id = ['NAME', 'state']

    ## Import data and concatenate onto ID fields ##
    print("Importing and compiling ACS data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    file_vars = Path(__file__).parent / 'census.xlsx'
    df_vars = pd.read_excel(file_vars, sheet_name=sample_type)

    list_df_years = []

    for year in tqdm(years_to_import):

        list_df_tables = []
        
        try:
            for table in tables:

                tqdm.write('')
                tqdm.write("Table ID: " + table)
                tqdm.write('')

                df_table = df_vars[((df_vars['Indicator Name'].str.contains(f'{indicator}$', regex=True).replace(np.nan, False)) | (df_vars['Indicator Name'].str.contains(f'{indicator},', regex=True).replace(np.nan, False)))
                                    & (df_vars['Table'] == table) & (df_vars['Year'] == year)]
                if margin_of_error == 'Yes':
                    list_table_vars  = [['NAME'] + df_table['ID_Attributes'] .to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes' ].to_list()), 20)]
                    list_table_vars2 = [['NAME'] + df_table['ID_Attributes2'].to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes2'].to_list()), 20)]
                else:
                    list_table_vars  = [['NAME'] + df_table['ID' ].to_list()[x:x+45] for x in range(0, len(df_table['ID' ].to_list()), 45)]
                    list_table_vars2 = [['NAME'] + df_table['ID2'].to_list()[x:x+45] for x in range(0, len(df_table['ID2'].to_list()), 45)]
                
                list_variables  = []
                list_variables2 = []
                for x, y in zip(list_table_vars, list_table_vars2):
                    list_variables.append(",".join(x))
                    y.remove('NAME')
                    y2 = []
                    for ii in y:
                        ii = ii.split(',')
                        y2 = y2 + ii
                    list_variables2.append(y2)
                
                list_df_vars = []
                
                for variables, variables2 in zip(list_variables, list_variables2):

                    tqdm.write("Variables: " + variables)
                    list_df_states = []

                    if import_tab == 'Counties':
                        for state in list(dt_fips.keys()):
                            tqdm.write('State: ' + state)
                            try:
                                list_df_states.append(
                                    get_data(df_urls      = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state
                                                , county    = dt_fips[state])
                                )
                            except Exception as e: print(e)
                                    
                    if import_tab == 'MSA':
                        try:
                            msa_to_import = df_fips[df_fips['Year'] == year]
                            msa_to_import = list(msa_to_import['MSA_ID'].values)
                            msa_to_import = ','.join(msa_to_import)
                            list_df_states.append(
                                get_data(df_urls      = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year
                                            , msa       = msa_to_import)
                            )
                        except Exception as e: print(e)

                    if import_tab == 'States':
                        for state in states_to_import:
                            tqdm.write('State: ' + state)
                            try:
                                list_df_states.append(
                                    get_data(df_urls      = df_urls
                                              , api_key   = api_key
                                              , estimate  = estimate
                                              , sample    = sample_type
                                              , geography = geography
                                              , variables = variables
                                              , year      = year
                                              , state     = state)
                                )
                            except Exception as e: print(e)

                    if import_tab == 'National':
                        try:
                            list_df_states.append(
                                get_data(df_urls      = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year)
                            )
                        except Exception as e: print(e)

                    df_states = pd.concat(list_df_states)
                    df_states = df_states.set_index(geo_id + ['Year']).reset_index()
                    df_states.columns = geo_id + ['Year'] + variables2
                    list_df_vars.append(df_states)

                df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_vars)

                list_df_tables.append(df_vars_all)
                tqdm.write("All variables from table ID " + table + " have been reduced together into one table")
                tqdm.write('')

            tqdm.write('')
            tqdm.write("Reducing all tables together into one final table...")
            tqdm.write('')

            df_year = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_tables)
            df_year = df_year.set_index(geo_id + ['Year']).reset_index()
            if geography in ['Block Groups', 'Tracts', 'Counties']:
                df_year = df_year.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                        , left_on = ['state', 'county']
                                                        , right_on = ['State FIPS', 'County FIPS'])
                df_year.drop(['State FIPS', 'County FIPS'], axis=1, inplace=True)
                df_year = df_year.set_index(geo_id + ['Year']).reset_index()
            if geography == 'National':
                df_year = df_year.drop('us', axis=1)


            list_df_years.append(df_year)
        except Exception as e: print(e)

    df_census = pd.concat(list_df_years)
    df_census = df_census.drop_duplicates().reset_index(drop=True)
    display(df_census.head())

    return df_census






# PUMS ---

def get_pums(api_key, df_urls, estimate, sample_type, indicator, geography, years_to_import, margin_of_error, import_tab):

    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    # Remove 2012-2015 if pulling PUMS tables (they only reported at the state level for PUMS on these years)
    # Create dictionary of variable mappings by year (sometimes the variable name changes over time)
    # Import County FIPS mapping
    # Convert to dictionary object for easy state-county combination importing

    df_vars = read_vars_file(file_inputs, sample_type, indicator, years_to_import, estimate)
    if 'H' in df_vars['Table Type'].unique():
        table_type = 'H'
        weight = 'WGTP'
    else:
        table_type = 'P'
        weight = 'PWGTP'

    print()
    print('PUMS table roll up: ' + table_type)

    # if margin_of_error == 'Yes':
    #     df_vars.loc[(df_vars['ID'].str.contains('WGTP')) & (df_vars['Table Type'] == table_type), 'Include'] = 'Yes'                
    
    df_vars = df_vars[df_vars['Include'] == 'Yes']
        
    groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
    groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

    print()
    print('PUMS variables to group by: ')
    print(groups)
    print()
    print('PUMS variables to group by (excluding integer based groups): ')
    print(groups2)
    
    df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
            
    dt_vars = {}
    for year in years_to_import:
        if margin_of_error == 'Yes': #TODO:, i forget why i the ""== integer" filter is there, probably important?
            dt_vars[str(year)] = func.unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'].str.contains('group'))]['ID'].to_list()) + func.unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'] == 'integer')]['ID'].to_list()) + [weight] + [weight + str(num) for num in func.sequence(1, 80, 1)]
        else:
            dt_vars[str(year)] = func.unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'].str.contains('group'))]['ID'].to_list()) + func.unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'] == 'integer')]['ID'].to_list()) + [weight]

    # TODO: replace w function
    df_fips, dt_fips = read_fips_file_pums(import_tab)

    print()
    print("PUMA's set to import by state: ")
    print(dt_fips)
    print()
    print('Variables set to import by year:')
    print(dt_vars)


    print()
    print('Variable Mapping table:')
    display(df_vars.head(3))


    print("Importing and compiling PUMS data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and PUMAs
    # import all variables
    # combine all years and PUMAs
    # outer join variables onto ID fields for each geography type
    # calculate margin of error using replicate weights

    for state in list(dt_fips.keys()):
        print('State: ' + state)
        list_df_years = []
        for year in years_to_import:
            print()
            print('Year: ' + str(year))
            list_df_vars = []
            try:
                list_table_vars = [dt_vars[str(year)][x:x+45] for x in range(0, len(dt_vars[str(year)]), 45)]
                
                list_variables = []
                for x in list_table_vars:
                    list_variables.append(",".join(x))

                print('Querying variables...')
                for variables in tqdm(list_variables):
                    df_pums = get_data(df_urls         = df_urls
                                                        , api_key   = api_key
                                                        , estimate  = estimate
                                                        , sample    = sample_type
                                                        , geography = geography
                                                        , variables = 'PUMA,SERIALNO,SPORDER,' + variables
                                                        , year      = year
                                                        , state     = state
                                                        , puma      = dt_fips[state])
                    df_pums['state'] = state
                    df_pums = df_pums.drop(['public use microdata area'], axis=1)
                    list_df_vars.append(df_pums)

                df_vars_years = ft.reduce(lambda left, right: pd.merge(left, right, on = ['state', 'SERIALNO', 'Year', 'PUMA', 'SPORDER'], how = 'left'), list_df_vars)
                df_vars_years = df_vars_years.set_index(['state', 'SERIALNO', 'Year', 'PUMA', 'SPORDER']).reset_index()
                df_vars_years.columns = ['state', 'SERIALNO', 'Year', 'PUMA', 'SPORDER'] + dt_vars[str(np.max(years_to_import))]
                if (table_type == 'H') & ('SPORDER' in df_vars_years.columns):
                    df_vars_years = df_vars_years[df_vars_years['SPORDER'] == '1']
                df_vars_years = df_vars_years.drop('SPORDER', axis=1)
                if margin_of_error == 'Yes':
                    print('Calculating margin of error using replicate weights...')
                    cols = [col for col in df_vars_years.columns if weight in col]
                    df_vars_years[cols] = df_vars_years[cols].replace('', np.nan).astype(int)
                    ME_weights = [weight + str(num) for num in func.sequence(1, 80, 1)]
                    cols = list(df_vars_years.drop(ME_weights, axis=1).columns)
                    df_me = pd.melt(df_vars_years, id_vars=cols, var_name='replicates', value_name='replicate_weights')
                    df_me['sq_diff'] = (df_me['replicate_weights'] - df_me[weight])**2
                    df_me = df_me.groupby(cols, as_index=False)['sq_diff'].agg('sum') # Change from sum to 'sum'
                    df_me['variance'] = df_me['sq_diff']*(4/80)
                    df_me['SE'] = np.sqrt(df_me['variance'])
                    df_me['ME'] = df_me['SE']*1.645
                    df_me = df_me[cols + ['ME']].drop_duplicates()
                    df_vars_years = df_vars_years.drop(ME_weights, axis=1)
                    df_vars_years = df_vars_years.merge(df_me, on=cols, how='left')
                    df_vars_years = df_vars_years.drop_duplicates().reset_index(drop=True)
                list_df_years.append(df_vars_years)
                
                print('Success!')
                
            except Exception as e:
                # Get exception information
                # Extract the line number from the traceback
                # Print the error message and line number
                exc_type, exc_value, exc_traceback = sys.exc_info()
                line_number = traceback.extract_tb(exc_traceback)[-1][1]
                print(f"Error: {e}")
                print(f"Line number: {line_number}")
                                
    df_census = pd.concat(list_df_years)

    return df_census






# SUBJECT ---

def get_subject(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab):

    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    if import_tab == 'Counties':
        df_vars, df_fips, dt_fips = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'MSA':
        df_vars, df_fips, msa_to_import = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'States':
        df_vars, df_fips, states_to_import = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'National':
        df_vars = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)

    if geography == 'Tracts':
        geo_id = ['NAME', 'state', 'county', 'tract']
    if geography == 'Counties':
        geo_id = ['NAME', 'state', 'county']
    if geography == 'MSA':
        geo_id = ['NAME', 'metropolitan statistical area/micropolitan statistical area']
    if geography == 'States':
        geo_id = ['NAME', 'state']

    print("Importing and compiling ACS Subject data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    file_vars = Path(__file__).parent / 'census.xlsx'
    df_vars = pd.read_excel(file_vars, sheet_name=sample_type)

    list_df_years = []

    for year in tqdm(years_to_import):
        try:
            df_vars2 = df_vars.copy()
            df_vars2 = df_vars2[df_vars2['Year'] == year]
            df_vars2 = df_vars2[(df_vars2['Indicator Name'].str.contains(f'{indicator}$', regex=True).replace(np.nan, False)) | (df_vars2['Indicator Name'].str.contains(f'{indicator},', regex=True).replace(np.nan, False))]
            df_vars2 = df_vars2[df_vars2['Include'] == 'Yes']

            if margin_of_error == 'Yes':
                list_table_vars  = [['NAME'] + df_vars2['ID_Attributes' ].to_list()[x:x+20] for x in range(0, len(df_vars2['ID_Attributes' ].to_list()), 20)]
                list_table_vars2 = [['NAME'] + df_vars2['ID_Attributes2'].to_list()[x:x+20] for x in range(0, len(df_vars2['ID_Attributes2'].to_list()), 20)]
            else:
                list_table_vars  = [['NAME'] + df_vars2['ID' ].to_list()[x:x+45] for x in range(0, len(df_vars2['ID' ].to_list()), 45)]
                list_table_vars2 = [['NAME'] + df_vars2['ID2'].to_list()[x:x+45] for x in range(0, len(df_vars2['ID2'].to_list()), 45)]


            list_variables  = []
            list_variables2 = []
            for x, y in zip(list_table_vars, list_table_vars2):
                list_variables.append(",".join(x))
                y.remove('NAME')
                y2 = []
                for ii in y:
                    ii = ii.split(',')
                    y2 = y2 + ii
                list_variables2.append(y2)


            list_df_vars = []

            for variables, variables2 in zip(list_variables, list_variables2):

                list_df_states = []
                tqdm.write("Variables: " + variables)

                if import_tab == 'Counties':
                    for state in list(dt_fips.keys()):
                        tqdm.write('State: ' + state)
                        try:
                            list_df_states.append(
                                get_data(df_urls        = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state
                                                , county    = dt_fips[state])
                            )
                        except Exception as e: print(e)
                                
                if import_tab == 'MSA':
                    try:
                        list_df_states.append(
                            get_data(df_urls        = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year
                                            , msa       = msa_to_import)
                        )
                    except Exception as e: print(e)

                if import_tab == 'States':
                    for state in states_to_import:
                        tqdm.write('State: ' + state)
                        try:
                            list_df_states.append(
                                get_data(df_urls        = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state)
                            )
                        except Exception as e: print(e)

                df_states = pd.concat(list_df_states)
                df_states = df_states.set_index(geo_id + ['Year']).reset_index()
                df_states.columns = geo_id + ['Year'] + variables2
                list_df_vars.append(df_states)

            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_vars)
            list_df_years.append(df_vars_all)

        except Exception as e: print(e)


    print()
    print("Reducing all tables together into one final table...")
    print()

    df_census = pd.concat(list_df_years)
    if geography == 'Tracts':
        df_census = df_census.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']], left_on=['state', 'county'], right_on=['State FIPS', 'County FIPS'])
        df_census = df_census.drop(['State FIPS', 'County FIPS'], axis=1)
        df_census = df_census.set_index(['NAME', 'state', 'county', 'County Name', 'tract', 'Year']).reset_index()
    if geography == 'Counties':
        df_census = df_census.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']], left_on=['state', 'county'], right_on=['State FIPS', 'County FIPS'])
        df_census = df_census.drop(['State FIPS', 'County FIPS'], axis=1)
        df_census = df_census.set_index(['NAME', 'state', 'county', 'County Name', 'Year']).reset_index()
    if geography == 'MSA':
        df_census = df_census.set_index(['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year']).reset_index()
    if geography == 'States':
        df_census = df_census.set_index(['NAME', 'state','Year']).reset_index()

    return df_census








# Demographic Profile ---


def get_dp(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab):

    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    if import_tab == 'Counties':
        df_vars, df_fips, dt_fips, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'MSA':
        df_vars, df_fips, msa_to_import, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'States':
        df_vars, df_fips, states_to_import, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)
    if import_tab == 'National':
        df_vars, tables = prep_request_special(df_inputs, file_inputs, file_area, sample_type, indicator, margin_of_error, import_tab, years_to_import, estimate)


    if geography == 'Places':
        geo_id = ['NAME', 'state', 'place']
    if geography == 'Block Groups':
        geo_id = ['NAME', 'state', 'county', 'tract', 'block group']
    if geography == 'Tracts':
        geo_id = ['NAME', 'state', 'county', 'tract']
    if geography == 'Counties':
        geo_id = ['NAME', 'state', 'county']
    if geography == 'MSA':
        geo_id = ['NAME', 'metropolitan statistical area/micropolitan statistical area']
    if geography == 'States':
        geo_id = ['NAME', 'state']

    ## Import data and concatenate onto ID fields ##
    print("Importing and compiling ACS data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    file_vars = Path(__file__).parent / 'census.xlsx'
    df_vars = pd.read_excel(file_vars, sheet_name=sample_type)

    list_df_years = []


    for year in tqdm(years_to_import):

        list_df_tables = []
        
        for table in tables:

            tqdm.write('')
            tqdm.write("Table ID: " + table)
            tqdm.write('')

            df_table = df_vars[((df_vars['Indicator Name'].str.contains(f'{indicator}$', regex=True).replace(np.nan, False)) | (df_vars['Indicator Name'].str.contains(f'{indicator},', regex=True).replace(np.nan, False))) & (df_vars['Table'] == table) & (df_vars['Year'] == year)]
            if margin_of_error == 'Yes':
                list_table_vars  = [['NAME'] + df_table['ID_Attributes'] .to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes' ].to_list()), 20)]
                list_table_vars2 = [['NAME'] + df_table['ID_Attributes2'].to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes2'].to_list()), 20)]
            else:
                list_table_vars  = [['NAME'] + df_table['ID' ].to_list()[x:x+45] for x in range(0, len(df_table['ID' ].to_list()), 45)]
                list_table_vars2 = [['NAME'] + df_table['ID2'].to_list()[x:x+45] for x in range(0, len(df_table['ID2'].to_list()), 45)]
            
            list_variables  = []
            list_variables2 = []
            for x, y in zip(list_table_vars, list_table_vars2):
                list_variables.append(",".join(x))
                y.remove('NAME')
                y2 = []
                for ii in y:
                    ii = ii.split(',')
                    y2 = y2 + ii
                list_variables2.append(y2)
            
            list_df_vars = []
            
            for variables, variables2 in zip(list_variables, list_variables2):

                tqdm.write("Variables: " + variables)
                list_df_states = []

                if import_tab == 'Counties':
                    for state in list(dt_fips.keys()):
                        tqdm.write('State: ' + state)
                        try:
                            list_df_states.append(
                                get_data(df_urls        = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state
                                                , county    = dt_fips[state])
                            )
                        except Exception as e: print(e)
                                
                if import_tab == 'MSA':
                    try:
                        msa_to_import = df_fips[df_fips['Year'] == year]
                        msa_to_import = list(msa_to_import['MSA_ID'].values)
                        msa_to_import = ','.join(msa_to_import)
                        list_df_states.append(
                            get_data(df_urls        = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year
                                            , msa       = msa_to_import)
                        )
                    except Exception as e: print(e)

                if import_tab == 'States':
                    for state in states_to_import:
                        tqdm.write('State: ' + state)
                        try:
                            list_df_states.append(
                                get_data(df_urls        = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state)
                            )
                        except Exception as e: print(e)

                if import_tab == 'National':
                    try:
                        list_df_states.append(
                            get_data(df_urls        = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year)
                        )
                    except Exception as e: print(e)

                df_states = pd.concat(list_df_states)
                df_states = df_states.set_index(geo_id + ['Year']).reset_index()
                df_states.columns = geo_id + ['Year'] + variables2
                list_df_vars.append(df_states)

            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_vars)

            list_df_tables.append(df_vars_all)
            tqdm.write("All variables from table ID " + table + " have been reduced together into one table")
            tqdm.write('')

        tqdm.write('')
        tqdm.write("Reducing all tables together into one final table...")
        tqdm.write('')

        df_year = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_tables)
        df_year = df_year.set_index(geo_id + ['Year']).reset_index()
        if geography in ['Block Groups', 'Tracts', 'Counties']:
            df_year = df_year.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']], left_on=['state', 'county'], right_on=['State FIPS', 'County FIPS'])
            df_year.drop(['State FIPS', 'County FIPS'], axis=1, inplace=True)
            df_year = df_year.set_index(geo_id + ['Year']).reset_index()
        if geography == 'National':
            df_year = df_year.drop('us', axis=1)

        list_df_years.append(df_year)

    df_census = pd.concat(list_df_years)
    df_census = df_census.drop_duplicates().reset_index(drop=True)
    display(df_census.head())

    return df_census






# DEC ---


def get_dec(api_key, df_urls, estimate, sample_type, indicator, geography, years_to_import, import_tab):

    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    # Reset years to import for DEC
    # Set DEC variables to import
    # Import County FIPS mapping
    # Convert to dictionary object for easy state-county combination importing

    df_vars = read_vars_file(file_inputs, sample_type, indicator, years_to_import, estimate)
            
    dt_vars  = {}
    dt_vars2 = {}
    for year in years_to_import:
        dt_vars [str(year)] = ['NAME'] + func.unique(df_vars[df_vars['Year'] == year]['ID' ].to_list())
        dt_vars2[str(year)] = ['NAME'] + func.unique(df_vars[df_vars['Year'] == year]['ID2'].to_list())

        
    if import_tab == 'Counties':
        df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype = {'State FIPS':str, 'County FIPS':str})
        df_fips = df_fips[df_fips['State'].isin(df_inputs['states'].values)]
        df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values)) & (df_fips['County Name'].isin(df_inputs['counties'].values))]

        dt_fips = dt_fips[['State FIPS', 'County FIPS']].drop_duplicates().reset_index(drop=True).groupby('State FIPS')['County FIPS'].apply(list).to_dict()    
        for key in list(dt_fips.keys()):
            dt_fips[key] = ",".join(dt_fips[key])
        
        print()
        print('Counties set to import by state:')
        print(dt_fips)
        print()
        print('Variables set to import by year:')
        print(dt_vars)

    if import_tab == 'States':
    
        # Set MSAs to import
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing

        df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype={'State FIPS':str, 'County FIPS':str})
        df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values))]
        states_to_import = [str(state) for state in df_fips['State FIPS'].unique()]
    
        print()
        print("States set to import:")
        print(states_to_import)
        print()
        print("List of variables to import:")
        print(dt_vars)


    print()
    print('Variable Mapping table:')
    display(df_vars.head(3))


    if geography == 'Places':
        geo_id = ['NAME', 'state', 'place']
    if geography == 'Block Groups':
        geo_id = ['NAME', 'state', 'county', 'tract', 'block group']
    if geography == 'Tracts':
        geo_id = ['NAME', 'state', 'county', 'tract']
    if geography == 'Counties':
        geo_id = ['NAME', 'state', 'county']
    if geography == 'MSA':
        geo_id = ['NAME', 'metropolitan statistical area/micropolitan statistical area']
    if geography == 'States':
        geo_id = ['NAME', 'state']


    print("Importing and compiling Decennial data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties
    # reduce all tables/variables pulled into one table

    list_df_years = []

    for year in tqdm(years_to_import):

        list_df_states = []

        if import_tab == 'Counties':
            for state in list(dt_fips.keys()):
                tqdm.write('State: ' + state)
                try:
                    list_df_states.append(
                        get_data(df_urls        = df_urls
                                        , api_key   = api_key
                                        , estimate  = estimate
                                        , sample    = sample_type
                                        , geography = geography
                                        , variables = ','.join(dt_vars[str(year)]) # Should I keep variable org like this?  Then just rename with latest ID names after each pull?  or should I adjust this to ACS style
                                        , year      = year
                                        , state     = state
                                        , county    = dt_fips[state])
                    )
                except Exception as e: print(e)

        if import_tab == 'States':
            for state in states_to_import:
                tqdm.write('State: ' + state)
                try:
                    list_df_states.append(
                        get_data(df_urls        = df_urls
                                        , api_key   = api_key
                                        , estimate  = estimate
                                        , sample    = sample_type
                                        , geography = geography
                                        , variables = ','.join(dt_vars[str(year)])
                                        , year      = year
                                        , state     = state)
                    )
                except Exception as e: print(e)

        df_states = pd.concat(list_df_states)
        df_states = df_states.set_index(geo_id + ['Year']).reset_index()
        df_states.columns = geo_id + ['Year'] + dt_vars2[str(year)][1:]
        list_df_years.append(df_states)
        
    df_census = pd.concat(list_df_years)

    if geography == 'Counties':
        df_census = df_census.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census.drop(['State FIPS', 'County FIPS'], axis=1, inplace=True)
        df_census = df_census.set_index(geo_id + ['County Name', 'Year']).reset_index()

    return df_census







# LEHD ---

def get_lehd(api_key, df_urls, estimate, sample_type, indicator, geography, import_tab, years_to_import):

    df_inputs, file_inputs, file_area = read_inputs_file(import_tab)

    df_vars = read_vars_file(file_inputs, sample_type, indicator, years_to_import, estimate)
    
    variables = df_vars['ID'].unique()
    variables = ','.join(variables)

    if indicator == 'Jobs_4':
        variables = variables + '&ownercode=A05'

    print()
    print("Variables set to import:")
    print(variables)
    print()

    if import_tab == 'Counties':
        
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing

        df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype={'State FIPS':object, 'County FIPS':object})
        df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values)) & (df_fips['County Name'].isin(df_inputs['counties'].values))]

        dt_fips = df_fips[['State FIPS', 'County FIPS']].drop_duplicates().reset_index(drop=True).groupby('State FIPS')['County FIPS'].apply(list).to_dict()
        for key in list(dt_fips.keys()):
            dt_fips[key] = ",".join(dt_fips[key])
    
        print()
        print('Counties set to import by state:')
        print(dt_fips)
        print()

    if import_tab == 'MSA':
    
        df_inputs['msa'] = df_inputs['msa'].astype("str")
        msa_to_import = list(df_inputs['msa'].values)
        df_fips = pd.read_excel(file_area, sheet_name='MSAcodes', dtype={'State FIPS':object, 'MSA_ID':object})
        df_fips = df_fips[['Year', 'State FIPS', 'MSA_ID', 'MSA', 'Abbrv']].drop_duplicates()
        df_fips = df_fips[df_fips['Abbrv'].isin(msa_to_import)]

        dt_fips = df_fips[['State FIPS', 'MSA_ID']].drop_duplicates().drop_duplicates().reset_index(drop=True).groupby('State FIPS')['MSA_ID'].apply(list).to_dict()
        for key in list(dt_fips.keys()):
            dt_fips[key] = ",".join(dt_fips[key])
    
        print()
        print("MSA IDs set to import by state:")
        print(dt_fips)
        print()


    print()
    print('Variable Mapping table:')
    display(df_vars.head(3))


    print("Importing and compiling LEHD data from the Census Bureau...")
    print()

    list_df_states = []
    if import_tab == 'Counties':

        print('Importing by state: ' + ', '.join(list(dt_fips.keys())))
        for state in tqdm(list(dt_fips.keys())):
            try:
                df_state = get_data(df_urls         = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = 'year,'+variables
                                            , year      = 'timeseries'
                                            , state     = state
                                            , county    = dt_fips[state])
                df_state = df_state.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
                df_state = df_state.drop(['state', 'county'], axis=1)
                df_state = df_state.set_index(['State FIPS', 'County FIPS', 'County Name', 'year', 'time']).reset_index()
                list_df_states.append(df_state)
            except Exception as e: print(e)

    if import_tab == 'MSA':

        print('Importing by state: ' + ', '.join(list(dt_fips.keys())))
        for state in tqdm(list(dt_fips.keys())):
            try:
                df_state = get_data(df_urls         = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = 'year,'+variables
                                            , year      = 'timeseries'
                                            , state     = state
                                            , msa       = dt_fips[state])
                df_state = df_state.merge(df_fips[['State FIPS', 'MSA_ID', 'MSA']], left_on=['state', 'metropolitan statistical area/micropolitan statistical area'], right_on=['State FIPS', 'MSA_ID'])
                df_state = df_state.drop(['state', 'metropolitan statistical area/micropolitan statistical area'], axis=1)
                df_state = df_state.set_index(['State FIPS', 'MSA_ID', 'MSA', 'time']).reset_index()
                list_df_states.append(df_state)
            except Exception as e: print(e)
    df_census = pd.concat(list_df_states)
    df_census = df_census.rename(columns = {'year':'Year'})
    df_census = df_census.drop_duplicates(subset=['MSA_ID', 'time', 'Year', 'firmage', 'Emp']).reset_index(drop=True)

    return df_census








# # CPS ---

# def get_cps(api_key, df_urls, estimate, sample_type, indicator, geography, years_to_import, import_tab):

#     df_inputs, file_inputs, file_area = read_inputs_file(import_tab)
    
#     df_vars = pd.read_excel(file_inputs, sheet_name=sample_type)
#     df_vars = df_vars[(df_vars['Year'].isin(years_to_import)) & (df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)) & (df_vars['Include'] == 'Yes')]
        
#     dt_vars = {}
#     for year in years_to_import:
#         dt_vars[str(year)] = func.unique(df_vars[df_vars['Year'] == year]['ID'].to_list()) + [weight]
    
#     # Import County FIPS mapping
#     # Convert to dictionary object for easy state-county combination importing

#     df_fips = pd.read_excel(file_area, sheet_name='CountyFIPS', dtype={'State FIPS':object, 'County FIPS':object})
#     df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values)) & (df_fips['County Name'].isin(df_inputs['counties'].values))]

#     dt_fips = df_fips[['State FIPS', 'County FIPS']].drop_duplicates().reset_index(drop=True).groupby('State FIPS')['County FIPS'].apply(list).to_dict()
#     for key in list(dt_fips.keys()):
#         dt_fips[key] = ",".join(dt_fips[key])
        
#     print(dt_fips)
#     print(dt_vars)


#     print()
#     print('Variable Mapping table:')
#     display(df_vars.head(3))


#     print("Importing and compiling CPS data from the Census Bureau...")
#     print()

#     list_df = []

#     for state in list(dt_fips.keys()):
#         print('State: ' + state)
#         for year in tqdm(years_to_import):
#             try:
#                 list_df.append(
#                     get_data(df_urls        = df_urls
#                                     , api_key   = api_key
#                                     , estimate  = estimate
#                                     , sample    = sample_type
#                                     , geography = geography
#                                     , variables = 'HRHHID,HRHHID2,PERRP,'+','.join(dt_vars[str(year)])
#                                     , year      = year
#                                     , state     = state
#                                     , county    = dt_fips[state])
#                             )
#             except Exception as e: print(e)
                
#     df_census = pd.concat(list_df)
#     df_census['state' ] = df_census['state' ].astype(str).apply('{:0>2}'.format)
#     df_census['county'] = df_census['county'].astype(str).apply('{:0>3}'.format)
#     df_census = df_census.merge(df_fips[['State FIPS', 'MPO', 'County FIPS', 'County Name']]
#                                             , left_on = ['state', 'county']
#                                             , right_on = ['State FIPS', 'County FIPS'])
#     df_census.drop(['State FIPS', 'County FIPS'], axis=1, inplace=True)
#     df_census = df_census.set_index(['state', 'MPO', 'county', 'County Name', 'Year']).reset_index()

#     return df_census





# # Request any ---------------------------------------------------------------------------------------------------------------------------------------------------------


# def get_any(api_key, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab):

#     print(); print(); print()
#     start_time = time.time()

#     file_url = Path(__file__).parent / 'census.xlsx'
#     sheet_name = 'URL'
#     df_urls = pd.read_excel(file_url, sheet_name=sheet_name)

#     if sample_type == 'ACS':
#         df_census = get_acs(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)

#     if geography == 'PUMA':
#         df_census = get_pums(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)
        
#     if sample_type == 'SUBJECT':
#         df_census = get_subject(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)

#     if sample_type == 'DP':
#         df_census = get_dp(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)

#     if estimate == 'DEC':
#         df_census = get_dec(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)

#     if sample_type == 'LEHD':
#         df_census = get_lehd(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)

#     if estimate == 'CPS':
#         df_census = get_cps(api_key, df_urls, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)


#     print()
#     print("Finished!!")
#     print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
#     print()
#     print()
#     print('Summary of data quality: ')
#     print()
#     print("Count of '-555555555'   values in dataframe: " + str((df_census.values == '-555555555'  ).sum()))
#     print("Count of '-666666666'   values in dataframe: " + str((df_census.values == '-666666666'  ).sum()))
#     print("Count of '-222222222'   values in dataframe: " + str((df_census.values == '-222222222'  ).sum()))
#     print("Count of '-999999999.0' values in dataframe: " + str((df_census.values == '-999999999.0').sum()))
#     print("Count of 'null'         values in dataframe: " + str((df_census.values == 'null'        ).sum()))
#     print("Count of '-'            values in dataframe: " + str((df_census.values == '-'           ).sum()))
#     print("Count of ''             values in dataframe: " + str((df_census.values == ''            ).sum()))
#     print("Count of NaN            values in dataframe: " + str( df_census.isna().sum()             .sum()))
#     print()
#     print()

#     df_census = df_census.drop_duplicates().reset_index(drop=True)
#     print('Number of rows/columns: ')
#     print(df_census.shape)
#     print('Years imported: ')
#     print(df_census.Year.unique())

#     return df_census


