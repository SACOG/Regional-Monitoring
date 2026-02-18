

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

    df_places1 = df_places1.rename(columns={'NAME':'Geography', 'Variable': 'Housing Tenure'})
    df_places2 = df_places2.rename(columns={'NAME':'Geography', 'Variable': 'Housing Tenure'})

    df_places1 = df_places1[['County Name', 'Geography', 'Year', 'Housing Tenure', 'Households']]
    df_places2 = df_places2[['County Name', 'Geography', 'Year', 'Housing Tenure', 'Households']]

    df_places1 = df_places1.pivot_table(index=['County Name', 'Geography', 'Year'], columns='Housing Tenure', values='Households').reset_index()
    df_places1['Owner occupied'] = df_places1['Total'] - df_places1['Renter occupied']
    df_places1 = df_places1.drop('Total', axis=1)
    df_places1 = df_places1.melt(id_vars=['County Name', 'Geography', 'Year'], var_name='Housing Tenure', value_name='Households')

    df_places = pd.concat([df_places1, df_places2])
    df_places['Percent'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', 'Year'])['Households'].transform('sum')


    counties = df_places['County Name'].unique()

    for county in counties:
        
        rhna.print2()
        print(county); print()
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county].drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Year', columns='Housing Tenure', values='Households').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Year', columns='Housing Tenure', values='Percent'   ).reset_index()

            df_plot = df_pct.melt(id_vars='Year', var_name='Housing Tenure', value_name='Percent')
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)
            df_plot = df_plot.sort_values(['Year', 'Percent of Households'], ascending=[True, False])
            df_plot['Year'] = df_plot['Year'].astype(str)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

