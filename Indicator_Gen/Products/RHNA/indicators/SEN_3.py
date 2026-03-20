

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import warnings

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_CHAS = PATH_DATA / f'HUD_CHAS_2017thru2021.csv'
FILE_AREA = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'

warnings.filterwarnings("ignore")

if __name__ == '__main__':

    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = [
        'T7_est17', 'T7_est18', 'T7_est19', 'T7_est38', 'T7_est39', 'T7_est40', 'T7_est59', 'T7_est60', 'T7_est61',
        'T7_est80', 'T7_est81', 'T7_est82', 'T7_est101', 'T7_est102', 'T7_est103', 'T7_est123', 'T7_est124', 'T7_est125',
        'T7_est144', 'T7_est145', 'T7_est146', 'T7_est165', 'T7_est166', 'T7_est167', 'T7_est186', 'T7_est187', 'T7_est188',
        'T7_est207', 'T7_est208', 'T7_est209'
    ]

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())

    df_chas = df_chas[['County Name', 'name', 'Description 2', 'Description 4', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 4':'Cost Burden', 'Description 2':'Income Level'})
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

    conditions = [
        df_chas['Cost Burden'] == 'housing cost burden is less than or equal to 30%'
        , df_chas['Cost Burden'] == 'housing cost burden is greater than 30% but less than or equal to 50%'
        , df_chas['Cost Burden'] == 'housing cost burden is greater than 50%'
        , df_chas['Cost Burden'] == 'housing cost burden not computed (no/negative income)'
    ]
    choices = ['0%-30% of income used for housing', '30%-50% of income used for housing', '50%+ of income used for housing', 'Not computed']
    df_chas['Cost Burden'] = np.select(conditions, choices, default='no')

    df_chas = df_chas.groupby(['County Name', 'name', 'Income Level', 'Cost Burden'], as_index=False)['Households'].sum()
    df_chas['Percent'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Income Level'])['Households'].transform('sum')
    df_chas = df_chas.reset_index(drop=True)


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        print();print()
        print(county)
        time.sleep(2)

        df_chas_sub = df_chas[df_chas['County Name'] == county]
        jurisdictions = df_chas_sub['name'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index='Income Level', columns='Cost Burden', values='Households').reset_index()
            df_pct  = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index='Income Level', columns='Cost Burden', values='Percent'   ).reset_index()
            
            df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

