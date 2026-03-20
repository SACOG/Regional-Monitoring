

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

FILE_CHAS = PATH_DATA / 'HUD_CHAS_2017thru2021.csv'

warnings.filterwarnings("ignore")


if __name__ == '__main__':

    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = [
        'T8_est4', 'T8_est7', 'T8_est10', 'T8_est13', 'T8_est17', 'T8_est20', 'T8_est23', 'T8_est26', 
        'T8_est30', 'T8_est33', 'T8_est36', 'T8_est39', 'T8_est43', 'T8_est46', 'T8_est49', 'T8_est52', 
        'T8_est56', 'T8_est59', 'T8_est62', 'T8_est65', 'T8_est70', 'T8_est73', 'T8_est76', 'T8_est79',
        'T8_est83', 'T8_est86', 'T8_est89', 'T8_est92', 'T8_est96', 'T8_est99', 'T8_est102', 'T8_est105',
        'T8_est109', 'T8_est112', 'T8_est115', 'T8_est118', 'T8_est122', 'T8_est125', 'T8_est128', 'T8_est131'
    ]

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())

    df_chas = df_chas[['County Name', 'name', 'Description 2', 'Description 3', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 2':'Income Level', 'Description 3':'Cost Burden'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Cost Burden'] == ' AND housing cost burden is less than or equal to 30%'
        , df_chas['Cost Burden'] == ' AND housing cost burden is greater than 30% but less than or equal to 50%'
        , df_chas['Cost Burden'] == ' AND housing cost burden is greater than 50%'
        , df_chas['Cost Burden'] == ' AND housing cost burden not computed (no/negative income)'
    ]
    choices = ['0%-30% of income used for housing', '30%-50% of income used for housing', '50%+ of income used for housing', 'Not computed']
    df_chas['Cost Burden'] = np.select(conditions, choices, default='no')

    conditions = [
        df_chas['Income Level'  ] == ' AND household income is less than or equal to 30% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 30% but less than or equal to 50% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 50% but less than or equal to 80% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 80% but less than or equal to 100% of HAMFI'
        , df_chas['Income Level'] == ' AND household income is greater than 100% of HAMFI'
    ]
    choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']
    df_chas['Income Level'] = np.select(conditions, choices, default='no')

    df_chas = df_chas.groupby(['County Name', 'name', 'Income Level', 'Cost Burden'], as_index=False)['Households'].sum()
    df_chas['Percent'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Income Level'])['Households'].transform('sum')
    df_chas = df_chas.reset_index(drop=True)


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
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

