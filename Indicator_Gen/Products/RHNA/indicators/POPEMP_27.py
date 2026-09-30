

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

PATH_MNR = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')


if __name__ == '__main__':

    df_places_sub   = pd.read_excel(PATH_DATA/f'{INDICATOR} Places SUBJECT5.xlsx'  , sheet_name='Places'  )
    df_counties_sub = pd.read_excel(PATH_DATA/f'{INDICATOR} Counties SUBJECT5.xlsx', sheet_name='Counties')
    df_mpo_sub      = pd.read_excel(PATH_DATA/f'{INDICATOR} MPO SUBJECT5.xlsx'     , sheet_name='MPO'     )

    df_places_dec   = pd.read_excel(PATH_DATA/f'{INDICATOR} Places DEC.xlsx'  , sheet_name='Places'  )
    df_counties_dec = pd.read_excel(PATH_DATA/f'{INDICATOR} Counties DEC.xlsx', sheet_name='Counties')
    df_mpo_dec      = pd.read_excel(PATH_DATA/f'{INDICATOR} MPO DEC.xlsx'     , sheet_name='MPO'     )


    df_places_sub   = df_places_sub  [['County Name', 'NAME', 'Year', 'Median Age']].rename(columns={'NAME':'Geography'})
    df_counties_sub = df_counties_sub[['County Name',         'Year', 'Median Age']].rename(columns={'County Name':'Geography'})
    df_mpo_sub      = df_mpo_sub     [[               'NAME', 'Year', 'Median Age']].rename(columns={'NAME':'Geography'})

    df_places_dec   = df_places_dec  [['County Name', 'NAME', 'Year', 'Median Age']].rename(columns={'NAME':'Geography'})
    df_counties_dec = df_counties_dec[['County Name',         'Year', 'Median Age']].rename(columns={'County Name':'Geography'})
    df_mpo_dec      = df_mpo_dec     [[               'NAME', 'Year', 'Median Age']].rename(columns={'NAME':'Geography'})

    df_mpo_sub['Geography'] = 'SACOG Region'
    df_mpo_dec['Geography'] = 'SACOG Region'

    df_places   = pd.concat([df_places_sub  , df_places_dec  ])
    df_counties = pd.concat([df_counties_sub, df_counties_dec])
    df_mpo      = pd.concat([df_mpo_sub     , df_mpo_dec     ])


    counties = df_places['County Name'].unique()

    for county in counties:

        print('\n'*2)
        print(county)
        print()
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography'] == county]
        df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'
        df_places_sub = df_places[df_places['County Name'] == county].drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_prod.copy()
            df_prod = df_prod.pivot_table(index='Year', columns='Geography', values='Median Age').reset_index()
            df_prod = rhna.cols_geo_rename(df_prod, params['Columns'].split('<>'), county, jurisdiction)
            df_plot = df_plot.sort_values('Year', ascending=True)
            df_plot['Year'] = df_plot['Year'].astype(str)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

