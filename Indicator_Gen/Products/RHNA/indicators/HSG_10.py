


import numpy as np
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

FILE_AREA = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'
FILE_WEIGHTS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Households Places ACS5.xlsx'



if __name__ == '__main__':


    df_places, df_counties, df_mpo = rhna.acs_import(INDICATOR)
    df_places['Place ID'] = df_places['Place ID'].astype(str).apply('{:0>5}'.format)

    df_codes = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
    df_codes = df_codes[(df_codes['MPO'].str.contains('SACOG')) & (df_codes['Incorporated']=='Yes') & (df_codes['Year']==2020)]
    df_codes['place'] = df_codes['place'].astype(str).apply('{:0>5}'.format)
    CDP_inc = list(df_codes['place'].unique())

    df_places.loc[~df_places['Place ID'].isin(CDP_inc), 'NAME'] = 'Unincorporated'

    df_weight = pd.read_excel(FILE_WEIGHTS, sheet_name='Places')
    df_weight = df_weight[df_weight['Race/Ethnicity'] == 'All'][['Place ID', 'Year', 'Households']].reset_index(drop=True)
    df_weight['Place ID'] = df_weight['Place ID'].astype(str).apply('{:0>5}'.format)

    df_places = df_places.merge(df_weight, on=['Place ID', 'Year'], how='left')

    wm = lambda x: np.average(x, weights = df_places.loc[x.index, 'Households']) # weighted average (or Population or Households)
    df_places = df_places.groupby(['County Name', 'NAME', 'Year'], as_index=False, sort=False).agg(Total=('Median Contract Rent', wm))
    df_places = df_places.rename(columns={'Total':'Median Contract Rent'})

    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
    df_counties['NAME'] = df_counties['NAME'].str.replace(', California'     , '', regex=True)

    df_places   = df_places  .rename(columns={'NAME':'Geography'})
    df_counties = df_counties.rename(columns={'NAME':'Geography'})
    df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography'})
    df_mpo['Geography'] = df_mpo['Geography'] + ' Region'
    df_mpo = df_mpo.drop_duplicates()

    df_places   = df_places  [['County Name', 'Geography', 'Year', 'Median Contract Rent']].reset_index(drop=True)
    df_counties = df_counties[[               'Geography', 'Year', 'Median Contract Rent']].reset_index(drop=True)
    df_mpo      = df_mpo     [[               'Geography', 'Year', 'Median Contract Rent']].reset_index(drop=True)


    counties = df_counties['Geography'].unique()

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
            tqdm.write(jurisdiction)
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod = df_plot.pivot_table(index='Year', columns='Geography', values='Median Contract Rent').reset_index()
            df_prod = df_prod[['Year', jurisdiction, county, 'SACOG Region']].sort_values('Year', ascending=True).reset_index(drop=True)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

