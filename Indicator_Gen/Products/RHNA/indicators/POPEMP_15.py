


import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from IPython.display import display


import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_AREA = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'config' / 'area_codes.xlsx'
FILE_EMPLOYMENT = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / f'laborforceandunemployment_monthly_2025422.csv'


if __name__ == '__main__':

    df_codes = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
    df_codes = df_codes[(df_codes['Year']==2020) & (df_codes['MPO'] == 'SACOG')]
    df_codes = df_codes[['NAME', 'MPO', 'County Name', 'Incorporated']].drop_duplicates().reset_index(drop=True)
    df_codes = df_codes.rename(columns={'NAME':'Geography'})
    df_codes['Geography'] = df_codes['Geography'].str.replace(' city', '')
    df_codes['Geography'] = df_codes['Geography'].str.replace(' CDP', '')
    df_codes['Geography'] = df_codes['Geography'].str.replace(' town', '')

    df_places   = pd.read_csv(FILE_EMPLOYMENT)
    df_counties = pd.read_csv(FILE_EMPLOYMENT)
    
    df_places   = df_places  .rename(columns={'Area Name':'Geography'})
    df_counties = df_counties.rename(columns={'Area Name':'Geography'})

    df_places['Geography'] = df_places['Geography'].str.replace(' city', '')
    df_places['Geography'] = df_places['Geography'].str.replace(' CDP' , '')
    df_places['Geography'] = df_places['Geography'].str.replace(' town', '')
    df_places = df_places.merge(df_codes, on='Geography', how='left')
    df_places = df_places[df_places['MPO'] == 'SACOG']
    df_places.loc[df_places['Incorporated'] != 'Yes', 'Geography'] = 'Unincorporated'

    wm = lambda x: np.average(x, weights = df_places.loc[x.index, "Labor Force"])
    df_places = df_places.groupby(['County Name', 'Geography', 'Year'], as_index=False).agg(unemployment_rate=('Unemployment Rate', wm))
    df_places['County Name'] = df_places['County Name'] + ' County'

    df_counties = df_counties[df_counties['Geography'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
    df_counties = df_counties[df_counties['Year'] >= 2010]
    df_mpo = df_counties.copy()

    wm = lambda x: np.average(x, weights = df_counties.loc[x.index, "Labor Force"])
    df_counties = df_counties.groupby(['Geography', 'Year'], as_index=False).agg(unemployment_rate=('Unemployment Rate', wm))

    wm = lambda x: np.average(x, weights = df_mpo.loc[x.index, "Labor Force"])
    df_mpo = df_mpo.groupby(['Year'], as_index=False).agg(unemployment_rate=('Unemployment Rate', wm))
    df_mpo['Geography'] = 'SACOG Region'


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_counties_sub = df_counties.copy()
        df_counties_sub = df_counties_sub[df_counties_sub['Geography'] == county]

        df_places_sub = df_places.copy()
        df_places_sub = df_places_sub[df_places_sub['County Name'] == county].drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod['unemployment_rate'] = df_prod['unemployment_rate']/100
            df_prod = df_prod.pivot_table(index='Year', columns='Geography', values='unemployment_rate').reset_index()
            df_prod = df_prod[['Year', jurisdiction, county, 'SACOG Region']]
            if jurisdiction == 'Sacramento':
                display(df_prod.head())
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot=df_plot.rename(columns={'unemployment_rate':'Unemployment Rate'})

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

