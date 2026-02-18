


import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import warnings; warnings.filterwarnings("ignore")

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


FILE_CHAS = PATH_DATA / f'HUD_CHAS_2017thru2021.csv'

if __name__ == '__main__':

    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = ['T10_est3', 'T10_est24', 'T10_est45', 'T10_est67', 'T10_est88', 'T10_est109']

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())


    df_chas = df_chas[['County Name', 'name', 'Description 2', 'Households']].rename(columns = {'Description 2':'Overcrowding Severity'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Overcrowding Severity'] == ' AND persons per room is less than or equal to 1'
        , df_chas['Overcrowding Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
        , df_chas['Overcrowding Severity'] == ' AND persons per room is greater than 1.5'
    ]
    choices = ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', 'More than 1.5 occupants per room']
    df_chas['Overcrowding Severity'] = np.select(conditions, choices, default='no')

    df_chas     = df_chas.groupby(['County Name', 'name', 'Overcrowding Severity'], as_index=False)['Households'].sum()
    df_counties = df_chas.groupby(['County Name',         'Overcrowding Severity'], as_index=False)['Households'].sum()
    df_mpo      = df_chas.groupby([                       'Overcrowding Severity'], as_index=False)['Households'].sum()
    df_mpo['MPO'] = 'SACOG Region'

    df_chas    ['Percent'] = df_chas    ['Households'] / df_chas    .groupby(['County Name', 'name'])['Households'].transform('sum')
    df_counties['Percent'] = df_counties['Households'] / df_counties.groupby(['County Name'        ])['Households'].transform('sum')
    df_mpo     ['Percent'] = df_mpo     ['Households'] / df_mpo     .groupby(['MPO'                ])['Households'].transform('sum')

    df_chas     = df_chas    .rename(columns = {'name'       :'Geography'}).reset_index(drop=True)
    df_counties = df_counties.rename(columns = {'County Name':'Geography'}).reset_index(drop=True)
    df_mpo      = df_mpo     .rename(columns = {'MPO'        :'Geography'}).reset_index(drop=True)


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography'] == county]
        df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'

        df_chas_sub = df_chas[df_chas['County Name'] == county].drop(['County Name'], axis=1)
        jurisdictions = df_chas_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod = df_prod.pivot_table(index='Overcrowding Severity', columns='Geography', values='Households').reset_index()
            df_prod = rhna.cols_geo_rename(df_prod, params['Columns'].split('<>'), county, jurisdiction)

            df_pct = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.pivot_table(index='Overcrowding Severity', columns='Geography', values='Percent').reset_index()
            df_pct = rhna.cols_geo_rename(df_pct , params['Columns'].split('<>'), county, jurisdiction)

            df_prod = rhna.sort_categorical(df_prod, 'Overcrowding Severity', ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', 'More than 1.5 occupants per room'])
            df_pct  = rhna.sort_categorical(df_pct , 'Overcrowding Severity', ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', 'More than 1.5 occupants per room'])

            df_plot = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)
            df_plot['Sort'] = pd.Categorical(df_plot['Geography'], [jurisdiction, f'{county} County', 'SACOG Region'])
            df_plot = df_plot.sort_values(['Sort', 'Percent of Households'], ascending=[True, False]).drop('Sort', axis=1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

