

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import warnings

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
warnings.filterwarnings("ignore")


yaml_file = rhna.load_yaml()
PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_AREA = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'



ACS_YEAR = 2022
START_YEAR = ACS_YEAR-4


if __name__ == '__main__':

    FILE_CHAS = PATH_DATA / f'HUD_CHAS_{START_YEAR}thru{ACS_YEAR}.csv'
    
    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = ['T7_est3', 'T7_est24', 'T7_est45', 'T7_est66', 'T7_est87', 'T7_est109', 'T7_est130', 'T7_est151', 'T7_est172', 'T7_est193']


    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())

    df_chas = df_chas[['County Name', 'name', 'Description 1', 'Description 2', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 1':'Tenure', 'Description 2':'Income Level'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True).replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Income Level'  ] == 'household income is less than or equal to 30% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 30% but less than or equal to 50% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 50% but less than or equal to 80% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 80% but less than or equal to 100% of HAMFI'
        , df_chas['Income Level'] == 'household income is greater than 100% of HAMFI'
    ]
    choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']
    df_chas['Income Level'] = np.select(conditions, choices, default='no')

    conditions = [
          df_chas['Tenure'] == 'Owner occupied'
        , df_chas['Tenure'] == 'Renter occupied'
    ]
    choices = ['Owner Occupied', 'Renter Occupied']
    df_chas['Tenure'] = np.select(conditions, choices, default='no')

    df_chas = df_chas.groupby(['County Name', 'name', 'Tenure', 'Income Level'], as_index=False)['Households'].sum()
    df_chas['Percent'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Tenure'])['Households'].transform('sum')
    df_chas = df_chas.reset_index(drop=True)

    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)
        print()

        df_chas_sub = df_chas[df_chas['County Name'] == county]
        jurisdictions = df_chas_sub['name'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index=['Income Level'], columns='Tenure', values='Households').reset_index()
            df_pct  = df_chas_sub[df_chas_sub['name'] == jurisdiction].pivot_table(index=['Income Level'], columns='Tenure', values='Percent'   ).reset_index()

            df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)
