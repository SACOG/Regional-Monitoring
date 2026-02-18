

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from IPython.display import display
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


    df_chas = df_chas[['County Name', 'name', 'Description 1', 'Description 2', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 1':'Housing Tenure', 'Description 2':'Overcrowding Severity'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
          df_chas['Overcrowding Severity'] == ' AND persons per room is less than or equal to 1'
        , df_chas['Overcrowding Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
        , df_chas['Overcrowding Severity'] == ' AND persons per room is greater than 1.5'
    ]

    choices = ['Less than or equal to 1 person per room', '1.01 to 1.5 occupants per room', 'More than 1.5 occupants per room']
    df_chas['Overcrowding Severity'] = np.select(conditions, choices, default='no')
    df_chas['Percent'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Housing Tenure'])['Households'].transform('sum')
    df_chas = df_chas[df_chas['Overcrowding Severity'] != 'Less than or equal to 1 person per room'].reset_index(drop=True)

    display(df_chas)


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_chas_sub = df_chas[df_chas['County Name'] == county]
        jurisdictions = df_chas_sub['name'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index='Housing Tenure', columns='Overcrowding Severity', values='Households').reset_index()
            df_pct  = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index='Housing Tenure', columns='Overcrowding Severity', values='Percent'   ).reset_index()
            
            df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_plot['Percent'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

