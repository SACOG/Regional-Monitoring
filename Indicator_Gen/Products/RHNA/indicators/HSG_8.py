

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from IPython.display import display


def extrapolate_weights(df):
    df_temp  = df[df['Year'] == 2023]
    df_temp2 = df[df['Year'] == 2023]
    df_temp ['Year'] = 2024
    df_temp2['Year'] = 2025
    df_temp3  = df[df['Year'] == 2009]
    df_temp4  = df[df['Year'] == 2009]
    df_temp5  = df[df['Year'] == 2009]
    df_temp6  = df[df['Year'] == 2009]
    df_temp7  = df[df['Year'] == 2009]
    df_temp8  = df[df['Year'] == 2009]
    df_temp9  = df[df['Year'] == 2009]
    df_temp10 = df[df['Year'] == 2009]
    df_temp11 = df[df['Year'] == 2009]
    df_temp3['Year'] = 2008
    df_temp4['Year'] = 2007
    df_temp5['Year'] = 2006
    df_temp6['Year'] = 2005
    df_temp7['Year'] = 2004
    df_temp8['Year'] = 2003
    df_temp9['Year'] = 2002
    df_temp10['Year'] = 2001
    df_temp11['Year'] = 2000
    df = pd.concat([df, df_temp, df_temp2, df_temp3, df_temp4, df_temp5, df_temp6, df_temp7, df_temp8, df_temp9, df_temp10, df_temp11])
    return df


import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


FILE_AREA = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'
FILE_ZHVI_CITIES = PATH_DATA / f'City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
FILE_ZHVI_COUNTIES = PATH_DATA / f'County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'

FILE_WEIGHTS_CDP = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Population Places ACS5.xlsx'  
FILE_WEIGHTS_COUNTIES = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Population Counties ACS5.xlsx'


if __name__ == '__main__':

    df_codes = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')

    df_places   = pd.read_csv(FILE_ZHVI_CITIES)
    df_counties = pd.read_csv(FILE_ZHVI_COUNTIES)

    df_w_cities   = pd.read_excel(FILE_WEIGHTS_CDP)
    df_w_counties = pd.read_excel(FILE_WEIGHTS_COUNTIES)

    df_w_cities   = extrapolate_weights(df_w_cities  )
    df_w_counties = extrapolate_weights(df_w_counties)

    df_w_cities  ['Households'] = df_w_cities  ['Population'].copy()
    df_w_counties['Households'] = df_w_counties['Population'].copy()

    df_codes = df_codes[df_codes['MPO'] == 'SACOG'][['NAME', 'Incorporated']].drop_duplicates().rename(columns={'NAME':'Geography'}).reset_index(drop=True)
    df_codes['Geography'] = df_codes['Geography'].str.replace(' city', '')
    df_codes['Geography'] = df_codes['Geography'].str.replace(' CDP' , '')
    df_codes['Geography'] = df_codes['Geography'].str.replace(' town', '')

    df_w_cities = df_w_cities[df_w_cities['Race_Ethnicity'] == 'All'][['NAME', 'Year', 'Households']].rename(columns={'NAME':'Geography'})

    df_places = df_places.rename(columns={'RegionName':'Geography'})
    df_places = df_places[df_places['CountyName'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
    df_places = df_places.drop(['RegionID', 'SizeRank', 'RegionType', 'StateName', 'State', 'Metro'], axis=1)
    df_places = df_places.melt(id_vars=['Geography', 'CountyName'], var_name='date_', value_name='ZHVI')
    df_places = df_places.merge(df_codes, on='Geography', how='left')
    df_places['date_'] = pd.to_datetime(df_places['date_'])
    df_places['Year'] = df_places['date_'].dt.year
    df_places = df_places.drop('date_', axis=1)

    df_places = df_places.merge(df_w_cities, on=['Geography', 'Year'], how='left')
    df_places = df_places.dropna(subset=['Households', 'ZHVI']).reset_index(drop=True)
    df_places.loc[df_places['Incorporated'] != 'Yes', 'Geography'] = 'Unincorporated'

    wm = lambda x: np.average(x, weights = df_places.loc[x.index, "Households"])
    df_places = df_places.groupby(['CountyName', 'Geography', 'Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df_places = df_places.sort_values(['CountyName', 'Geography', 'Year'], ascending=[True, True, True]).reset_index(drop=True)

    df_w_counties = df_w_counties[df_w_counties['Race/Ethnicity'] == 'All']
    df_w_counties = df_w_counties[['County Name', 'Year', 'Households']].rename(columns={'County Name':'Geography'})
    df_w_counties['Geography'] = df_w_counties['Geography'] + ' County'

    df_counties = df_counties.rename(columns={'RegionName':'Geography'})
    df_counties = df_counties[df_counties['Geography'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
    df_counties = df_counties.drop(['RegionID', 'SizeRank', 'RegionType', 'StateName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'], axis=1)
    df_counties = df_counties.melt(id_vars=['Geography'], var_name='date_', value_name='ZHVI')
    df_counties['date_'] = pd.to_datetime(df_counties['date_'])
    df_counties['Year'] = df_counties['date_'].dt.year
    df_counties = df_counties.drop('date_', axis=1)

    df_counties = df_counties.merge(df_w_counties, on=['Geography', 'Year'], how='left')
    df_counties = df_counties.dropna(subset=['Households', 'ZHVI']).reset_index(drop=True)
    df_mpo = df_counties.copy()

    wm = lambda x: np.average(x, weights = df_counties.loc[x.index, "Households"])
    df_counties = df_counties.groupby(['Geography', 'Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df_counties = df_counties.sort_values(['Geography', 'Year'], ascending=[True, True]).reset_index(drop=True)

    wm = lambda x: np.average(x, weights = df_mpo.loc[x.index, "Households"])
    df_mpo = df_mpo.groupby(['Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df_mpo = df_mpo.sort_values(['Year'], ascending=[True]).reset_index(drop=True)
    df_mpo['Geography'] = 'SACOG Region'


    counties = list(df_places['CountyName'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography'] == county]

        df_places_sub = df_places[df_places['CountyName'] == county].drop('CountyName', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod = df_prod.pivot_table(index=['Year'], columns='Geography', values='ZHVI').reset_index()
            df_prod = df_prod[['Year', jurisdiction, county, 'SACOG Region']]
            if jurisdiction == 'Sacramento':
                display(df_prod.head())
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

