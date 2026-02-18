

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from IPython.display import display


import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()


INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


if __name__ == '__main__':

    df_places, df_counties, df_mpo = rhna.dof_import(INDICATOR)
    df_places, df_counties, df_mpo = rhna.dof_clean(df_places, df_counties, df_mpo)
    counties = df_counties['Geography'].unique()

    for county in counties:

        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.dof_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)
        
            df_prod1, df_prod2, df_prod3 = rhna.dof_index(df_places_sub, df_counties_sub, df_mpo, jurisdiction)
            df_prod2['Geography'] = df_prod2['Geography'] + ' County'
            df_plot = pd.concat([df_prod1, df_prod2, df_prod3]).drop(['County', 'Population'], axis=1)
            df_plot['Percent Difference'] = df_plot['growth']*100

            df_prod2 = df_prod2.drop('Geography', axis=1).rename(columns={'Population': f'{county} County', 'growth': f'{county} County_growth'})
            df_prod3 = df_prod3.drop('Geography', axis=1).rename(columns={'Population': 'SACOG'           , 'growth': f'SACOG_growth'          })
            df_prod = df_prod1[df_prod1['Geography'] == jurisdiction].drop(['County', 'Geography'], axis=1).rename(columns = {'Population': jurisdiction, 'growth': f'{jurisdiction}_growth'})
            df_prod = df_prod.merge(df_prod2, on='Year')
            df_prod = df_prod.merge(df_prod3, on='Year')
            df_prod = df_prod[['Year', jurisdiction, f'{county} County', 'SACOG', f'{jurisdiction}_growth', f'{county} County_growth', 'SACOG_growth']].sort_values('Year', ascending=True).reset_index(drop=True)
            df_prod.columns = [col.replace('_growth', ' (% Difference from 2000)') for col in df_prod.columns]
            # df_prod = rhna.cols_geo_rename(df_prod, params['Columns'].split('<>'), county, jurisdiction)

            if jurisdiction == 'Sacramento':
                print()
                print('Final Product:')
                display(df_prod.head())
                print()

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

