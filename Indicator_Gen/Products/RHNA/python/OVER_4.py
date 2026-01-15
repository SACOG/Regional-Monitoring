





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

    indicator = 'RHNA_OVER_4'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Households'
    columns = 'Severity'


    ## Organizing

    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = [
        'T10_est4', 'T10_est8', 'T10_est12', 'T10_est16', 'T10_est20', 'T10_est25', 'T10_est29', 'T10_est33',
        'T10_est37', 'T10_est41', 'T10_est46', 'T10_est50', 'T10_est54', 'T10_est58', 'T10_est62', 'T10_est68',
        'T10_est72', 'T10_est76', 'T10_est80', 'T10_est84', 'T10_est89', 'T10_est93', 'T10_est97', 'T10_est101',
        'T10_est105', 'T10_est110', 'T10_est114', 'T10_est118', 'T10_est122', 'T10_est126'
    ]

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())


    df_chas = df_chas[['County Name', 'name', 'Description 2', 'Description 3', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 3':'Income Level', 'Description 2':'Severity'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Severity'] == ' AND persons per room is less than or equal to 1'
        , df_chas['Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
        , df_chas['Severity'] == ' AND persons per room is greater than 1.5'
    ]

    choices = ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', 'More than 1.5 occupants per room']

    df_chas['Severity'] = np.select(conditions, choices, default='no')

    conditions = [
        df_chas['Income Level'  ] == ' AND household income is less than or equal to 30% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 30% but less than or equal to 50% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 50% but less than or equal to 80% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 80% but less than or equal to 100% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 100% of HAMFI'
    ]

    choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']

    df_chas['Income Level'] = np.select(conditions, choices, default='no')


    df_chas = df_chas.groupby(['County Name', 'name', 'Income Level', 'Severity'], as_index=False)['Households'].sum()

    df_chas['Percentage'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Income Level'])['Households'].transform('sum')
    df_chas = df_chas[df_chas['Severity'] != 'Less than or equal to 1 person per room']


    df_chas = df_chas.reset_index(drop=True)



    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_chas_sub = df_chas[df_chas['County Name'] == county]
        jurisdictions = df_chas_sub['name'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_prod = df_prod.drop('Percentage', axis=1)
            df_prod = df_prod.pivot_table(index=['Income Level'], columns=columns, values=values).reset_index()

            df_pct = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_pct = df_pct.drop('Households', axis=1)
            df_pct = df_pct.pivot_table(index=['Income Level'], columns=columns, values='Percentage').reset_index()
            
            ## Plotting ---

            df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            
            color_map  = {
                '1.01 to 1.5 occupants per room': '#9DC209'
                , 'More than 1.5 occupants per room': '#1F45FC'
            }

            fig = px.bar(df_plot, x='Income Level', y='Percentage'
                        , color = columns
                        , barmode='group'
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_yaxes(ticksuffix='%')

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)


