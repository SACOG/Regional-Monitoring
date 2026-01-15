




import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px


FILE_CHAS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / f'HUD_CHAS_2017thru2021.csv'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()





if __name__ == '__main__':

    indicator = 'RHNA_OVER_2'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Households'
    columns = 'Severity'



    ## Organizing ---

    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = ['T10_est3', 'T10_est24', 'T10_est45', 'T10_est67', 'T10_est88', 'T10_est109']

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())


    df_chas = df_chas[['County Name', 'name', 'Description 2', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 2':'Severity'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Severity'] == ' AND persons per room is less than or equal to 1'
        , df_chas['Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
        , df_chas['Severity'] == ' AND persons per room is greater than 1.5'
    ]

    choices = ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', '1.5 occupants per room or more']

    df_chas['Severity'] = np.select(conditions, choices, default='no')
    df_chas = df_chas.reset_index(drop=True)

    df_chas     = df_chas.groupby(['County Name', 'name', 'Severity'], as_index=False)['Households'].sum()
    df_counties = df_chas.groupby(['County Name',         'Severity'], as_index=False)['Households'].sum()
    df_mpo      = df_chas.groupby([                       'Severity'], as_index=False)['Households'].sum()
    df_mpo['MPO'] = 'SACOG'

    df_chas    ['Percentage'] = df_chas    ['Households'] / df_chas    .groupby(['County Name', 'name'])['Households'].transform('sum')
    df_counties['Percentage'] = df_counties['Households'] / df_counties.groupby(['County Name'        ])['Households'].transform('sum')
    df_mpo     ['Percentage'] = df_mpo     ['Households'] / df_mpo     .groupby(['MPO'                ])['Households'].transform('sum')

    df_chas     = df_chas    .rename(columns = {'name':'Geography'})
    df_counties = df_counties.rename(columns = {'County Name':'Geography'})
    df_mpo      = df_mpo     .rename(columns = {'MPO':'Geography'})

    df_chas    = df_chas    .reset_index(drop=True)
    df_counties= df_counties.reset_index(drop=True)
    df_mpo     = df_mpo     .reset_index(drop=True)




    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography'  ] == county]
        df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'
        df_chas_sub     = df_chas    [df_chas    ['County Name'] == county]

        df_chas_sub = df_chas_sub.drop(['County Name'], axis=1)
        jurisdictions = df_chas_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod = df_prod.drop('Percentage', axis=1)
            df_prod = df_prod.pivot_table(index=['Geography'], columns=columns, values=values).reset_index()
            df_prod = df_prod[['Geography', 'Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', '1.5 occupants per room or more']]

            df_pct = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.drop('Households', axis=1)
            df_pct = df_pct.pivot_table(index=['Geography'], columns=columns, values='Percentage').reset_index()
            df_pct = df_pct[['Geography', 'Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', '1.5 occupants per room or more']]

            ## Plotting ---

            df_plot = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            df_plot['sort'] = pd.Categorical(df_plot[columns], ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', '1.5 occupants per room or more'])
            df_plot = df_plot.sort_values('sort')
            df_plot = df_plot.drop('sort', axis=1)
            
            color_map  = {
                'Less than or equal to 1 person per room': '#1F45FC'
                , '1.01 to 1.5 occupants per room': '#1E90FF'
                , '1.5 occupants per room or more': '#9DC209'
            }

            fig = px.bar(df_plot, x='Geography', y='Percentage'
                        , color = columns
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_layout(legend={'traceorder': 'reversed'})
        
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

