

import pandas as pd
import numpy as np
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


if __name__ == '__main__':

    df_dof = pd.read_excel(PATH_DATA / 'DOF_E5_and_E8_Jurisdictions.xlsx')
    df_dof = df_dof[df_dof['MPO'] == 'SACOG']
    df_dof['MPO'] = df_dof['MPO'] + ' Region'
    df_dof = df_dof[df_dof['Year'].isin([2010, 2020, 2024])].sort_values('Year')
    df_dof['Year'] = df_dof['Year'].astype(str)

    df_dof = df_dof[['County', 'Jurisdiction', 'Year', 'Single Attached', 'Single Detached', 'Two to Four', 'Five Plus', 'Mobile Homes']]

    df_dof = df_dof.melt(id_vars=['County', 'Jurisdiction', 'Year'], var_name='Housing Type', value_name='Households')
    df_dof = df_dof.reset_index(drop=True)

    conditions = [
        df_dof['Housing Type'] == 'Single Attached'
        , df_dof['Housing Type'] == 'Single Detached'
        , df_dof['Housing Type'] == 'Two to Four'
        , df_dof['Housing Type'] == 'Five Plus'
        , df_dof['Housing Type'] == 'Mobile Homes'
    ]
    choices = ['Single Family Attached', 'Single Family Detached', 'Multifamily: Two to Four Units', 'Multifamily: 5+ Units', 'Mobile Homes']
    df_dof['Housing Type'] = np.select(conditions, choices, default='no')

    counties = list(df_dof['County'].unique())

    df_dof_region = df_dof.groupby(['Year', 'Housing Type'], as_index=False)['Households'].sum()
    df_dof_region['County'] = 'SACOG Region'
    df_dof_region['Jurisdiction'] = 'SACOG Region'


    for county in counties:
        print();print()
        print(county)
        time.sleep(2)
        
        df_dof_sub = df_dof[df_dof['County'] == county]
        df_dof_county = df_dof_sub.groupby(['County', 'Year', 'Housing Type'], as_index=False)['Households'].sum()
        df_dof_county['Jurisdiction'] = f'{county} County'

        jurisdictions = df_dof_sub['Jurisdiction'].unique()

        for jurisdiction in tqdm(jurisdictions):
            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_dof_sub[df_dof_sub['Jurisdiction'] == jurisdiction], df_dof_county, df_dof_region])
            df_prod['Year'] = df_prod['Jurisdiction'] + ' (' + df_prod['Year'] + ')'
            df_prod = df_prod.pivot_table(index='Housing Type', columns='Year', values='Households').reset_index()
            df_prod = df_prod[['Housing Type',
                               f'{jurisdiction} (2010)',  f'{jurisdiction} (2020)',  f'{jurisdiction} (2024)',
                              f'{county} County (2010)', f'{county} County (2020)', f'{county} County (2024)',
                                  'SACOG Region (2010)',     'SACOG Region (2020)',     'SACOG Region (2024)']]

            df_plot = df_dof_sub[df_dof_sub['Jurisdiction'] == jurisdiction]
            dt_type_map = {
                'Single Family Attached': 'Single Family<br>Attached',
                'Single Family Detached': 'Single Family<br>Detached',
                'Multifamily: Two to Four Units': 'Multifamily:<br>Two to Four Units',
                'Multifamily: 5+ Units': 'Multifamily:<br>5+ Units',
                'Mobile Homes': 'Mobile Homes'
            }
            df_plot['Housing Type'] = df_plot['Housing Type'].map(dt_type_map)            

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)



