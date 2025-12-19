




'''

Functions:

set_workbook_name()
clean_fips()
misc_mappings()
misc_groups()
acs_processing_1()
acs_processing_2()
acs_processing_3()
pums_processing_1()
pums_processing_2()
pums_processing_3()
pums_processing_4()
foodsec_processing_4()
lehd_processing()
rename_census()
write_about_master()
export_indicator()
foodsec_processing()

'''




import numpy as np
import pandas as pd
from pathlib import Path
from IPython.display import display
import sys

PATH_GIT = Path(__file__).parent.parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'

FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_CPI = PATH_CONFIG0 / 'CPI_IAF.xlsx'
FILE_CONFIG = PATH_CONFIG / 'bls.xlsx'

# SharePoint OneDrive and internal server paths
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
PATH_MAIN = PATH_SP / 'Data'
PATH_WEIGHTS = PATH_MAIN / 'Reference' / 'Weights'
PATH_PROD = PATH_SP / 'Products'
PATH_ABOUT = PATH_SP / 'Process Revamp' / 'Task 6. Process Map'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')


sys.path.append(str(PATH_CONFIG))
import get



def proc_bls(df, dt_params, yaml_bls):

    print()
    print('Processing BLS data...')

    survey    = dt_params['Survey'   ]
    indicator = dt_params['Indicator']
    list_series_all, df_series_area, dt_series = get.create_series_dictionary(dt_params, yaml_bls)

    df = pd.melt(df, id_vars = ['year', 'periodName'], var_name='seriesID', value_name='value')
    df['date_'] = df['year'].astype('str') + '-' + df['periodName'].astype('str')
    df['date_'] = pd.to_datetime(df['date_'])

    if survey in ['SM', 'CE']:
        df['value'] = df['value'].astype('float32').apply(lambda x: x*1000)

    if survey in ['SM', 'LA', 'CE']:       
        df = df.merge(df_series_area, on='seriesID')
        if survey in ['SM', 'CE']:
            df_industries = get.read_industries(indicator, survey)
            df = df.groupby(['date_', 'area_text', 'area_code', 'Variable'], as_index=False).agg(value=('value', 'sum'))
            df = df.pivot_table(index = ['date_', 'area_code', 'area_text'], columns='Variable', values='value').reset_index()
            df = pd.melt(df, id_vars = ['date_', 'area_code', 'area_text'], var_name='Variable', value_name='Value')
            df = df.merge(df_industries[['Variable', 'industry_code']], on='Variable')
            df = df.sort_values(['area_code', 'area_text', 'date_', 'industry_code'], ascending=[True, True, False, True])
        if survey == 'LA':
            df = df.sort_values(['MSA_ID', 'area_text', 'date_'], ascending=[True, True, False])
            df = df[['date_', 'MSA_ID', 'area_text', 'value']]
            df['date_'] = df['date_'].astype('str')

    df = df.reset_index(drop=True)
    display(df.head())

    return df, df_series_area



def jobs_1(df, percentages, geography):

    if percentages == 'Yes':
            df['Percentage'] = df['Value'] / df.groupby(['area_text', 'date_'])['Value'].transform('sum')
            df_pct = df.pivot_table(index = ['area_text', 'date_']
                                               , columns='Variable'
                                               , values='Percentage').reset_index()
            df_pct = df_pct.sort_values(['area_text', 'date_'], ascending=[True, False])
    
    df_all = df.groupby(['date_', 'area_text'], as_index=False)['Value'].agg(sum)
    df_all['Variable'] = 'All'
    df_all['Percentage'] = np.nan
    df_all = df_all.merge(df[['area_text', 'area_code']].drop_duplicates(), on='area_text', how='left')
    
    df_all = pd.concat([df, df_all])
    df_all = df_all.sort_values(['area_code', 'date_', 'Variable'], ascending=[True, False, True])
    df = df_all.copy()
    df = df.reset_index(drop=True)
    df['date_'] = df['date_'].astype('str')
    df = df.drop(['industry_code'], axis=1)
    df = df.sort_values(['area_code', 'date_', 'Variable'], ascending=[True, False, True])

    if geography == 'MSA':
        df = df.rename(columns={'area_text':'MSA', 'Variable':'Sector', 'Value':'Total Jobs', 'area_code':'MSA ID'})
    if geography == 'National':
        df = df.rename(columns={'area_text':'MSA', 'Variable':'Sector', 'Value':'Total Jobs', 'area_code':'MSA ID'})

    display(df.head())

    return df



def jobs_2(df, percentages, geography, df_series_area):


    if geography == 'MSA':
        
        df_msa = df.copy()
        df_msa = df_msa.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
        df_msa = df_msa.drop_duplicates()
        df_mpo = df_msa[df_msa['MSA'].str.contains('Sacramento|Yuba')]

        df_msa = df_msa.groupby(['MSA ID', 'MSA', 'date_', 'Variable', 'industry_code'], as_index=False).agg(value=('Value', 'sum'))
        df_mpo = df_mpo.groupby([                 'date_', 'Variable', 'industry_code'], as_index=False).agg(value=('Value', 'sum'))
        df_mpo['MPO'] = 'SACOG'

        df_msa = df_msa.pivot_table(index = ['MSA ID', 'MSA', 'date_'], columns='Variable', values='value').reset_index()
        df_mpo = df_mpo.pivot_table(index = [          'MPO', 'date_'], columns='Variable', values='value').reset_index()

        df_msa = pd.melt(df_msa, id_vars = ['MSA ID', 'MSA', 'date_'], var_name='Variable', value_name='Value')
        df_mpo = pd.melt(df_mpo, id_vars = [          'MPO', 'date_'], var_name='Variable', value_name='Value')

        df_msa = df_msa.merge(df_series_area[['Variable', 'industry_code']], on='Variable')
        df_mpo = df_mpo.merge(df_series_area[['Variable', 'industry_code']], on='Variable')

        df_msa = df_msa.drop_duplicates(['MSA ID', 'MSA', 'date_', 'Variable', 'Value'])
        df_mpo = df_mpo.drop_duplicates([          'MPO', 'date_', 'Variable', 'Value'])
    
        if percentages == 'Yes':
            vars_to_exclude = ['Total Nonfarm', 'Total Private', 'State Government Educational Services', 'State Government Excluding Education', 'Local Government Educational Services', 'Local Government excluding Educational Services']
            df_msa['Percentage'] = df_msa['Value'] / df_msa[~df_msa['Variable'].isin(vars_to_exclude)].groupby(['MSA', 'date_'])['Value'].transform('sum')
            df_mpo['Percentage'] = df_mpo['Value'] / df_mpo[~df_mpo['Variable'].isin(vars_to_exclude)].groupby(['MPO', 'date_'])['Value'].transform('sum')
    
        df_msa = df_msa.sort_values(['MSA ID', 'MSA', 'date_', 'industry_code'], ascending=[True, True, False, True])
        df_mpo = df_mpo.sort_values([          'MPO', 'date_', 'industry_code'], ascending=[True,       False, True])
        
        df_msa = df_msa.drop(['industry_code'], axis=1)
        df_mpo = df_mpo.drop(['industry_code'], axis=1)
    
        df_msa['date_'] = df_msa['date_'].astype('str')
        df_mpo['date_'] = df_mpo['date_'].astype('str')
    
        df_msa = df_msa.reset_index(drop=True)
        df_mpo = df_mpo.reset_index(drop=True)

        df_msa = df_msa.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
        df_mpo = df_mpo.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
        df_msa['Notes'] = np.nan
        df_msa.loc[df_msa['Total Jobs'] == 0, 'Notes'] = 'No data collected for this specific sector'
        display(df_msa.head(), df_mpo.head())


    if geography == 'National':
        df_nat = df.set_index(['date_']).reset_index()
        df_nat = df_nat.drop(['industry_code'], axis=1) # removed "area_code"
        df_nat = df_nat.drop_duplicates()
        df_nat['date_'] = df_nat['date_'].astype('str')
        df_nat['Percentage'] = df_nat['Value'] / df_nat[~df_nat['Variable'].isin(['Total Nonfarm', 'Total Private', 'State Government', 'Local Government'])].groupby(['area_text', 'date_'])['Value'].transform('sum')
        df_nat = df_nat.rename(columns={'area_text':'Geography', 'Variable':'Sector', 'Value':'Total Jobs'})
        display(df_nat.head())


    if geography == 'MSA':
        return df_msa, df_mpo
    if geography == 'National':
        return df_nat


def jobs_3(df):
    
    df1 = df[df['Variable'].isin(['Total Private'  , 'Government'       ])]
    df2 = df[df['Variable'].isin(['Goods Producing', 'Service-Providing'])]

    df1['Percentage'] = df1['Value'] / df1.groupby(['area_text', 'date_'])['Value'].transform('sum')
    df2['Percentage'] = df2['Value'] / df2.groupby(['area_text', 'date_'])['Value'].transform('sum')

    df1_all = df1.groupby(['date_', 'area_text'], as_index=False)['Value'].agg(sum)
    df1_all['Variable'] = 'All'
    df1_all['Percentage'] = np.nan
    df1_all = df1_all.merge(df1[['area_text', 'area_code']].drop_duplicates(), on='area_text', how='left')
    df1_all = pd.concat([df1, df1_all])
    df1_all = df1_all.sort_values(['area_text', 'date_', 'Variable'], ascending=[True, False, True])
    df1 = df1_all.copy()
    
    df2_all = df2.groupby(['date_', 'area_text'], as_index=False)['Value'].agg(sum)
    df2_all['Variable'] = 'All'
    df2_all['Percentage'] = np.nan
    df2_all = df2_all.merge(df2[['area_text', 'area_code']].drop_duplicates(), on='area_text', how='left')
    df2_all = pd.concat([df2, df2_all])
    df2_all = df2_all.sort_values(['area_text', 'date_', 'Variable'], ascending=[True, False, True])
    df2 = df2_all.copy()

    df1 = df1.drop(['industry_code'], axis=1)
    df2 = df2.drop(['industry_code'], axis=1)

    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    
    df1['date_'] = df1['date_'].astype('str')
    df2['date_'] = df2['date_'].astype('str')

    df1 = df1.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
    df2 = df2.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
    if geography == 'MSA':
        df1 = df1.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
        df2 = df2.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
    if geography == 'National':
        df1 = df1.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
        df2 = df2.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
    display(df1.head(), df2.head())


    return df1, df2


def labor_2(df):
    df['value'] = df['value']/100
    df = df.rename(columns={'area_text':'Geography', 'value':'Unemployment Rate'})
    return df


