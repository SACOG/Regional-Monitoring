


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
    estimates = ['T7_est3', 'T7_est24', 'T7_est45', 'T7_est66', 'T7_est87', 'T7_est109', 'T7_est130', 'T7_est151', 'T7_est172', 'T7_est193']

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())

    df_chas = df_chas[['County Name', 'name', 'Description 2', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 2':'Income Level'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Income Level'] == 'household income is less than or equal to 30% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 30% but less than or equal to 50% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 50% but less than or equal to 80% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 80% but less than or equal to 100% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 100% of HAMFI'
    ]
    choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']
    df_chas['Income Level'] = np.select(conditions, choices, default='no')

    df_chas     = df_chas.groupby(['County Name', 'name', 'Income Level'], as_index=False)['Households'].sum()
    df_counties = df_chas.groupby(['County Name',         'Income Level'], as_index=False)['Households'].sum()
    df_mpo      = df_chas.groupby([                       'Income Level'], as_index=False)['Households'].sum()
    df_mpo['MPO'] = 'SACOG Region'

    df_chas    ['Percent'] = df_chas    ['Households'] / df_chas    .groupby(['County Name', 'name'])['Households'].transform('sum')
    df_counties['Percent'] = df_counties['Households'] / df_counties.groupby(['County Name'        ])['Households'].transform('sum')
    df_mpo     ['Percent'] = df_mpo     ['Households'] / df_mpo     .groupby(['MPO'                ])['Households'].transform('sum')

    df_chas     = df_chas    .reset_index(drop=True).rename(columns = {'name':'Geography'})
    df_counties = df_counties.reset_index(drop=True).rename(columns = {'County Name':'Geography'})
    df_mpo      = df_mpo     .reset_index(drop=True).rename(columns = {'MPO':'Geography'})


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2); print()

        df_counties_sub              = df_counties    [df_counties['Geography'  ] == county]
        df_chas_sub                  = df_chas        [df_chas    ['County Name'] == county]
        df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'

        df_chas_sub = df_chas_sub.drop(['County Name'], axis=1)
        jurisdictions = df_chas_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod = df_prod.pivot_table(index='Income Level', columns='Geography', values='Households').reset_index()
            df_prod['Sort'] = pd.Categorical(df_prod['Income Level'], ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', 'Greater than 100% of AMI'])
            df_prod = df_prod.sort_values(['Sort']).drop(['Sort'], axis=1).reset_index(drop=True)

            df_pct = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_pct = df_pct.pivot_table(index='Income Level', columns='Geography', values='Percent').reset_index()
            df_pct['Sort'] = pd.Categorical(df_pct['Income Level'], ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', 'Greater than 100% of AMI'])
            df_pct = df_pct.sort_values(['Sort']).drop(['Sort'], axis=1).reset_index(drop=True)
            
            df_plot = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)
