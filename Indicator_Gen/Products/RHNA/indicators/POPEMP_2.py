

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


if __name__ == '__main__':

    df_places2 = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR} Places ACS5.xlsx', sheet_name='Places')
    df_places1 = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR} Places DEC.xlsx' , sheet_name='Places')

    df_places1['Geography'] = df_places1['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places1['Geography'] = df_places1['NAME'].str.replace(' city, California', '', regex=True)
    df_places2['Geography'] = df_places2['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places2['Geography'] = df_places2['NAME'].str.replace(' city, California', '', regex=True)

    df_places1 = df_places1.rename(columns={'Race_Ethnicity':'Race/Ethnicity'})
    df_places2 = df_places2.rename(columns={'Race_Ethnicity':'Race/Ethnicity'})

    df_places1 = df_places1[df_places1['Race/Ethnicity'] != 'All'][['County Name', 'Geography', 'Year', 'Race/Ethnicity', 'Population', 'Percentage']]
    df_places2 = df_places2[df_places2['Race/Ethnicity'] != 'All'][['County Name', 'Geography', 'Year', 'Race/Ethnicity', 'Population', 'Percentage']]

    df_places1.loc[df_places1['Race/Ethnicity'].isin(['Some other race (NH)', 'Two or more races (NH)']), 'Race/Ethnicity'] = 'Other race or multiple races (NH)'
    df_places2.loc[df_places2['Race/Ethnicity'].isin(['Some other race (NH)', 'Two or more races (NH)']), 'Race/Ethnicity'] = 'Other race or multiple races (NH)'

    df_places1 = df_places1.groupby(['County Name', 'Geography', 'Year', 'Race/Ethnicity'], as_index=False)['Population'].sum()
    df_places2 = df_places2.groupby(['County Name', 'Geography', 'Year', 'Race/Ethnicity'], as_index=False)['Population'].sum()

    df_places1['Percent'] = df_places1['Population'] / df_places1.groupby(['County Name', 'Geography', 'Year'])['Population'].transform('sum')
    df_places2['Percent'] = df_places2['Population'] / df_places2.groupby(['County Name', 'Geography', 'Year'])['Population'].transform('sum')

    df_places = pd.concat([df_places1, df_places2])


    counties = df_places['County Name'].unique()

    for county in counties:
        
        rhna.print2()
        print(county); print()
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county].drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction]

            df_prod['Year'] = 'Year ' + df_prod['Year'].astype(str)
            df_pct ['Year'] = 'Year ' + df_pct ['Year'].astype(str)

            df_prod = df_prod.pivot_table(index='Race/Ethnicity', columns='Year', values='Population').reset_index()
            df_pct  = df_pct .pivot_table(index='Race/Ethnicity', columns='Year', values='Percent'   ).reset_index()

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction].sort_values(['Year', 'Percent'], ascending=[True, False])
            df_plot['Year'] = df_plot['Year'].astype(str)
            df_plot['Percent of Population'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)
