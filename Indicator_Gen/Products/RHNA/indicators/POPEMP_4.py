

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time


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

    df_places1['NAME'] = df_places1['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places1['NAME'] = df_places1['NAME'].str.replace(' city, California', '', regex=True)
    df_places2['NAME'] = df_places2['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places2['NAME'] = df_places2['NAME'].str.replace(' city, California', '', regex=True)

    df_places1 = df_places1.rename(columns={'NAME':'Geography', 'Variable':'Age Group'})
    df_places2 = df_places2.rename(columns={'NAME':'Geography', 'Variable':'Age Group'})

    df_places1 = df_places1.groupby(['County Name', 'Geography', 'Age Group', 'Year'], as_index=False)['Population'].sum()
    df_places2 = df_places2.groupby(['County Name', 'Geography', 'Age Group', 'Year'], as_index=False)['Population'].sum()

    df_places1['Percent'] = df_places1['Population'] / df_places1.groupby(['County Name', 'Geography', 'Year'])['Population'].transform('sum')
    df_places2['Percent'] = df_places2['Population'] / df_places2.groupby(['County Name', 'Geography', 'Year'])['Population'].transform('sum')

    df_places = pd.concat([df_places1, df_places2])
    df_places['Year'] = df_places['Year'].astype(str)
    df_places['Year'] = 'Year ' + df_places['Year']


    counties = df_places['County Name'].unique()

    for county in counties:
        
        rhna.print2()
        print(county); print()
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county].drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Age Group', columns='Year', values='Population').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Age Group', columns='Year', values='Percent'   ).reset_index()

            df_prod = rhna.sort_categorical(df_prod, 'Age Group', ['Age 0-4', 'Age 5-17', 'Age 18-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64', 'Age 65-74', 'Age 75-84', 'Age 85+'])
            df_pct  = rhna.sort_categorical(df_pct , 'Age Group', ['Age 0-4', 'Age 5-17', 'Age 18-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64', 'Age 65-74', 'Age 75-84', 'Age 85+'])
            
            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction].drop(['Geography', 'Percent'], axis=1)
            df_plot['Year'] = df_plot['Year'].str.replace('Year ', '')
            df_plot['Sort'] = pd.Categorical(df_plot['Age Group'], ['Age 0-4', 'Age 5-17', 'Age 18-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64', 'Age 65-74', 'Age 75-84', 'Age 85+'])
            df_plot = df_plot.sort_values(['Sort', 'Year'], ascending=[True, True]).drop(['Sort'], axis=1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)
