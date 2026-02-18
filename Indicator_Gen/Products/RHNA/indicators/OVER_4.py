

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
    df_chas = df_chas.rename(columns = {'Description 3':'Income Level', 'Description 2':'Overcrowding Severity'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Overcrowding Severity'] == ' AND persons per room is less than or equal to 1'
        , df_chas['Overcrowding Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
        , df_chas['Overcrowding Severity'] == ' AND persons per room is greater than 1.5'
    ]
    choices = ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', 'More than 1.5 occupants per room']
    df_chas['Overcrowding Severity'] = np.select(conditions, choices, default='no')

    conditions = [
        df_chas['Income Level'  ] == ' AND household income is less than or equal to 30% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 30% but less than or equal to 50% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 50% but less than or equal to 80% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 80% but less than or equal to 100% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 100% of HAMFI'
    ]
    choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']
    df_chas['Income Level'] = np.select(conditions, choices, default='no')

    df_chas = df_chas.groupby(['County Name', 'name', 'Income Level', 'Overcrowding Severity'], as_index=False)['Households'].sum()

    df_chas['Percent'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Income Level'])['Households'].transform('sum')
    df_chas = df_chas[df_chas['Overcrowding Severity'] != 'Less than or equal to 1 person per room'].reset_index(drop=True)


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_chas_sub = df_chas[df_chas['County Name'] == county]
        jurisdictions = df_chas_sub['name'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index='Income Level', columns='Overcrowding Severity', values='Households').reset_index()
            df_pct  = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index='Income Level', columns='Overcrowding Severity', values='Percent'   ).reset_index()
            
            df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


