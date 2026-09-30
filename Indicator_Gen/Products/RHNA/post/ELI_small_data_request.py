

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
FILE_AREA = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'
PATH_OUT = r'I:\Projects\Josh\RHNA\Small data requests'


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
    choices = ['Less than 80% of HAMFI', 'Less than 80% of HAMFI', 'Less than 80% of HAMFI', 'Greater than 80% of HAMFI', 'Greater than 80% of HAMFI']
    df_chas['Income Level'] = np.select(conditions, choices, default='no')

    conditions = [
          df_chas['Tenure'] == 'Owner occupied'
        , df_chas['Tenure'] == 'Renter occupied'
    ]
    choices = ['All', 'All']
    df_chas['Tenure'] = np.select(conditions, choices, default='no')

    df_chas = df_chas.groupby(['County Name', 'name', 'Income Level'], as_index=False)['Households'].sum()
    df_chas['Percent'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name'])['Households'].transform('sum')

    df_r = df_chas.groupby(['Income Level'], as_index=False)['Households'].sum()
    df_r['Percent'] = df_r['Households'] / df_r['Households'].sum()

    df_chas = df_chas[df_chas['Income Level']=='Less than 80% of HAMFI'].drop('Income Level', axis=1).reset_index(drop=True)
    df_r    = df_r   [df_r   ['Income Level']=='Less than 80% of HAMFI'].drop(['Income Level', 'Households'], axis=1).reset_index(drop=True)

    df_chas.columns = ['County Name', 'Jurisdiction', 'Existing Lower Income Households', 'Existing Lower Income Households (%)']

    df_chas['Regional Parity Target (%)'] = df_r['Percent'].values[0]
    
    file_out = Path(PATH_OUT)/'Existing lower income households_py.xlsx'
    df_chas.to_excel(file_out, index=False, sheet_name='Data')