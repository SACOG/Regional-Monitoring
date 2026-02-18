

'''

Note: post.py has functions to process the original census bureau data that are unique to how SACOG has defined the indicators,
meaning this is how we wanted to process the data for our own data needs. Functions found in this file may or may not be useful 
to other users that want to pull data from the Census Bureau.

All user defined geographies/variable mappings seen throughout the processing steps are predetermined by the user
in the "census.xlsx" workbook.  This includes which census bureau tables/estimates are being pulled for which indicators,
user defined groupings of unique estimates together, which race/ethnicities to include, and how to sort the variables for a clean/consistent output.

'''


import numpy as np
import pandas as pd
from pathlib import Path
import time
import os
import re
from IPython.display import display

PATH_GIT = Path(__file__).parent.parent.parent.parent
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_GIT / 'Data' / 'Census' / 'config'

FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_CPI = PATH_CONFIG0 / 'CPI_IAF.xlsx'
FILE_INPUTS = PATH_CONFIG / 'census.xlsx'

# SharePoint OneDrive paths
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
PATH_MAIN = PATH_SP / 'Data'
PATH_WEIGHTS = PATH_MAIN / 'Reference' / 'Weights'
PATH_ABOUT = PATH_SP / 'Process Revamp' / 'Task 6. Process Map'

PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')

import sys
sys.path.append(str(PATH_CONFIG0))
import functions as func
import help

sys.path.append(str(PATH_CONFIG))
import get




GEO_SHEETS = {
                    'Block Groups': 'Block Groups'
                        , 'Tracts': 'Tracts'
                        , 'Counties': 'Counties'
                        , 'MPO': 'MPO'
                        , 'States': 'States'
                        , 'National': 'National'
                        , 'Places': 'Places'
                        , 'MSA': 'MSA'
                        , 'Congressional Districts': 'CD'
                        , 'State Legislative Upper Districts': 'SLDU'
                        , 'State Legislative Lower Districts': 'SLDL'
                }

GEOID_ORIG = {
                    'Places': ['state', 'place', 'NAME']
                        , 'Block Groups': ['state', 'County Name', 'county', 'tract', 'block group', 'NAME']
                        , 'Tracts': ['state', 'County Name', 'county', 'tract', 'NAME']
                        , 'Counties': ['state', 'County Name', 'county', 'NAME']
                        , 'MSA': ['MSA_ID', 'MSA']
                        , 'Congressional Districts': ['NAME', 'state', 'congressional district']
                        , 'State Legislative Upper Districts': ['NAME', 'state', 'state legislative district (upper chamber)']
                        , 'State Legislative Lower Districts': ['NAME', 'state', 'state legislative district (lower chamber)']
                        , 'States': ['NAME', 'state']
                        , 'National': ['NAME']
                }

CLEAN_COLS = {
                    'state':'State FIPS'
                        , 'place':'Place ID'
                        , 'county':'County FIPS'
                        , 'tract':'Tract ID'
                        , 'block group':'Block Group ID'
                        , 'congressional district':'Congressional District'
                        , 'state legislative district (upper chamber)':'State Legislative Upper District'
                        , 'state legislative district (lower chamber)':'State Legislative Lower District'
                        , 'metropolitan statistical area/micropolitan statistical area':'MSA_ID'
                        , 'COUNTYNAME': 'County Name'
                    }

GEOID_CLEAN = {
                    'Places': ['State FIPS', 'County Name', 'Place ID', 'NAME']
                        , 'Block Groups': ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'Block Group ID', 'NAME']
                        , 'Tracts': ['State FIPS', 'County FIPS', 'County Name', 'Tract ID', 'NAME']
                        , 'Counties': ['State FIPS', 'MPO', 'County FIPS', 'County Name', 'NAME']
                        , 'MSA': ['MSA_ID', 'MSA']
                        , 'Congressional Districts': ['State FIPS', 'Congressional District', 'NAME']
                        , 'State Legislative Upper Districts': ['State FIPS', 'State Legislative Upper District', 'NAME']
                        , 'State Legislative Lower Districts': ['State FIPS', 'State Legislative Lower District', 'NAME']
                        , 'States': ['State FIPS', 'NAME']
                        , 'National': ['NAME']
                }








## ACS -------------------------------------------------------------------------------------------------------------------------------------------------------


'''
User defined functions to clean ACS tables immediately after query
Replaces weird missing values with np.nan, drops rows with all missing
Melts data from wide to long
Merges clean variable mapping, race/ethnicity label, and sorting assignment
Adjusts dollars for inflation as needed
'''


def acs_convert_to_nan(df):

    print('Converting all missing formatted values to np.nan...')

    df = df.replace('-666666666'  , np.nan)
    df = df.replace('-666666666.0', np.nan)
    df = df.replace( -666666666.0 , np.nan)
    df = df.replace('-222222222'  , np.nan)
    df = df.replace('-222222222.0', np.nan)
    df = df.replace( -222222222.0 , np.nan)
    df = df.replace( '-333333333' , np.nan)
    df = df.replace( -333333333.0 , np.nan)
    df = df.replace('-555555555'  , np.nan)
    df = df.replace( -555555555.0 , np.nan)
    df = df.replace('-999999999.0', np.nan)
    df = df.replace( -999999999.0 , np.nan)
    df = df.replace('null', np.nan)
    df = df.dropna(axis=1, how='all')

    return df


def acs_clean_cols(df, params):

    print('Renaming geography fields to common type...')
    df = df.rename(columns=CLEAN_COLS)
    if params['geo'] == 'MSA':
        df = df.rename(columns={'NAME':'MSA'})
    if params['geo'] == 'Places':
        df['County Name'] = 'placeholder'

    return df


def acs_match_county_to_mpo(df, params):

    if params['geo'] == 'Counties': # changed from params['geo'] to params['import_tab']

        print('Matching counties to their respective MPO...')

        df_inputs = pd.read_excel(FILE_INPUTS, sheet_name=params['import_tab'])
        df_fips = pd.read_excel(FILE_AREA, sheet_name='CountyFIPS', dtype={'STATEFP':str, 'COUNTYFP':str})
        df_fips = df_fips.rename(columns={'STATE':'State', 'STATEFP':'State FIPS', 'COUNTYFP':'County FIPS', 'COUNTYNAME':'County Name'})
        df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values)) & (df_fips['County Name'].isin(df_inputs['counties'].values))]

        df_mpo = df_fips[['County Name', 'MPO']]
        df = df.merge(df_mpo, on=['County Name'], how='left')

        # dt_fips = df_fips[['State FIPS', 'County FIPS']].drop_duplicates().reset_index(drop=True).groupby('State FIPS')['County FIPS'].apply(list).to_dict()
        # for key in list(dt_fips.keys()): dt_fips[key] = ",".join(dt_fips[key])

    return df


def acs_merge_vars_labels(df, params, df_vars):

    print('Merging ACS common variable names (and user defined groups) onto their estimate IDs...')

    df = pd.melt(df, id_vars = GEOID_CLEAN[params['geo']] + ['Year'], var_name='Estimate ID', value_name='Total')
    df = df.dropna()
    df['Total'] = df['Total'].apply(pd.to_numeric)
    df['Year'] = df['Year'].astype(int)
    df = df.merge(df_vars.rename(columns={'ID2':'Estimate ID'}), on=['Year', 'Estimate ID'], how='left')
    df = df.drop_duplicates()

    return df


def acs_moe_reshape(df, params):

    print('Reshaping data to include Margin of Error estimates, if needed...')

    if params['moe']:
        df_me = df[ df['Label'].isna()].reset_index(drop=True)
        df    = df[~df['Label'].isna()].reset_index(drop=True)
        df_me = df_me[['Estimate ID'] + GEOID_CLEAN[params['geo']] + ['Year', 'Total']].rename(columns={'Total':'MOE'})
        df_me['Estimate ID'] = df_me['Estimate ID'].apply(lambda s : re.sub("M", "E", s))
        df = df.merge(df_me, on=['Estimate ID'] + GEOID_CLEAN[params['geo']] + ['Year'], how='left')
        df = df[list(df.drop(['Total', 'MOE'], axis=1).columns) + ['Total', 'MOE']]
        df.loc[df['MOE'] < 0, 'MOE'] = np.nan
        
    if not params['moe']:
        df = df[list(df.drop(['Total'], axis=1).columns) + ['Total']]

    cols_to_keep = ['Estimate ID'] + GEOID_CLEAN[params['geo']] + ['Year', 'Variable', 'Race/Ethnicity', 'Sort', 'Total']
    if params['moe']: cols_to_keep = cols_to_keep + ['MOE']
    df = df[cols_to_keep]

    df['Total'] = df['Total'].fillna(0) # TODO: quality control on this step, does it make sense to do this?
    

    df = df.reset_index(drop=True)

    return df



'''
User defined functions to process ACS tables for SACOG specific indicator's
Maps the Estimate ID's from the Census Bureau to cleaned label fields, rolls up groupings, race/ethnicity mappings, and sorting order
For any indicator involving money ($-USD), adjusts for inflation based on latest year
For any indicator involving rolls ups that need to be weighted by the population by params['geo'], imports and merges population params['estimate']s
'''


def acs_cpi_adjust(df, params):

    print('Adjusting dollar estimates for inflation using the CPI...')

    if params['indicator'] in ['Income_1']:#, 'Chamber_H_5']:
        df_cpi = pd.read_excel(FILE_CPI, sheet_name='BLS_West')
        df_cpi = df_cpi[['Year', 'IAF_' + str(params['end_year'])]]
        df = df.merge(df_cpi, on='Year', how='left')
        df['Total'] = round(df['Total']*df['IAF_' + str(params['end_year'])])
        df['MOE'  ] = round(df['MOE'  ]*df['IAF_' + str(params['end_year'])])
        df = df.drop(['IAF_' + str(params['end_year'])], axis=1)

        return df



def acs_merge_place_codes(df, params):

    if params['geo'] == 'Places':

        print('Matching place names to their appropriate jurisdiction geographies (counties, FIPS codes, MPO, etc...)...')

        df = df.drop('County Name', axis=1)
        df_codes = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
        if params['unincorporated']:
            df_codes = df_codes[(df_codes['MPO'].str.contains('SACOG')) & (df_codes['Incorporated'] == 'Yes')]
        df_codes['place'] = df_codes['place'].astype(str).apply('{:0>5}'.format)
        CDP_to_keep = list(df_codes['place'].unique())
        df = df[df['Place ID'].isin(CDP_to_keep)]
        df_codes = df_codes.rename(columns={'place':'Place ID'})

        df_codes = df_codes[['Year', 'Place ID', 'County Name']]

        df_codes2010 = df_codes[df_codes['Year'] == 2010]
        df_codes2020 = df_codes[df_codes['Year'] == 2020]

        df_2010 = df[df['Year'] <  2020]
        df_2020 = df[df['Year'] >= 2020]

        df_2010 = df_2010.merge(df_codes2010.drop('Year', axis=1), on='Place ID', how='left')
        df_2020 = df_2020.merge(df_codes2020.drop('Year', axis=1), on='Place ID', how='left')

        df = pd.concat([df_2020, df_2010])

        df['NAME'] = df['NAME'].str.replace(' CDP, California' , '', regex=True)
        df['NAME'] = df['NAME'].str.replace(' town, California', '', regex=True)
        df['NAME'] = df['NAME'].str.replace(' city, California', '', regex=True)
        df = df.drop_duplicates()
        
        return df
    


def acs_merge_weights(df, params):

    if params['weight']:

        print('Merging weights (population or household estimates) onto main dataset for future aggregation step...')

        file_weights = PATH_WEIGHTS / f'Total_{params['weight']} {params['geo']} {params['estimate']}.xlsx' # _ChamberStudy2026.xlsx
        df_weight = pd.read_excel(file_weights, sheet_name=GEO_SHEETS[params['geo']])

        if params['geo'] == 'MSA': field_id = 'MSA_ID'
        else: field_id = 'NAME'
        
        df_weight = df_weight[[field_id, 'Year','Race/Ethnicity', params['weight']]]
        if params['weight'] == 'Population':
            conditions = [
                            (df_weight["Race/Ethnicity"] == 'All'                                           ),
                            (df_weight["Race/Ethnicity"] == 'American Indian or Alaska Native (NH)'         ),
                            (df_weight["Race/Ethnicity"] == 'Asian (NH)'                                    ),
                            (df_weight["Race/Ethnicity"] == 'Black or African American (NH)'                ),
                            (df_weight["Race/Ethnicity"] == 'Hispanic or Latino'                            ),
                            (df_weight["Race/Ethnicity"] == 'Native Hawaiian or other Pacific Islander (NH)'),
                            (df_weight["Race/Ethnicity"] == 'White (NH)'                                    ),
                            (df_weight["Race/Ethnicity"] == 'Some other race (NH)'                          ),
                            (df_weight["Race/Ethnicity"] == 'Two or more races (NH)'                        )
                        ]
            choices = ["All", "American Indian or Alaska Native", "Asian", "Black or African American", "Hispanic or Latino",
                        "Native Hawaiian or other Pacific Islander", "White (NH)", "Some other race", "Two or more races"]
            df_weight["Race/Ethnicity"] = np.select(conditions, choices)          
        
        df = df.merge(df_weight, on=[field_id, 'Year', 'Race/Ethnicity'], how='left').drop_duplicates()

        if params['indicator'] in ['Chamber_H_5', 'Chamber_H_7']:
            df_hisp = df[df['Race/Ethnicity'] == 'Hispanic or Latino']
            df_hisp = df_hisp[GEOID_CLEAN[params['geo']] + ['Year', 'Households']]
            df_hisp = df_hisp.rename(columns={'Households':'Hispanic Households'})
            df = df.merge(df_hisp, on=GEOID_CLEAN[params['geo']]+['Year'], how='left')
            df.loc[df['Race/Ethnicity'] == 'All', 'Households'] = df['Households'] - df['Hispanic Households']
            df = df.drop('Hispanic Households', axis=1)
            if params['indicator'] == 'Chamber_H_5':
                conditions = [
                        (df["Race/Ethnicity"] == 'All'               ),
                        (df["Race/Ethnicity"] == 'Hispanic or Latino')
                    ]
                choices = ["Not Hispanic or Latino", "Hispanic or Latino"]
                df["Race/Ethnicity"] = np.select(conditions, choices)

        df[params['weight']] = df[params['weight']].fillna(0).replace(0, 1) # TODO: need quality control on this step, does it actually make sense to do this?
    
    return df



'''
User defined functions to aggregate ACS estimates
Rolls up population/household counts and standard errors and calculates percentages based on user defined geography/variable mappings
'''

def acs_rollup(df, params):

    x = df['Total'].to_numpy()

    if params['moe']:
        se = df['MOE'].to_numpy()

    if not params['weight']:
        est = np.sum(x)
        if params['moe']:
            est_se = np.sqrt(np.sum(se**2))

    if params['weight']:
        w = df[params['weight']].to_numpy()
        est_w = np.sum(w)
        est = np.average(x, weights=w)
        if params['moe']:
            est_se = np.sqrt(np.sum((w**2) * (se**2))) / np.sum(w)

    if not params['moe'] and not params['weight']:
        return pd.Series({'Total': est})
    if not params['moe'] and params['weight']:
        return pd.Series({'Total': est, params['weight']: est_w})
    if params['moe'] and not params['weight']:
        return pd.Series({'Total': est, 'MOE': est_se})
    if params['moe'] and params['weight']:
        return pd.Series({'Total': est, 'MOE': est_se, params['weight']: est_w})



def calculate_ME_ratio(df, params):

    if params['moe']:
        df['MOE_ratio'] = df['MOE']/df['Total']
        conditions = [
            (df['Race/Ethnicity'] == 'All') & (len(df['Race/Ethnicity'].unique()) > 1)
            , df['MOE_ratio'] <= params['moe_thresh']
            , df['MOE_ratio']  > params['moe_thresh']
        ]
        choices = ['Yes', 'Yes', 'No']
        df['Use for Reporting'] = np.select(conditions, choices, default='No')

    return df



def acs_calculate_unincorporated(df, params):

    if params['geo'] == 'Places':

        if params['unincorporated']: # TODO: Need to figure out if I can get around this weird file name problem

            print('Calculating estimates for unincorporated communities...')
        
            if params['sample'] == 'SUBJECT':
                params['estimate'] = re.sub('ACS', 'SUBJECT', params['estimate'])
            if params['sample'] == 'DP':
                params['estimate'] = re.sub('ACS', 'DP', params['estimate'])

            if params['project'] == 'Monitoring and Reporting':
                file_counties = PATH_SERVER / f'{params['indicator']} Counties {params['estimate']}.xlsx'
            else:
                file_counties = Path(params['export_loc']) / f'{params['indicator']} Counties {params['estimate']}.xlsx'

            if params['sample'] == 'SUBJECT':
                params['estimate'] = re.sub('SUBJECT', 'ACS', params['estimate'])
            if params['sample'] == 'DP':
                params['estimate'] = re.sub('DP', 'ACS', params['estimate'])

            if params['indicator'] == 'Income_1':

                ## Need to include weighted average of unincorporated areas properly for things like income
                # County Average Household Income = ((Unincorporated Average Household Income)*(Unincorporated Population) + (Incorporated Average Household Income)*(Incorporated Population)) / (County Population)
                # Unincorporated Average Household Income = ((County Average Household Income)*(County Population) - (Incorporated Average Household Income)*(Incorporated Population)) / (Unincorporated Population)
                
                # Import County average household income
                # Calculate incorporated average household income and total households
                # Import total households in county
                # Subtact total incorporated county households from total county households to get total unincorporated county households

                df_counties = pd.read_excel(file_counties, sheet_name='Counties')
                df_counties = df_counties[['County Name', 'Year', 'Race/Ethnicity', 'Median Household Income', 'Margin of Error']].rename(columns={'Median Household Income':'Median Household Income County', 'Margin of Error':'MOE County'})
                
                df_inc1 = df.groupby(['County Name', 'Year', 'Race/Ethnicity', 'Variable'], as_index=False, sort=False).apply(lambda x: acs_rollup(x, params))
                df_inc1 = df_inc1.drop(['Variable', params['weight']], axis=1).rename(columns={'Total':'Median Household Income Inc', 'MOE':'MOE Inc'})
                file_cdp_pop = PATH_WEIGHTS / f'Total_{params['weight']} {params['geo']} {params['estimate']}.xlsx'
                df_inc_pop = pd.read_excel(file_cdp_pop, sheet_name=GEO_SHEETS[params['geo']])
                df_inc_pop = df_inc_pop[['County Name', 'Place ID', 'NAME', 'Year','Race/Ethnicity', params['weight']]]
                list_cdp_inc = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
                list_cdp_inc = list_cdp_inc[(list_cdp_inc['MPO']=='SACOG') & (list_cdp_inc['Year']==2020) & (list_cdp_inc['Incorporated']=='Yes')]
                list_cdp_inc['NAME'] = list_cdp_inc['NAME'].str.replace(' city', '')
                list_cdp_inc['NAME'] = list_cdp_inc['NAME'].str.replace(' town', '')
                list_cdp_inc = list(list_cdp_inc.NAME.unique())
                df_inc_pop = df_inc_pop[df_inc_pop['NAME'].isin(list_cdp_inc)]
                df_inc_pop = df_inc_pop.groupby(['County Name', 'Year', 'Race/Ethnicity'], as_index=False)['Households'].sum()

                file_cdp_pop = PATH_WEIGHTS / f'Total_{params['weight']} Counties {params['estimate']}.xlsx'
                df_counties_pop = pd.read_excel(file_cdp_pop, sheet_name='Counties')
                df_counties_pop = df_counties_pop[['County Name', 'Year','Race/Ethnicity', params['weight']]]

                df_all_households = df_counties_pop.merge(df_inc_pop.rename(columns={'Households':'Households Inc'}), on=['County Name', 'Year', 'Race/Ethnicity'])
                df_all_households['Households Uninc'] = df_all_households['Households'] - df_all_households['Households Inc']

                df_all_income = df_counties.merge(df_inc1, on=['County Name', 'Year', 'Race/Ethnicity'])
                df_all = df_all_income.merge(df_all_households, on=['County Name', 'Year', 'Race/Ethnicity'])

                def calculate_uninc_income(county_income, county_households, incorp_income, incorp_households, unincorp_households):
                    try: unincorp_income = ((county_income)*(county_households) - (incorp_income)*(incorp_households)) / (unincorp_households)
                    except: unincorp_income = 999999
                    return unincorp_income
                
                def calculate_uninc_income_me(county_me, county_hh, incorp_me, incorp_hh, uninc_hh):
                    try:
                        term1 = (county_hh / uninc_hh)**2 * county_me**2
                        term2 = (incorp_hh / uninc_hh)**2 * incorp_me**2
                        return np.sqrt(term1 + term2)
                    except:
                        return np.nan
                df_all['Median Household Income Uninc'] = df_all.apply(lambda x: calculate_uninc_income(x['Median Household Income County'], x['Households'], x['Median Household Income Inc'], x['Households Inc'], x['Households Uninc']), axis=1)
                if params['moe']: df_all['Median Household Income Uninc MOE'] = df_all.apply(lambda x: calculate_uninc_income_me(x['MOE County'], x['Households'], x['MOE Inc'], x['Households Inc'], x['Households Uninc']), axis=1)
                df_uninc = df_all[['County Name', 'Year', 'Race/Ethnicity', 'Median Household Income Uninc', 'Median Household Income Uninc MOE', 'Households Uninc']].rename(columns={'Median Household Income Uninc':'Total', 'Median Household Income Uninc MOE':'MOE', 'Households Uninc':'Households'})
                df_uninc[['State FIPS', 'Variable', 'Place ID', 'NAME', 'Sort']] = '06', 'Median household income in the past 12 months (in inflation-adjusted dollars by year)', 'Unincorporated', 'Unincorporated', 1
                df_uninc = calculate_ME_ratio(df_uninc, params)
                df = pd.concat([df, df_uninc])

            else:

                # if params['indicator'] == 'RHNA_HSG_10': col_var = 'Median Contract Rent'
                # else: col_var = 'Median Household Income'

                df_inc1 = df.groupby(['State FIPS', 'County Name', 'Year', 'Race/Ethnicity', 'Variable'], as_index=False, sort=False).apply(lambda x: acs_rollup(x, params))
                df_counties = pd.read_excel(file_counties, sheet_name='Counties')
                if not params['moe']:
                    df_inc1 = df_inc1.merge(df_counties[['County Name', 'Year', 'Race/Ethnicity', 'Variable', params['metric']]], on=['County Name', 'Year', 'Race/Ethnicity', 'Variable'], how='left')
                if params['moe']: 
                    df_inc1 = df_inc1.merge(df_counties[['County Name', 'Year', 'Race/Ethnicity', 'Variable', params['metric'], 'Margin of Error']], on=['County Name', 'Year', 'Race/Ethnicity', 'Variable'], how='left')
                    df_inc1['diff_ME'] = np.sqrt(df_inc1['Margin of Error']**2 + df_inc1['MOE']**2)
                df_inc1['diff'] = df_inc1[params['metric']] - df_inc1['Total']
                df_inc1['Place ID'] = 'Unincorporated'
                df_inc1['NAME'    ] = 'Unincorporated'
                if not params['moe']:
                    df_uninc = df_inc1[['State FIPS', 'County Name', 'Place ID', 'NAME', 'Year', 'Race/Ethnicity', 'Variable', 'diff']].rename(columns={'diff': 'Total'})
                if params['moe']:
                    df_uninc = df_inc1[['State FIPS', 'County Name', 'Place ID', 'NAME', 'Year', 'Race/Ethnicity', 'Variable', 'diff', 'diff_ME']].rename(columns={'diff': 'Total', 'diff_ME':'MOE'})
                    df_uninc = calculate_ME_ratio(df_uninc, params)
                df = pd.concat([df, df_uninc])
    
    df = df.reset_index(drop=True)

    return df



def acs_aggregate(df, params):


    print('Aggregating and rolling up across groupings and geographies, as needed...')

    df = df.groupby(GEOID_CLEAN[params['geo']] + ['Year', 'Race/Ethnicity', 'Variable', 'Sort'], as_index=False, sort=False).apply(lambda x: acs_rollup(x, params))


    if params['indicator'] == 'Income_4':
        df_all = df[df['Year'].isin([2009, 2010, 2011, 2012])].groupby(GEOID_CLEAN[params['geo']] + ['Year', 'Variable', 'Sort'], as_index=False, sort=False).apply(lambda x: acs_rollup(x, params))
        df_all.loc[:, 'Race/Ethnicity'] = 'All'
        df = pd.concat([df, df_all])
    

    if params['moe']:
        df = calculate_ME_ratio(df, params)

    if params['geo'] == 'Counties':
        if params['mpo']:
            df_mpo = df.groupby(['State FIPS', 'MPO', 'Year', 'Race/Ethnicity', 'Variable', 'Sort'], as_index=False, sort=False).apply(lambda x: acs_rollup(x, params))
            df_mpo[['County FIPS', 'County Name', 'NAME']] = 'MPO', 'MPO', 'MPO'
            if params['moe']:
                df_mpo = calculate_ME_ratio(df_mpo, params)
            df = pd.concat([df, df_mpo])

    if params['geo'] == 'Places':
        df = acs_calculate_unincorporated(df, params)

    df = df.drop_duplicates()
    df = df.replace([np.inf, -np.inf, 0], np.nan)

    if params['pct']:
        if params['num_vars'] == 1:
            df['Percent'] = df['Total'] / df[df['Race/Ethnicity'] != 'All'].groupby(GEOID_CLEAN[params['geo']] + ['Year'])['Total'].transform('sum')
        if params['num_vars'] > 1:
            df['Percent'] = df['Total'] / df.groupby(GEOID_CLEAN[params['geo']] + ['Year', 'Race/Ethnicity'])['Total'].transform('sum')


    return df




def sort_table(df, params):
    
    '''
    User defined function to do final clean-up, renaming, sorting, organizing of Census Bureau tables
    '''

    print('Sorting by sort fields for consistency in outputs...')

    df['Race/Ethnicity_sort'] = pd.Categorical(df['Race/Ethnicity'], ['All'
                                                                        , 'American Indian or Alaska Native'
                                                                        , 'American Indian or Alaska Native (NH)'
                                                                        , 'Asian'
                                                                        , 'Asian (NH)'
                                                                        , 'Black or African American'
                                                                        , 'Black or African American (NH)'
                                                                        , 'Hispanic or Latino'
                                                                        , 'Native Hawaiian or other Pacific Islander'
                                                                        , 'Native Hawaiian or other Pacific Islander (NH)'
                                                                        , 'White'
                                                                        , 'White (NH)'
                                                                        , 'Some other race'
                                                                        , 'Some other race (NH)'
                                                                        , 'Two or more races'
                                                                        , 'Two or more races (NH)'
                                                                    ])
    if params['geo'] == 'MSA':
        df = df.sort_values(by= ['MSA_ID']+['Year', 'Race/Ethnicity_sort', 'Sort'], ascending=[True]+[False, True, True])
    else:
        df = df.sort_values(by= GEOID_CLEAN[params['geo']]+['Year', 'Race/Ethnicity_sort', 'Sort'], ascending=[item in GEOID_CLEAN[params['geo']] for item in GEOID_CLEAN[params['geo']]]+[False, True, True])
    df = df.drop(['Race/Ethnicity_sort', 'Sort'], axis=1).reset_index(drop=True)
    if 'Percent' in df.columns:
        df = help.move_column_after(df, 'Percent', 'Total')
    if params['project'] == 'Monitoring and Reporting':
        if params['geo'] not in ['MSA', 'Places']:
            df = df.drop('NAME', axis=1)
    df = df.rename(columns={'Total': params['metric'], 'MOE':'Margin of Error', 'MOE_ratio':'Margin of Error Ratio', 'MSA_ID':'MSA ID'})

    return df




def acs_main(df, params, df_vars):

    '''
    Main function to used process requested ACS data
    '''

    print(); print('Post processing for ACS data:'); print()

    df = acs_convert_to_nan(df)

    df = acs_clean_cols(df, params)
    
    if params['geo'] == 'Counties':
        df = acs_match_county_to_mpo(df, params)
    
    df = acs_merge_vars_labels(df, params, df_vars)
    df = acs_moe_reshape(df, params)

    df = help.clean_fips(df)

    if params['adjust_cpi']:
        df = acs_cpi_adjust(df, params)

    if params['geo'] == 'Places':
        df = acs_merge_place_codes(df, params)

    if params['weight']:
        df = acs_merge_weights(df, params)

    df = acs_aggregate(df, params)
    df = sort_table(df, params)

    help.print2()
    time.sleep(5)
    print('Final table:')
    display(df)
    help.print2()
    time.sleep(5)

    return df



def acs_export(df, params):

    help.print2()
    workbooks = set_workbook_name(params)

    path_out_sp = Path(params['export_loc']) / f"{params['indicator']} {params['folder']}"
    if params['project'] != 'Monitoring and Reporting':
        path_out_sp = Path(params['export_loc'])
    if params['project'] == 'Monitoring and Reporting' and params['server']: paths = [PATH_SERVER, path_out_sp]
    else: paths = [path_out_sp]

    if params['geo'] == 'Counties' and params['mpo']:
        df_mpo = df[df['County Name']=='MPO'].reset_index(drop=True).drop(['County FIPS', 'County Name'], axis=1)
        df     = df[df['County Name']!='MPO'].reset_index(drop=True)

    for path_ in paths:

        if params['geo'] == 'Counties' and params['mpo']:
            params['path_wb'] = path_ / workbooks[1]
            export_indicator(df_mpo, params)

        params['path_wb'] = path_ / workbooks[0]
        export_indicator(df, params)







## PUMS -----------------------------------------------------------------------------------------------------------------------------------------------------------------



def misc_groups():

    group_puma     = ['State FIPS', 'MPO', 'PUMA'       , 'PUMA NAME'  ]
    group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
    group_msa      = [                     'MSA_ID'     , 'MSA'        ] # Dropped State FIPS
    group_mpo      = [              'MPO'                              ] # Dropped State FIPS

    return group_puma, group_counties, group_msa, group_mpo




def pums_clean_data(df, params, weight, df_vars):

    '''
    User defined function to do initial cleaning of PUMS tables
    Cleans the FIPS codes fields
    Subsets to head of household (LEHD)
    Reassigns raw variable values with the descriptio on user defined params['geo']/variable mappings
    '''

    print('Cleaning FIPS codes fields and variable descriptions...')

    groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
    groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

    if params['sample'] == 'PUMS':
        df['PUMA'] = df['PUMA'].astype(str).apply('{:0>5}'.format)
        df[weight] = df[weight].astype(int)

    # if params['sample'] == 'FOODSEC':
    #     df['Household_ID'] = df['HRHHID'].map(str) + '-' + df['HRHHID2'].map(str)
    #     df = df.drop(['HRHHID', 'HRHHID2'], axis=1)
    #     df['Householder'] = df.groupby(['Household_ID', 'Year'], as_index=False)['PERRP'].transform(min)
    #     df = df[df['PERRP'] == df['Householder']]
    #     df = df.drop_duplicates(['Household_ID', 'Year'])

    for group in groups2:
        df[group] = df[group].astype(int).astype(str).apply('{:0>2}'.format)

    df_vars  ['Value1'] = df_vars  ['Value1'].astype(str).apply('{:0>2}'.format)
    df['state' ] = df['state' ].astype(str).apply('{:0>2}'.format)

    if params['sample'] == 'PUMS':
        df[weight] = df[weight].astype(int)
    # if params['sample'] == 'FOODSEC':
    #     df[weight] = df[weight].astype('float')
    df[groups2] = df[groups2].astype("string")

    df_vars2 = df_vars.pivot_table(index=['Year', 'Value1'], columns='ID2', values='Description2', aggfunc = lambda x: x).reset_index()
    cols = ['Year', 'Value1'] + groups2
    df_vars2 = df_vars2[cols]

    list_values = []
    for group in groups2:
        list_values = list_values + list(df[group].values)
    set_values = set(list_values)

    df_vars2 = df_vars2[df_vars2['Value1'].isin(set_values)]
    df_vars2 = df_vars2.add_suffix('_desc').rename(columns={'Value1_desc':'Value1', 'Year_desc':'Year'})

    for col in cols[2:]:
        df = df.merge(df_vars2[['Value1', col+'_desc', 'Year']], left_on=[col, 'Year'], right_on=['Value1', 'Year'], how='inner')
        df[col] = df[col+'_desc']
        df = df.drop(['Value1', col+'_desc'], axis=1)

    return df, groups




def pums_cw_to_geos(df, params, groups):

    '''
    User defined function to process PUMS tables
    Maps area codes together
    Links PUMA codes to county FIPS codes by year
    Then maps the county FIPS codes to MSA IDs
    '''
    print('Mapping PUMA codes to other area codes...')

    df_fips, dt_fips = get.read_fips_file_pums(params)
    
    # df = df.dropna()
    df = df.rename(columns={'state':'State FIPS', 'county':'County FIPS'})

    if params['sample'] == 'PUMS':
        df_fips_pums = pd.read_excel(FILE_AREA, sheet_name='PUMAcodes', dtype={'STATEFP': object, 'COUNTYFP': object, 'TRACTCE': object, 'PUMA5CE': object})
        df_fips_pums = df_fips_pums[df_fips_pums['STATEFP'].isin(list(dt_fips.keys()))]
        df_fips_pums = df_fips_pums[['STATEFP', 'PUMA5CE', 'PUMA NAME', 'COUNTYFP', 'Years']].rename(columns={'PUMA5CE':'PUMA', 'STATEFP':'State FIPS', 'COUNTYFP':'County FIPS'}).drop_duplicates()

        if params['estimate'] in ['ACS5', 'PUMS5']:
            df1 = df[df['Year'].isin(help.sequence(2012, 2021, 1))]
            df2 = df[df['Year'].isin(help.sequence(2022, 2031, 1))]
        else:
            df1 = df[df['Year'].isin(help.sequence(2010, 2020, 1))]
            df2 = df[df['Year'].isin(help.sequence(2021, 2030, 1))]

        df1 = df1.merge(df_fips_pums[df_fips_pums['Years'] == '2012-2021'], on=['State FIPS', 'PUMA'], how='left')
        df2 = df2.merge(df_fips_pums[df_fips_pums['Years'] == '2022-2031'], on=['State FIPS', 'PUMA'], how='left')
        df = pd.concat([df1, df2])
        df = df.drop('Years', axis=1)
        df['County FIPS'] = df['County FIPS'].astype(str).apply('{:0>3}'.format)
        df = df.merge(df_fips[['State FIPS', 'MPO', 'County FIPS', 'County Name', 'MSA_ID', 'MSA_acs']].drop_duplicates(), on=['State FIPS', 'County FIPS'])
        df = df.rename(columns={'MSA_acs':'MSA'})
        df = df.set_index(['State FIPS', 'MPO', 'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'Year']).reset_index()
        df = df.sort_values(['State FIPS', 'PUMA', 'Year'] + groups, ascending=[True, True, False] + [item in groups for item in groups])
    
    # if params['sample'] == 'FOODSEC':
    #     df = df.sort_values(['State FIPS', 'MPO', 'County FIPS', 'Year'] + groups, ascending=[True, True, True, False] + [item in groups for item in groups])

    return df



'''
User defined functions to clean grouping fields of PUMS tables
Adjusts the race/ethnicity field to include hispanic or latino
Creates new groups for Cost_6 indicator
Adjusts $USD fields for inflation to the latest year (creates groupings as needed)
'''

def pums_clean_eth_groups(df, params, groups):

    if 'HISP' in groups:
        if params['project'] == 'Monitoring and Reporting':
            df.loc[df['HISP'] == 'Hispanic or Latino', 'RAC1P'] = 'Hispanic or Latino'
            df = df.drop('HISP', axis=1)
            groups.remove('HISP')
        # if params['project'] == 'Chamber Study Missions': ## HERE
        #     df.loc[df['HISP'] == 'Hispanic or Latino', 'RAC1P'] = 'Hispanic or Latino'
        #     df = df.drop('HISP', axis=1)
        #     groups.remove('HISP')

    if 'HHLDRHISP' in groups:
        df.loc[df['HHLDRHISP'] == 'Hispanic or Latino', 'HHLDRRAC1P'] = 'Hispanic or Latino'
        df = df.drop('HHLDRHISP', axis=1)
        groups.remove('HHLDRHISP')

    if 'PEHSPNON' in groups:
        df.loc[df['PEHSPNON'] == 'Hispanic or Latino', 'PTDTRACE'] = 'Hispanic or Latino'
        df = df.drop('PEHSPNON', axis=1)
        groups.remove('PEHSPNON')

    return df, groups


def pums_cpi_adjust(df, params):

    if params['indicator'] in ['Income_2', 'Accessibility_2', 'Accessibility_4']:

        print('Adjusting income estimates for inflation...')

        df_cpi = pd.read_excel(os.path.join(PATH_CONFIG0, 'CPI_IAF.xlsx'), sheet_name='BLS_West')
        df_cpi = df_cpi[['Year', 'IAF_2024']]

        df = df.merge(df_cpi, on='Year', how='left')
        cols = ['HINCP', 'ADJINC']
        df[cols] = df[cols].astype('float32')
        df['HINCP'] = df['HINCP']*df['ADJINC']*df['IAF_2024']
        df = df.drop(['IAF_2024', 'ADJINC'], axis=1)

    return df



def pums_assign_own_vs_rent(df, params, groups):

    if params['indicator'] == 'Cost_6':
        cols = ['GRPIP', 'OCPIP']
        df[cols] = df[cols].astype(int)
        conditions = [
                        ( (df['WGTP' ] == 0) ),
                        ( (df['GRPIP'] == 0) & (df['OCPIP'] == 0) ),
                        ( (df['GRPIP'] == 0) & (df['OCPIP']  > 0) ),
                        ( (df['OCPIP'] == 0) & (df['GRPIP']  > 0) )
                    ]
        choices = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Owner', 'Renter']
        df["housing_type"] = np.select(conditions, choices)
        conditions = [
                        (  (df['WGTP' ] ==  0) ),
                        (  (df['GRPIP'] ==  0) & (df['OCPIP'] == 0)),
                        ( ((df['GRPIP'] ==  0) & (df['OCPIP'] <= 30)) | ((df['OCPIP'] ==  0) & (df['GRPIP'] <= 30)) ),
                        ( ((df['GRPIP']  > 30) & (df['GRPIP'] <= 50)) | ((df['OCPIP']  > 30) & (df['OCPIP'] <= 50)) ),
                        (  (df['GRPIP']  > 50) | (df['OCPIP']  > 50) )
                    ]
        choices = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Cost burden <=30%', 'Cost burden >30% to <=50%', 'Cost burden >50%']
        df["housing_burden"] = np.select(conditions, choices)
        df = df.drop(['GRPIP', 'OCPIP'], axis=1)
        # groups = list(map(lambda x: x.replace('GRPIP', 'housing_type'  ), groups))
        # groups = list(map(lambda x: x.replace('OCPIP', 'housing_burden'), groups))
        groups = ['RAC1P', 'housing_type', 'housing_burden']

    return df, groups


def pums_income_brackets(df, params, groups):

    if params['indicator'] in ['Income_2', 'Accessibility_2', 'Accessibility_4']:

        df_income_brackets = pd.read_excel(os.path.join(PATH_CONFIG0, 'CA_state_income_brackets_by_household_size.xlsx'), sheet_name='Table')
        df_income_brackets['County'].fillna(method='ffill', inplace=True)
        df_income_brackets['County'] = df_income_brackets['County'].str.replace(' County.*'         , '' , regex = True)
        df_income_brackets['County'] = df_income_brackets['County'].str.replace('\n'                , ' ', regex = True)
        df_income_brackets['AMI'   ] = df_income_brackets['County'].str.extract('\$?([0-9,]+)[.%]?')
        df_income_brackets['AMI'   ] = df_income_brackets['AMI'   ].str.replace(','                 , '' , regex = True)
        df_income_brackets['County'] = df_income_brackets['County'].str.replace(' \$?([0-9,]+)[.%]?', '' , regex = True)
        df_income_brackets = pd.melt(df_income_brackets, id_vars = ['County', 'Income Bracket', 'AMI'], var_name='NP', value_name='Income Threshold')
        df_income_brackets = df_income_brackets[df_income_brackets['Income Bracket'].isin(['Low Income', 'Moderate Income'])]
        df_income_brackets = df_income_brackets.pivot_table(index = ['County', 'NP'], columns='Income Bracket', values='Income Threshold').reset_index().rename(columns={'County':'County Name'})
        # df_income_brackets['NP'] = df_income_brackets['NP'].astype(str)
        df = df.merge(df_income_brackets, on=['County Name', 'NP'], how='left')
        df.loc[ df['HINCP'] <= df['Low Income']                                          , 'Income Bracket'] = 'Low Income'
        df.loc[(df['HINCP']  > df['Low Income']) & (df['HINCP'] <= df['Moderate Income']), 'Income Bracket'] = 'Moderate Income'
        df.loc[ df['HINCP']  > df['Moderate Income']                                     , 'Income Bracket'] = 'High Income'
        df.loc[ df['NP'] == 0                                                            , 'Income Bracket'] = 'No data available'
        df = df.drop(['HINCP', 'NP'], axis=1)
        groups = ['Income Bracket'] + groups[:-1]

    return df, groups


def pums_travel_time_brackets(df, params, groups):

    if params['indicator'] == 'Accessibility_4':
        df = df[df['JWTRNS'] != 'N/A, not a civillian in the labor force']
        df['JWMNP'] = df['JWMNP'].astype('float32')
        df.loc[(df['JWMNP'] ==  0)                      , 'Travel Time'] = 'No commute (worked from home)'
        df.loc[(df['JWMNP']  >  0) & (df['JWMNP'] <= 15), 'Travel Time'] = '0 to 15 minutes'
        df.loc[(df['JWMNP']  > 15) & (df['JWMNP'] <= 30), 'Travel Time'] = '15 to 30 minutes'
        df.loc[(df['JWMNP']  > 30)                      , 'Travel Time'] = 'More than 30 minutes'
        groups = groups[:-1] + ['Travel Time'] + ['RAC1P']
        df = df.drop('JWTRNS', axis=1)
        groups.remove('JWTRNS')

    return df, groups



def pums_calc_moe_ratio(params, df_puma, df_counties, df_msa, df_mpo):

    df_puma    ['MOE_ratio'] = df_puma    ['MOE']/df_puma    ['Total']
    df_counties['MOE_ratio'] = df_counties['MOE']/df_counties['Total']
    df_msa     ['MOE_ratio'] = df_msa     ['MOE']/df_msa     ['Total']
    df_mpo     ['MOE_ratio'] = df_mpo     ['MOE']/df_mpo     ['Total']
    
    conditions = [df_puma['MOE_ratio'] <= params['moe_thresh'], df_puma['MOE_ratio']  > params['moe_thresh']]
    choices = ['Yes', 'No']
    df_puma['Use for Reporting'] = np.select(conditions, choices, default='No')
    
    conditions = [df_counties['MOE_ratio'] <= params['moe_thresh'], df_counties['MOE_ratio']  > params['moe_thresh']]
    choices = ['Yes', 'No']
    df_counties['Use for Reporting'] = np.select(conditions, choices, default='No')
    
    conditions = [df_msa['MOE_ratio'] <= params['moe_thresh'], df_msa['MOE_ratio']  > params['moe_thresh']]
    choices = ['Yes', 'No']
    df_msa['Use for Reporting'] = np.select(conditions, choices, default='No')
    
    conditions = [df_mpo['MOE_ratio'] <= params['moe_thresh'], df_mpo['MOE_ratio']  > params['moe_thresh']]
    choices = ['Yes', 'No']
    df_mpo['Use for Reporting'] = np.select(conditions, choices, default='No')

    return df_puma, df_counties, df_msa, df_mpo



## TODO:
# Decompose PUMS_aggregate into smaller helper functions?
# Consolidate groupby roll ups together somehow?

def pums_aggregate(df_census, params, weight, groups):

    '''
    User defined function to process PUMS tables
    Rolls up population/household counts and standard errors and calculates percentages based on user defined geography/variable mappings
    '''

    print('Rolling up estimtaes to desired group variables and geographies, and calculating percentages...')

    group_puma, group_counties, group_msa, group_mpo = misc_groups()
    df_census.loc[df_census['MPO'].isna(), 'MPO'] = 'Unknown'
    df_puma     = df_census.drop([                            'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'SERIALNO'], axis=1).set_index(group_puma    ).reset_index()
    df_counties = df_census.drop([       'PUMA', 'PUMA NAME', 'MSA_ID', 'MSA',                               'SERIALNO'], axis=1).set_index(group_counties).reset_index()
    df_msa      = df_census.drop(['MPO', 'PUMA', 'PUMA NAME',                  'County FIPS', 'County Name', 'SERIALNO'], axis=1).set_index(group_msa     ).reset_index()
    df_mpo      = df_census.drop([       'PUMA', 'PUMA NAME', 'MSA_ID', 'MSA', 'County FIPS', 'County Name', 'SERIALNO'], axis=1).set_index(group_mpo     ).reset_index()

    if params['moe']:
        sqrtsumsq  = lambda x: np.sqrt(np.sum(x**2))
        df_puma    .loc[df_puma    ['MOE'] < 0, 'MOE'] = np.nan
        df_counties.loc[df_counties['MOE'] < 0, 'MOE'] = np.nan
        df_msa     .loc[df_msa     ['MOE'] < 0, 'MOE'] = np.nan
        df_mpo     .loc[df_mpo     ['MOE'] < 0, 'MOE'] = np.nan
        
        if params['indicator'] in ['Income_2', 'Accessibility_2', 'Accessibility_3', 'Accessibility_4']:
            if params['indicator'] == 'Accessibility_4':
                df_puma1     = df_puma    .groupby(group_puma     + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_counties1 = df_counties.groupby(group_counties + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_msa1      = df_msa     .groupby(group_msa      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo1      = df_mpo     .groupby(group_mpo      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_puma2     = df_puma    .groupby(group_puma     + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_counties2 = df_counties.groupby(group_counties + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_msa2      = df_msa     .groupby(group_msa      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo2      = df_mpo     .groupby(group_mpo      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_puma1    .loc[:, 'Income Bracket'] = 'All'
                df_counties1.loc[:, 'Income Bracket'] = 'All'
                df_msa1     .loc[:, 'Income Bracket'] = 'All'
                df_mpo1     .loc[:, 'Income Bracket'] = 'All'
                df_puma2    .loc[:, 'RAC1P'] = 'All'
                df_counties2.loc[:, 'RAC1P'] = 'All'
                df_msa2     .loc[:, 'RAC1P'] = 'All'
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_puma     = pd.concat([df_puma1    , df_puma2    ])
                df_counties = pd.concat([df_counties1, df_counties2])
                df_msa      = pd.concat([df_msa1     , df_msa2     ])
                df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])
            if params['indicator'] == 'Accessibility_3':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo1     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH', 'RAC1P'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo2     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_mpo      = pd.concat([df_mpo1, df_mpo2])           
            if params['indicator'] == 'Accessibility_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            if params['indicator'] == 'Income_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))

        elif params['indicator'] == 'Cost_6':

            groups2 = groups.copy()
            groups3 = groups.copy()
            groups2.remove('RAC1P')
            groups3.remove('housing_type')

            df_puma1 = df_puma.groupby(group_puma + ['Year'] + groups , as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_puma2 = df_puma.groupby(group_puma + ['Year'] + groups2, as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_puma2['RAC1P'] = 'All'
            df_puma2 = pd.concat([df_puma1, df_puma2])
            df_puma3 = df_puma2[df_puma2['housing_type'].isin(['Owner', 'Renter'])]
            df_puma3 = df_puma3.groupby(group_puma + ['Year'] + groups3, as_index=False).agg(Total=('Total', 'sum'), MOE=('MOE', sqrtsumsq))
            df_puma3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_puma = pd.concat([df_puma2, df_puma3])

            df_counties1 = df_counties.groupby(group_counties + ['Year'] + groups , as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_counties2 = df_counties.groupby(group_counties + ['Year'] + groups2, as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_counties2.loc[:, 'RAC1P'] = 'All'
            df_counties2 = pd.concat([df_counties1, df_counties2])
            df_counties3 = df_counties2[df_counties2['housing_type'].isin(['Owner', 'Renter'])]
            df_counties3 = df_counties3.groupby(group_counties + ['Year'] + groups3, as_index=False).agg(Total=('Total', 'sum'), MOE=('MOE', sqrtsumsq))
            df_counties3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_counties = pd.concat([df_counties2, df_counties3])
            
            df_msa1 = df_msa.groupby(group_msa + ['Year'] + groups , as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_msa2 = df_msa.groupby(group_msa + ['Year'] + groups2, as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_msa2.loc[:, 'RAC1P'] = 'All'
            df_msa2 = pd.concat([df_msa1, df_msa2])
            df_msa3 = df_msa2[df_msa2['housing_type'].isin(['Owner', 'Renter'])]
            df_msa3 = df_msa3.groupby(group_msa + ['Year'] + groups3, as_index=False).agg(Total=('Total', 'sum'), MOE=('MOE', sqrtsumsq))
            df_msa3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_msa = pd.concat([df_msa2, df_msa3])
            
            df_mpo1 = df_mpo.groupby(group_mpo + ['Year'] + groups , as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_mpo2 = df_mpo.groupby(group_mpo + ['Year'] + groups2, as_index=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_mpo2.loc[:, 'RAC1P'] = 'All'
            df_mpo2 = pd.concat([df_mpo1, df_mpo2])
            df_mpo3 = df_mpo2[df_mpo2['housing_type'].isin(['Owner', 'Renter'])]
            df_mpo3 = df_mpo3.groupby(group_mpo + ['Year'] + groups3, as_index=False).agg(Total=('Total', 'sum'), MOE=('MOE', sqrtsumsq))
            df_mpo3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_mpo = pd.concat([df_mpo2, df_mpo3])
        
        else:
            df_puma     = df_puma    .groupby(group_puma     + ['Year'] + groups , as_index=False, sort=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_counties = df_counties.groupby(group_counties + ['Year'] + groups , as_index=False, sort=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_msa      = df_msa     .groupby(group_msa      + ['Year'] + groups , as_index=False, sort=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
            df_mpo      = df_mpo     .groupby(group_mpo      + ['Year'] + groups , as_index=False, sort=False).agg(Total=(weight, 'sum'), MOE=('MOE', sqrtsumsq))
        
        df_puma, df_counties, df_msa, df_mpo = pums_calc_moe_ratio(params, df_puma, df_counties, df_msa, df_mpo)

    if not params['moe']:
        if params['indicator'] in ['Income_2', 'Accessibility_2', 'Accessibility_3', 'Accessibility_4']:
            if params['indicator'] == 'Accessibility_4':
                df_puma1     = df_puma    .groupby(group_puma     + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties1 = df_counties.groupby(group_counties + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa1      = df_msa     .groupby(group_msa      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo1      = df_mpo     .groupby(group_mpo      + ['Year', 'RAC1P'                  , 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_puma2     = df_puma    .groupby(group_puma     + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties2 = df_counties.groupby(group_counties + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa2      = df_msa     .groupby(group_msa      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo2      = df_mpo     .groupby(group_mpo      + ['Year',          'Income Bracket', 'Travel Time'], as_index=False).agg(Total=(weight, 'sum'))
                df_puma1    .loc[:, 'Income Bracket'] = 'All'
                df_counties1.loc[:, 'Income Bracket'] = 'All'
                df_msa1     .loc[:, 'Income Bracket'] = 'All'
                df_mpo1     .loc[:, 'Income Bracket'] = 'All'
                df_puma2    .loc[:, 'RAC1P'] = 'All'
                df_counties2.loc[:, 'RAC1P'] = 'All'
                df_msa2     .loc[:, 'RAC1P'] = 'All'
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_puma     = pd.concat([df_puma1    , df_puma2    ])
                df_counties = pd.concat([df_counties1, df_counties2])
                df_msa      = pd.concat([df_msa1     , df_msa2     ])
                df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])
            if params['indicator'] == 'Accessibility_3':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo1     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH', 'RAC1P'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo2     = df_mpo     .groupby(group_mpo      + ['Year', 'VEH'         ], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo2     .loc[:, 'RAC1P'] = 'All'
                df_mpo      = pd.concat([df_mpo1, df_mpo2])
            if params['indicator'] == 'Accessibility_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket', 'JWTRNS'], as_index=False).agg(Total=(weight, 'sum'))
            if params['indicator'] == 'Income_2':
                df_puma     = df_puma    .groupby(group_puma     + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                df_counties = df_counties.groupby(group_counties + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                df_msa      = df_msa     .groupby(group_msa      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                df_mpo      = df_mpo     .groupby(group_mpo      + ['Year', 'Income Bracket'], as_index=False).agg(Total=(weight, 'sum'))
                
        elif params['indicator'] == 'Cost_6':
            df_puma1 = df_puma.groupby(list(df_puma.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_puma2 = df_puma.groupby(list(df_puma.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_puma2.loc[:, 'RAC1P'] = 'All'
            df_puma2 = pd.concat([df_puma1, df_puma2])
            df_puma3 = df_puma2[df_puma2['housing_type'].isin(['Owner', 'Renter'])]
            df_puma3 = df_puma3.groupby(list(df_puma3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=('Total', 'sum'))
            df_puma3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_puma3['Percent'] = df_puma3['Total']/df_puma3.groupby(list(df_puma3.drop(['housing_burden', 'Total'], axis=1).columns))['Total'].transform('sum')
            df_puma = pd.concat([df_puma2, df_puma3])

            df_counties1 = df_counties.groupby(list(df_counties.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_counties2 = df_counties.groupby(list(df_counties.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_counties2.loc[:, 'RAC1P'] = 'All'
            df_counties2 = pd.concat([df_counties1, df_counties2])
            df_counties3 = df_counties2[df_counties2['housing_type'].isin(['Owner', 'Renter'])]
            df_counties3 = df_counties3.groupby(list(df_counties3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_counties3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_counties = pd.concat([df_counties2, df_counties3])

            df_msa1 = df_msa.groupby(list(df_msa.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_msa2 = df_msa.groupby(list(df_msa.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_msa2.loc[:, 'RAC1P'] = 'All'
            df_msa2 = pd.concat([df_msa1, df_msa2])
            df_msa3 = df_msa2[df_msa2['housing_type'].isin(['Owner', 'Renter'])]
            df_msa3 = df_msa3.groupby(list(df_msa3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_msa3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_msa = pd.concat([df_msa2, df_msa3])
            
            df_mpo1 = df_mpo.groupby(list(df_mpo.drop([weight         ], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_mpo2 = df_mpo.groupby(list(df_mpo.drop([weight, 'RAC1P'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_mpo2.loc[:, 'RAC1P'] = 'All'
            df_mpo2 = pd.concat([df_mpo1, df_mpo2])
            df_mpo3 = df_mpo2[df_mpo2['housing_type'].isin(['Owner', 'Renter'])]
            df_mpo3 = df_mpo3.groupby(list(df_mpo3.drop(['Total'], axis=1).columns), as_index=False).agg(Total=(weight, 'sum'))
            df_mpo3.loc[:, 'housing_type'] = 'Owners and Renters'
            df_mpo = pd.concat([df_mpo2, df_mpo3])

        else:
            df_puma     = df_puma    .groupby(list(df_puma    .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
            df_counties = df_counties.groupby(list(df_counties.drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
            df_msa      = df_msa     .groupby(list(df_msa     .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
            df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
    
    if 'RAC1P' in groups:# and indicator not in ['Cost_6', 'Accessibility_1']:
        groups.remove('RAC1P')
        groups = ['RAC1P'] + groups

    if params['pct']:
        if params['moe']:
            if len(groups) > 1:
                df_puma    ['Percent'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop([groups[-1]] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percent'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop([groups[-1]] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percent'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop([groups[-1]] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_mpo     ['Percent'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop([groups[-1]] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
            if len(groups) == 1:
                df_puma    ['Percent'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percent'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percent'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_mpo     ['Percent'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
        if not params['moe']:
            if len(groups) > 1:
                df_puma    ['Percent'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percent'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percent'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_mpo     ['Percent'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop([groups[-1]] + ['Total'], axis=1).columns))['Total'].transform('sum')
            if len(groups) == 1:
                df_puma    ['Percent'] = df_puma    ['Total'] / df_puma    .groupby(list(df_puma    .drop(groups + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_counties['Percent'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups + ['Total'], axis=1).columns))['Total'].transform('sum')
                df_msa     ['Percent'] = df_msa     ['Total'] / df_msa     .groupby(list(df_msa     .drop(groups + ['Total'], axis=1).columns))['Total'].transform('sum')           
                df_mpo     ['Percent'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups + ['Total'], axis=1).columns))['Total'].transform('sum')

    df_puma    .reset_index(drop=True, inplace=True)
    df_counties.reset_index(drop=True, inplace=True)
    df_msa     .reset_index(drop=True, inplace=True)
    df_mpo     .reset_index(drop=True, inplace=True)

    if params['indicator'] == 'Accessibility_4':
        if params['pct']:
            df_puma2     = df_puma    [df_puma    ['RAC1P'] != 'All']
            df_counties2 = df_counties[df_counties['RAC1P'] != 'All']
            df_msa2      = df_msa     [df_msa     ['RAC1P'] != 'All']
            df_mpo2      = df_mpo     [df_mpo     ['RAC1P'] != 'All']
            df_puma1     = df_puma    [df_puma    ['RAC1P'] == 'All']
            df_counties1 = df_counties[df_counties['RAC1P'] == 'All']
            df_msa1      = df_msa     [df_msa     ['RAC1P'] == 'All']
            df_mpo1      = df_mpo     [df_mpo     ['RAC1P'] == 'All']
            groups.remove('Income Bracket')
            groups = groups + ['Income Bracket']
            if params['moe']:
                df_puma1     = df_puma1    .drop('Percent', axis=1)
                df_counties1 = df_counties1.drop('Percent', axis=1)
                df_msa1      = df_msa1     .drop('Percent', axis=1)
                df_mpo1      = df_mpo1     .drop('Percent', axis=1)
                df_puma1    ['Percent'] = df_puma1    ['Total'] / df_puma1    .groupby(list(df_puma1    .drop(groups[:-1] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_counties1['Percent'] = df_counties1['Total'] / df_counties1.groupby(list(df_counties1.drop(groups[:-1] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_msa1     ['Percent'] = df_msa1     ['Total'] / df_msa1     .groupby(list(df_msa1     .drop(groups[:-1] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
                df_mpo1     ['Percent'] = df_mpo1     ['Total'] / df_mpo1     .groupby(list(df_mpo1     .drop(groups[:-1] + ['Total', 'MOE', 'MOE_ratio', 'Use for Reporting'], axis=1).columns))['Total'].transform('sum')
            df_puma     = pd.concat([df_puma1    , df_puma2    ])
            df_counties = pd.concat([df_counties1, df_counties2])
            df_msa      = pd.concat([df_msa1     , df_msa2     ])
            df_mpo      = pd.concat([df_mpo1     , df_mpo2     ])

    return df_puma, df_counties, df_msa, df_mpo, groups




def pums_rename(params, groups, df_puma, df_counties, df_msa, df_mpo):

    '''
    User defined function to finalize cleaning/renaming of PUMS fields
    '''

    if params['sample'] == 'PUMS':
        group_puma, group_counties, group_msa, group_mpo = misc_groups()
        if params['indicator'] not in ['Accessibility_2']:
            groups.reverse()
        if params['indicator'] == 'Cost_6':
            groups = ['RAC1P', 'housing_type', 'housing_burden']
        if params['indicator'] == 'Accessibility_4':
            groups = ['RAC1P', 'Income Bracket', 'Travel Time']
        if params['indicator'] == 'Accessibility_3':
            groups = ['VEH']
            groups_mpo = ['RAC1P', 'VEH']
        
        if params['moe']:
            df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total', 'Percent', 'MOE', 'MOE_ratio', 'Use for Reporting']]
            df_counties = df_counties[group_counties + ['Year'] + groups + ['Total', 'Percent', 'MOE', 'MOE_ratio', 'Use for Reporting']]
            df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total', 'Percent', 'MOE', 'MOE_ratio', 'Use for Reporting']]
            if params['indicator'] == 'Accessibility_3':
                df_mpo = df_mpo[group_mpo + ['Year'] + groups_mpo + ['Total', 'Percent', 'MOE', 'MOE_ratio', 'Use for Reporting']]
            else:
                df_mpo = df_mpo[group_mpo + ['Year'] + groups + ['Total', 'Percent', 'MOE', 'MOE_ratio', 'Use for Reporting']]
        df_puma     = df_puma    .rename(columns={'MOE':'Margin of Error', 'MOE_ratio':'Margin of Error Ratio'})
        df_counties = df_counties.rename(columns={'MOE':'Margin of Error', 'MOE_ratio':'Margin of Error Ratio'})
        df_msa      = df_msa     .rename(columns={'MOE':'Margin of Error', 'MOE_ratio':'Margin of Error Ratio'})
        df_mpo      = df_mpo     .rename(columns={'MOE':'Margin of Error', 'MOE_ratio':'Margin of Error Ratio'})

    if not params['moe']:
        if params['sample'] == 'PUMS':
            groups.reverse()
            if params['pct']:
                df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total', 'Percent']]
                df_counties = df_counties[group_counties + ['Year'] + groups + ['Total', 'Percent']]
                df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total', 'Percent']]
                df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups + ['Total', 'Percent']]
            else:
                df_puma     = df_puma    [group_puma     + ['Year'] + groups + ['Total']]
                df_counties = df_counties[group_counties + ['Year'] + groups + ['Total']]
                df_msa      = df_msa     [group_msa      + ['Year'] + groups + ['Total']]
                df_mpo      = df_mpo     [group_mpo      + ['Year'] + groups + ['Total']]
        if params['sample'] == 'FOODSEC':
            df_counties = df_counties[group_counties + groups + ['Total', 'Percent']]
            df_mpo      = df_mpo     [group_mpo      + groups + ['Total', 'Percent']]

    if params['geo'] == 'PUMA':
        df_puma     = df_puma    .sort_values(group_puma     + ['Year'] + groups, ascending=[True, True, True, True, False] + [item in groups for item in groups])
        df_counties = df_counties.sort_values(group_counties + ['Year'] + groups, ascending=[True, True, True, True, False] + [item in groups for item in groups])
        df_msa      = df_msa     .sort_values(group_msa      + ['Year'] + groups, ascending=[True, True,             False] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + ['Year'] + groups, ascending=[True,                   False] + [item in groups for item in groups])
    if params['sample'] == 'FOODSEC':
        df_counties = df_counties.sort_values(group_counties + groups, ascending=[True, True, True, True] + [item in groups for item in groups])
        df_mpo      = df_mpo     .sort_values(group_mpo      + groups, ascending=[True,                 ] + [item in groups for item in groups])
    if 'PTDTRACE' in groups:
        df_counties = df_counties.set_index(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'PTDTRACE']).reset_index()
        df_mpo      = df_mpo     .set_index(['State FIPS', 'MPO',                               'PTDTRACE']).reset_index()

    if params['indicator'] == 'Accessibility_1':
        factor_commutes = ['Car, truck, or van', 'Public transportation (bus, subway, or rail)', 'Bicycle', 'Walked', 'Other method', 'Worked from home']
        df_puma    ['JWTRNS_sort'] = pd.Categorical(df_puma    ['JWTRNS'], factor_commutes)
        df_counties['JWTRNS_sort'] = pd.Categorical(df_counties['JWTRNS'], factor_commutes)
        df_msa     ['JWTRNS_sort'] = pd.Categorical(df_msa     ['JWTRNS'], factor_commutes)
        df_mpo     ['JWTRNS_sort'] = pd.Categorical(df_mpo     ['JWTRNS'], factor_commutes)

        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True,  True,  True, False, True, True]).drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True,  True,  True, False, True, True]).drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True, True,               False, True, True]).drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'RAC1P_sort', 'JWTRNS_sort'], ascending=[True,                     False, True, True]).drop(['RAC1P_sort', 'JWTRNS_sort'], axis=1)

    if params['indicator'] == 'Accessibility_2':
        factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)

        factor_commutes = ['Car, truck, or van', 'Public transportation (bus, subway, or rail)', 'Bicycle', 'Walked', 'Worked from home', 'Other method']
        df_puma    ['JWTRNS_sort'] = pd.Categorical(df_puma    ['JWTRNS'], factor_commutes)
        df_counties['JWTRNS_sort'] = pd.Categorical(df_counties['JWTRNS'], factor_commutes)
        df_msa     ['JWTRNS_sort'] = pd.Categorical(df_msa     ['JWTRNS'], factor_commutes)
        df_mpo     ['JWTRNS_sort'] = pd.Categorical(df_mpo     ['JWTRNS'], factor_commutes)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True, True, True, False, True, True]).drop(['Income_sort', 'JWTRNS_sort'], axis=1)
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True, True, True, False, True, True]).drop(['Income_sort', 'JWTRNS_sort'], axis=1)
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True, True,             False, True, True]).drop(['Income_sort', 'JWTRNS_sort'], axis=1)
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'Income_sort', 'JWTRNS_sort'], ascending=[True,                   False, True, True]).drop(['Income_sort', 'JWTRNS_sort'], axis=1)

    if params['indicator'] == 'Accessibility_4':
        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)
        
        factor_incomes = ['All', 'No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)

        factor_times = ['No commute (worked from home)', '0 to 15 minutes', '15 to 30 minutes', 'More than 30 minutes']
        df_puma    ['Travel_sort'] = pd.Categorical(df_puma    ['Travel Time'], factor_times)
        df_counties['Travel_sort'] = pd.Categorical(df_counties['Travel Time'], factor_times)
        df_msa     ['Travel_sort'] = pd.Categorical(df_msa     ['Travel Time'], factor_times)
        df_mpo     ['Travel_sort'] = pd.Categorical(df_mpo     ['Travel Time'], factor_times)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True, True, True, False, True, True, True]).drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True, True, True, False, True, True, True]).drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True, True,             False, True, True, True]).drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'RAC1P_sort', 'Income_sort', 'Travel_sort'], ascending=[True,                   False, True, True, True]).drop(['RAC1P_sort', 'Income_sort', 'Travel_sort'], axis=1)

    if params['indicator'] == 'Accessibility_3':
        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_mpo['RAC1P_sort'] = pd.Categorical(df_mpo['RAC1P'], factor_race)
        df_mpo = df_mpo.sort_values(by= group_mpo + ['Year', 'RAC1P_sort', 'VEH'], ascending=[True, False, True, True]).drop(['RAC1P_sort'], axis=1)
        
    if params['indicator'] == 'Income_2':
        factor_incomes = ['No data available', 'Low Income', 'Moderate Income', 'High Income']
        df_puma    ['Income_sort'] = pd.Categorical(df_puma    ['Income Bracket'], factor_incomes)
        df_counties['Income_sort'] = pd.Categorical(df_counties['Income Bracket'], factor_incomes)
        df_msa     ['Income_sort'] = pd.Categorical(df_msa     ['Income Bracket'], factor_incomes)
        df_mpo     ['Income_sort'] = pd.Categorical(df_mpo     ['Income Bracket'], factor_incomes)
        
        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'Income_sort'], ascending=[True, True, True, True, False, True]).drop(['Income_sort'], axis=1)
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'Income_sort'], ascending=[True, True, True, True, False, True]).drop(['Income_sort'], axis=1)
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'Income_sort'], ascending=[True, True,             False, True]).drop(['Income_sort'], axis=1)
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'Income_sort'], ascending=[True,                   False, True]).drop(['Income_sort'], axis=1)

    if params['indicator'] == 'Cost_6':
        factor_burden = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Cost burden <=30%', 'Cost burden >30% to <=50%', 'Cost burden >50%']
        df_puma    ['housing_burden_sort'] = pd.Categorical(df_puma    ['housing_burden'], factor_burden)
        df_counties['housing_burden_sort'] = pd.Categorical(df_counties['housing_burden'], factor_burden)
        df_msa     ['housing_burden_sort'] = pd.Categorical(df_msa     ['housing_burden'], factor_burden)
        df_mpo     ['housing_burden_sort'] = pd.Categorical(df_mpo     ['housing_burden'], factor_burden)

        factor_types = ['Housing data not available', 'N/A (GQ/vacant/not owned or being bought/occupied without rent payment/no household income)', 'Owner', 'Renter', 'Owners and Renters']
        df_puma    ['housing_type_sort'] = pd.Categorical(df_puma    ['housing_type'], factor_types)
        df_counties['housing_type_sort'] = pd.Categorical(df_counties['housing_type'], factor_types)
        df_msa     ['housing_type_sort'] = pd.Categorical(df_msa     ['housing_type'], factor_types)
        df_mpo     ['housing_type_sort'] = pd.Categorical(df_mpo     ['housing_type'], factor_types)

        factor_race = ['All', 'American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'Hispanic or Latino', 'Native Hawaiian or other Pacific Islander (NH)', 'White (NH)', 'Some other race (NH)', 'Two or more races (NH)']
        df_puma    ['RAC1P_sort'] = pd.Categorical(df_puma    ['RAC1P'], factor_race)
        df_counties['RAC1P_sort'] = pd.Categorical(df_counties['RAC1P'], factor_race)
        df_msa     ['RAC1P_sort'] = pd.Categorical(df_msa     ['RAC1P'], factor_race)
        df_mpo     ['RAC1P_sort'] = pd.Categorical(df_mpo     ['RAC1P'], factor_race)

        df_puma     = df_puma    .sort_values(by= group_puma     + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True,  True,  True, False, True, True, True]).drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1).rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})
        df_counties = df_counties.sort_values(by= group_counties + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True,  True,  True, False, True, True, True]).drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1).rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})
        df_msa      = df_msa     .sort_values(by= group_msa      + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True, True,               False, True, True, True]).drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1).rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})
        df_mpo      = df_mpo     .sort_values(by= group_mpo      + ['Year', 'RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], ascending=[True,                     False, True, True, True]).drop(['RAC1P_sort', 'housing_type_sort', 'housing_burden_sort'], axis=1).rename(columns={'housing_type':'Housing Type', 'housing_burden':'Housing Burden'})

    df_puma     = df_puma    .rename(columns={'Total': params['metric']})
    df_counties = df_counties.rename(columns={'Total': params['metric']})
    df_msa      = df_msa     .rename(columns={'Total': params['metric']})
    df_mpo      = df_mpo     .rename(columns={'Total': params['metric']})


    return df_puma, df_counties, df_msa, df_mpo




def pums_main(df, params, weight, df_vars):
    
    df, groups = pums_clean_data(df, params, weight, df_vars)
    df = pums_cw_to_geos(df, params, groups)
    df, groups = pums_clean_eth_groups(df, params, groups)

    df, groups = pums_assign_own_vs_rent(df, params, groups)
    df, groups = pums_travel_time_brackets(df, params, groups)
    df = pums_cpi_adjust(df, params)
    df, groups = pums_income_brackets(df, params, groups)

    df_puma, df_counties, df_msa, df_mpo, groups = pums_aggregate(df, params, weight, groups)
    df_puma, df_counties, df_msa, df_mpo = pums_rename(params, groups, df_puma, df_counties, df_msa, df_mpo)

    help.print2()
    time.sleep(5)
    print('Final tables:'); print()
    print('PUMA')
    display(df_puma); print()
    print('Counties')
    display(df_counties); print()
    print('MSA')
    display(df_msa); print()
    print('MPO')
    display(df_mpo); print()
    help.print2()
    time.sleep(5)


    return df_puma, df_counties, df_msa, df_mpo





def pums_export(df_puma, df_counties, df_msa, df_mpo, params):

    help.print2()
    workbooks = set_workbook_name(params)

    path_out_sp = Path(params['export_loc']) / f"{params['indicator']} {params['folder']}"
    if params['project'] != 'Monitoring and Reporting':
        path_out_sp = Path(params['export_loc'])
    if params['project'] == 'Monitoring and Reporting' and params['server']: paths = [PATH_SERVER, path_out_sp]
    else: paths = [path_out_sp]

    for path_ in paths:            

        params['path_wb'] = path_ / workbooks[0]
        export_indicator(df_puma, params)

        params['path_wb'] = path_ / workbooks[1]
        if params['about']:
            params['df_about'].loc[params['df_about']['Indicator'] == 'Geography', params['indicator']] = 'Counties'
        export_indicator(df_counties, params)

        params['path_wb'] = path_ / workbooks[2]
        if params['about']:
            params['df_about'].loc[params['df_about']['Indicator'] == 'Geography', params['indicator']] = 'MSA'
        export_indicator(df_msa, params)

        params['path_wb'] = path_ / workbooks[3]
        if params['about']:
            params['df_about'].loc[params['df_about']['Indicator'] == 'Geography', params['indicator']] = 'MPO'
        export_indicator(df_mpo, params)





## ---


## CPS processing steps ---

## FOODSEC processing step (4) (use 1-3 from PUMS process steps)

def foodsec_processing(df_census, params, weight, groups):

    print()
    print('Processing 4:')
    print('Rolling up estimtaes to desired group variables and geographies, and calculating perecntages...')
    print()

    if 'PTDTRACE' in groups:
        groups.remove('PTDTRACE')
        groups_to_drop=groups.copy()
        groups = ['PTDTRACE'] + groups

    df_counties = df_census.drop([                              'Household_ID', 'Householder', 'PERRP'], axis=1)
    df_mpo      = df_census.drop(['County FIPS', 'County Name', 'Household_ID', 'Householder', 'PERRP'], axis=1)

    group_counties = ['State FIPS', 'MPO', 'County FIPS', 'County Name']
    group_mpo      = ['State FIPS', 'MPO'                              ]

    df_counties = df_counties.set_index(group_counties).reset_index()
    df_mpo      = df_mpo     .set_index(group_mpo     ).reset_index()

    df_counties = df_counties.drop('Year', axis=1)
    df_mpo      = df_mpo     .drop('Year', axis=1)

    df_counties[weight] = 1
    df_mpo     [weight] = 1

    df_counties = df_counties.groupby(list(df_counties.drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))
    df_mpo      = df_mpo     .groupby(list(df_mpo     .drop([weight], axis=1).columns), as_index=False, sort=False).agg(Total=(weight, 'sum'))

    if params['pct']:
        df_counties['Percent'] = df_counties['Total'] / df_counties.groupby(list(df_counties.drop(groups_to_drop + ['Total'], axis=1).columns))['Total'].transform('sum')
        df_mpo     ['Percent'] = df_mpo     ['Total'] / df_mpo     .groupby(list(df_mpo     .drop(groups_to_drop + ['Total'], axis=1).columns))['Total'].transform('sum')

    df_counties['Total'] = round(df_counties['Total'])
    df_mpo     ['Total'] = round(df_mpo     ['Total'])

    df_counties['Total'] = df_counties['Total'].astype(int)
    df_mpo     ['Total'] = df_mpo     ['Total'].astype(int)

    return df_counties, df_mpo, groups




## ---


## LEHD processing steps ---

def lehd_processing(df_census, params, df_fips=None):
    if params['indicator'] == 'Jobs_4':
        df_census = df_census[df_census['Emp'] != 'null']
        df_census = df_census[~df_census['Emp'].isna()]
        df_census['Emp'    ] = df_census['Emp'    ].astype('int')
        df_census['firmage'] = df_census['firmage'].astype('int')
        df_census = df_census[df_census['firmage'] != 0]
        df_census.loc[ df_census['firmage'].isin([1, 2, 3]), 'Firm Age'] = 'Less than or equal to 5 years old'
        df_census.loc[~df_census['firmage'].isin([1, 2, 3]), 'Firm Age'] = 'Greater than 5 years old'
        df_census = df_census.drop(['Year', 'ownercode', 'firmage'], axis=1)

        df_census = df_census.rename(columns={'time':'Quarter'})
        # df_census = df_census[df_census['Quarter'].str.contains('Q3')] # remove this if you want to show all quarters

        if params['geo'] == 'Counties':

            df_mpo = df_fips[['County Name', 'MPO']]
            df_census = df_census.merge(df_mpo, on=['County Name'], how='left')
            
            df_census = df_census[['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Quarter', 'Firm Age', 'Emp']]
            df_census['Emp'] = df_census['Emp'].astype('int')

            df_census['State FIPS' ] = df_census['State FIPS' ].astype(str).apply('{:0>2}'.format)
            df_census['County FIPS'] = df_census['County FIPS'].astype(str).apply('{:0>3}'.format)

            df_counties = df_census.groupby(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Quarter', 'Firm Age'], as_index=False).agg(Total=('Emp', 'sum'))
            df_mpo      = df_census.groupby(['State FIPS', 'MPO',                               'Quarter', 'Firm Age'], as_index=False).agg(Total=('Emp', 'sum'))
            
            df_counties = df_counties.sort_values(['State FIPS', 'MPO', 'County FIPS', 'County Name', 'Quarter', 'Firm Age'], ascending=[True, True, True, True, False, False]).reset_index(drop=True)
            df_mpo      = df_mpo     .sort_values(['State FIPS', 'MPO',                               'Quarter', 'Firm Age'], ascending=[True, True,             False, False]).reset_index(drop=True)

            if params['pct']:
                df_counties['Percent'] = df_counties['Total'] / df_counties.groupby(['State FIPS',        'County FIPS', 'Quarter'])['Total'].transform('sum')
                df_mpo     ['Percent'] = df_mpo     ['Total'] / df_mpo     .groupby(['State FIPS', 'MPO',                'Quarter'])['Total'].transform('sum')

        if params['geo'] == 'MSA':
            
            df_census = df_census[['MSA_ID', 'MSA', 'Quarter', 'Firm Age', 'Emp']]
            df_msa = df_census.groupby(['MSA_ID', 'MSA', 'Quarter', 'Firm Age'], as_index=False).agg(Total=('Emp', 'sum'))
            df_msa = df_msa.sort_values(['MSA', 'Quarter', 'Firm Age'], ascending=[True, False, False])
            df_msa = df_msa.reset_index(drop=True)

            if params['pct']:
                df_msa['Percent'] = df_msa['Total'] / df_msa.groupby(['MSA', 'Quarter'])['Total'].transform('sum')

    if params['geo'] == 'Counties':
        return df_counties, df_mpo
    if params['geo'] == 'MSA':
        return df_msa
    



## ---





## Exporting ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



def set_workbook_name(params):

    workbooks = []

    if params['sample'] == 'SUBJECT': params['estimate'] = re.sub('ACS', 'SUBJECT', params['estimate'])
    if params['sample'] == 'DP': params['estimate'] = re.sub('ACS', 'DP', params['estimate'])

    if params['geo'] == 'PUMA':
        params['estimate'] = re.sub('ACS', 'PUMS', params['estimate'])
        workbooks.append(f"{params['indicator']} PUMA {params['estimate']}.xlsx")
        workbooks.append(f"{params['indicator']} Counties {params['estimate']}.xlsx")
        workbooks.append(f"{params['indicator']} MSA {params['estimate']}.xlsx")
        workbooks.append(f"{params['indicator']} MPO {params['estimate']}.xlsx")
                
    if params['geo'] == 'Counties': workbooks.append(f"{params['indicator']} {params['geo']} {params['estimate']}.xlsx")
    if params['mpo']: workbooks.append(f"{params['indicator']} MPO {params['estimate']}.xlsx")
    else:
        if params['sample'] == 'LEHD': workbooks.append(f"{params['indicator']} {params['geo']} {params['sample']}.xlsx")
        else: workbooks.append(f"{params['indicator']} {params['geo']} {params['estimate']}.xlsx")

    print()

    return workbooks


def write_about_master(df_census, params):

    params['start_year'] = df_census.Year.min()
    params['end_year']   = df_census.Year.max()
    params['estimate'] = re.sub('PUMS', 'ACS', params['estimate'])

    df_about = func.write_about(params)
    params['df_about'] = df_about


    if params['update']:
        file_about = PATH_ABOUT / 'About Indicators.xlsx'
        with pd.ExcelWriter(file_about, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df_about.to_excel(writer, index=False, sheet_name=params['indicator'], header=False)

    if params['estimate'] not in ['LEHD', 'CPS']:
        if params['geo'] == 'Counties':
            if params['mpo']:
                params['geo'] = 'MPO'
                df_about_mpo = func.write_about(params)
                params['df_about_mpo'] = df_about_mpo
                params['geo'] = 'Counties'
            
    return params



def export_indicator(df, params):

    print('Excel files exported here: ' + str(params['path_wb']))

    writer = pd.ExcelWriter(params['path_wb'], engine='xlsxwriter')
    
    if params['geo'] == 'Congressional Districts': sheet_geo = 'CD'
    elif params['geo'] == 'State Legislative Lower Districts': sheet_geo = 'SLDL'
    elif params['geo'] == 'State Legislative Upper Districts': sheet_geo = 'SLDU'
    elif 'MPO' in str(params['path_wb']): sheet_geo = 'MPO'
    else: sheet_geo = params['geo']

    if params['about']:
        if params['geo']=='Counties' and params['mpo']:
            params['df_about_mpo'].to_excel(writer, sheet_name='About', index=False, header=False)
        else:
            params['df_about'].to_excel(writer, sheet_name='About', index=False, header=False)


    df.to_excel(writer, sheet_name=sheet_geo, index=False, header=True)
    workbook = writer.book
    
    format_numbers = workbook.add_format({'num_format': '#,##0' })
    formet_percent = workbook.add_format({'num_format': '0.0%'  })
    formet_dollars = workbook.add_format({'num_format': '$#,##0'})

    worksheet = writer.sheets[sheet_geo]
    
    try:
        idx_col = df.columns.get_loc('Population')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df.columns.get_loc('Households')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df.columns.get_loc('Housing Units')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df.columns.get_loc('Margin of Error')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df.columns.get_loc('Percent')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df.columns.get_loc('Margin of Error Ratio')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df.columns.get_loc('Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
        idx_col = df.columns.get_loc('Margin of Error')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
    except: pass
    try:
        idx_col = df.columns.get_loc('Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
        idx_col = df.columns.get_loc('Regional Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_dollars)
        idx_col = df.columns.get_loc('Percent of Regional Median Household Income')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df.columns.get_loc('Total Population')
        worksheet.set_column(idx_col, idx_col, 10, format_numbers)
    except: pass
    try:
        idx_col = df.columns.get_loc('Birth Rate Per 1,000 People')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass
    try:
        idx_col = df.columns.get_loc('Marriage Rate Per 1,000 People')
        worksheet.set_column(idx_col, idx_col, 10, formet_percent)
    except: pass


    worksheet.autofit()
    
    writer.close()

    print("Successfully exported!")
    print()

