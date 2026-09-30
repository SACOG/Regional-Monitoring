


'''
Life Expectancy data is collected from the California Health Rankings & Roadmaps survey (a program of the University of Wisconsin Population Health Institute)
https://www.countyhealthrankings.org/health-data/california/data-and-resources

Each year, download the "California Data" excel workbook, then copy/paste to I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\CHRR

Make sure to check workbook for changes in column name, table structure, etc... they have not been consistent year over year, so possibly need to update code below
'''


## Also, it looks like they are sourcing their data from https://www.cdc.gov/nchs/nvss/usaleep/usaleep.html#life-expectancy, but I do not see how
## CDC definitely has some info on life expectancy, but nothing at the county level by year
## Otherwise, maybe it makes sense for us to collect data directly from CDC?
## Not sure


# Setup ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'config'))
import functions as func


def calc_moe(df):
    if 'Margin of Error' not in df.columns:
        df['Margin of Error'] = (df['High'] - df['Low'])/2
        df = df.drop(['Low', 'High'], axis=1)
    df['Margin of Error Ratio'] = df['Margin of Error'] / df['Life Expectancy (Years)']
    df['Use for Reporting'] = 'Yes'
    df.loc[df['Margin of Error Ratio'] > 0.05, 'Use for Reporting'] = 'No'
    return df


def proc_wkbook(wkbook):

    df = pd.read_excel(PATH_DATA/wkbook, sheet_name='Additional Measure Data', skiprows=1)
    df = df[df['County'].isin(counties)]

    cols_to_keep = ['FIPS', 'County', '95% CI - Low', '95% CI - High'] + [col for col in df.columns if 'Life Expectancy' in col]
    df = df[cols_to_keep]

    df = df.melt(id_vars=['FIPS', 'County'], var_name='Race/Ethnicity', value_name='Life Expectancy (Years)')
    
    df.loc[df['Race/Ethnicity']=='Life Expectancy', 'Race/Ethnicity']='All'
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace('Life Expectancy ', '')

    df['Estimate'] = 'Life Expectancy (Years)'
    df.loc[df['Race/Ethnicity'].str.contains('High'), 'Estimate'] = 'High'
    df.loc[df['Race/Ethnicity'].str.contains('Low'), 'Estimate'] = 'Low'

    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace('95% CI - High', '')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace('95% CI - Low', '')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace('(', '')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace(')', '')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace('Non-Hispanic ', '')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace('white', 'White')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.replace(' all races', '')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].str.strip()
    df.loc[df['Race/Ethnicity'] == '', 'Race/Ethnicity'] = 'All'

    df = df.pivot_table(index=['FIPS', 'County', 'Race/Ethnicity'], columns='Estimate', values='Life Expectancy (Years)').reset_index()

    df = calc_moe(df)

    df.loc[df['Race/Ethnicity']=='AIAN', 'Race/Ethnicity'] = 'American Indian/Alaskan Native'
    df['Year'] = year

    df = df.set_index(['County', 'Year']).reset_index().drop('FIPS', axis=1)

    return df


def proc_weights():

    pop_eth_labels  = {
    'All': 'All'
        , 'American Indian or Alaska Native (NH)': 'American Indian/Alaskan Native'
        , 'Asian (NH)': 'Asian'
        , 'Black or African American (NH)': 'Black'
        , 'Hispanic or Latino': 'Hispanic'
        , 'Native Hawaiian or other Pacific Islander (NH)': 'Native Hawaiian and Other Pacific Islander'
        , 'Some other race (NH)': 'Some other race'
        , 'Two or more races (NH)': 'Two or more races'
        , 'White (NH)': 'White'
    }

    df = pd.read_excel(PATH_WEIGHTS/'Total_Population Counties ACS5.xlsx', sheet_name='Counties')
    df['Race/Ethnicity'] = df['Race/Ethnicity'].map(pop_eth_labels)
    df = df.rename(columns={'County Name':'County'})
    df = df[['County', 'Year', 'Race/Ethnicity', 'Population']]
    df_2025 = df[df['Year']==2024]
    df_2025['Year']=2025
    df = pd.concat([df_2025, df]).reset_index(drop=True)

    return df


def regional_rollup(df):

    df_weights = proc_weights()
    df = df.merge(df_weights, on=['County', 'Year', 'Race/Ethnicity'], how='left')

    def sumsqrt(x):
        return np.sqrt(np.sum((df.loc[x.index, "Population"]**2) * (x**2))) / np.sum(df.loc[x.index, "Population"])
    def wm(x):
        return np.average(x, weights=df.loc[x.index, "Population"])

    df = df.groupby(['Year', 'Race/Ethnicity'], as_index=False, sort=False).agg(LE=('Life Expectancy (Years)', wm), MOE=('Margin of Error', sumsqrt))
    df = df.rename(columns={'LE':'Life Expectancy (Years)', 'MOE':'Margin of Error'})
    df = calc_moe(df)
    df['Geography'] = 'SACOG Six-County Region'
    df = df.set_index('Geography').reset_index()

    return df



# Main ---------------------------------------------------------------------------------------------------------------------------------------------------------



EXPORT=True


PATH_DATA = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\CHRR')
PATH_WEIGHTS = Path(r'I:\Projects\Josh\Regional Monitoring\weights')
PATH_SP = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\People and Community\Healthy Places\Health_4 Life Expectancy')
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")

YEAR_REF = {
    2022: '2020-2022'
    , 2021: '2019-2021'
    , 2020: '2018-2020'
    , 2019: '2017-2019'
    , 2018: '2016-2018'
    , 2017: '2015-2017'
}

ACS_5_YEAR_REF = {
    2022: '2018-2022'
    , 2021: '2017-2021'
    , 2020: '2016-2020'
    , 2019: '2015-2019'
    , 2018: '2014-2018'
    , 2017: '2013-2017'
}


wkbooks = {
    2022: '2025 County Health Rankings California Data - v3.xlsx'
    , 2021: '2024 County Health Rankings California Data - v2.xlsx'
    # , 2021: '2023 County Health Rankings California Data - v3.xlsx' # 2023 has the same data as 2022, idk why
    , 2020: '2022 County Health Rankings California Data - v2.xlsx'
    , 2019: '2021 County Health Rankings California Data - v1.xlsx'
    , 2018: '2020 County Health Rankings California Data - v1_0.xlsx'
    , 2017: '2019 County Health Rankings California Data - v1_0.xlsx'
}


counties = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']




if __name__ == '__main__':

    list_df = []
    for year, wkbook in tqdm(wkbooks.items()):
        
        df = proc_wkbook(wkbook)
        list_df.append(df)

    df = pd.concat(list_df)
    df_mpo = regional_rollup(df)

    print('\nCombined Table:')
    display(df.head())
    print('\n'*2)

    if EXPORT:

        survey = 'CHRR'
        indicator = 'Health_4'
        year_start = df['Year'].min()
        year_end = df['Year'].max()
        geography = 'Counties'

        params = {
            'sample': survey
            , 'indicator': indicator
            , 'start_year': year_start
            , 'end_year': year_end
            , 'geo': geography
            , 'estimate': None
            , 'moe_thresh': 0.05
        }

        df_about = func.write_about(params)

        print("Visual representation of the output for:", indicator)
        display(df_about)

        paths = [PATH_SP, PATH_SERVER]

        for path_ in paths:

            file_ = path_ / f'{indicator} {geography} {survey}.xlsx'
            with pd.ExcelWriter(file_, engine='openpyxl') as writer:
                df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                df      .to_excel(writer, index=False, sheet_name='County')
                df_mpo  .to_excel(writer, index=False, sheet_name='Region')

        print("\nSuccessfully exported!\n")


