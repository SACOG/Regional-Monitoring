




import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px
from IPython.display import display


PATH_DATA = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected'
FILE_AREA = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'config' / 'area_codes.xlsx'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'


FILE_ZHVI_CITIES = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / f'City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
FILE_ZHVI_COUNTIES = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / f'County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'

FILE_WEIGHTS_CDP = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Households Places ACS5.xlsx'  
FILE_WEIGHTS_COUNTIES = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Households Counties ACS5.xlsx'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()



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


if __name__ == '__main__':

    indicator = 'RHNA_HSG_8'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']


    ## Importing ---
    df_codes = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')

    df_places   = pd.read_csv(FILE_ZHVI_CITIES)
    df_counties = pd.read_csv(FILE_ZHVI_COUNTIES)

    df_w_cities   = pd.read_excel(FILE_WEIGHTS_CDP)
    df_w_counties = pd.read_excel(FILE_WEIGHTS_COUNTIES)

    df_w_cities   = extrapolate_weights(df_w_cities  )
    df_w_counties = extrapolate_weights(df_w_counties)


    # df_w_cities  ['Households'] = df_w_cities  ['Households'].fillna(0)
    # df_w_counties['Households'] = df_w_counties['Households'].fillna(0)



    ## Organizing ---


    df_codes = df_codes[df_codes['MPO'] == 'SACOG']
    df_codes = df_codes[['NAME', 'Incorporated']].drop_duplicates()
    df_codes['NAME'] = df_codes['NAME'].str.replace(' city', '')
    df_codes['NAME'] = df_codes['NAME'].str.replace(' CDP' , '')
    df_codes['NAME'] = df_codes['NAME'].str.replace(' town', '')
    df_codes = df_codes.rename(columns={'NAME':'RegionName'})
    df_codes = df_codes.reset_index(drop=True)

    df_w_cities = df_w_cities[df_w_cities['Race_Ethnicity'] == 'All']
    df_w_cities = df_w_cities[['NAME', 'Year', 'Households']].rename(columns={'NAME':'RegionName'})



    df_places = df_places[df_places['CountyName'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
    df_places = df_places.drop(['RegionID', 'SizeRank', 'RegionType', 'StateName', 'State', 'Metro'], axis=1)
    df_places = df_places.melt(id_vars=['RegionName', 'CountyName'], var_name='date_', value_name='ZHVI')
    df_places = df_places.merge(df_codes, on='RegionName', how='left')
    df_places['date_'] = pd.to_datetime(df_places['date_'])
    df_places['Year'] = df_places['date_'].dt.year
    df_places = df_places.drop('date_', axis=1)


    df_places = df_places.merge(df_w_cities, on=['RegionName', 'Year'], how='left')
    df_places = df_places[~df_places['Households'].isna()]
    df_places = df_places.dropna(subset=['Households'])
    df_places = df_places.dropna(subset=['ZHVI'])
    df_places = df_places.reset_index(drop=True)

    df_places.loc[df_places['Incorporated'] != 'Yes', 'RegionName'] = 'Unincorporated'

    wm = lambda x: np.average(x, weights = df_places.loc[x.index, "Households"])
    df_places = df_places.groupby(['CountyName', 'RegionName', 'Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df_places = df_places.sort_values(['CountyName', 'RegionName', 'Year'], ascending=[True, True, True])
    df_places = df_places.reset_index(drop=True)



    df_w_counties = df_w_counties[df_w_counties['Race_Ethnicity'] == 'All']
    df_w_counties = df_w_counties[['County Name', 'Year', 'Households']].rename(columns={'County Name':'RegionName'})
    df_w_counties['RegionName'] = df_w_counties['RegionName'] + ' County'


    df_counties = df_counties[df_counties['RegionName'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
    df_counties = df_counties.drop(['RegionID', 'SizeRank', 'RegionType', 'StateName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'], axis=1)
    df_counties = df_counties.melt(id_vars=['RegionName'], var_name='date_', value_name='ZHVI')
    df_counties['date_'] = pd.to_datetime(df_counties['date_'])
    df_counties['Year'] = df_counties['date_'].dt.year
    df_counties = df_counties.drop('date_', axis=1)


    df_counties = df_counties.merge(df_w_counties, on=['RegionName', 'Year'], how='left')
    df_counties = df_counties.dropna(subset=['Households'])
    df_counties = df_counties.dropna(subset=['ZHVI'])
    df_counties = df_counties.reset_index(drop=True)
    df_mpo = df_counties.copy()


    wm = lambda x: np.average(x, weights = df_counties.loc[x.index, "Households"])
    df_counties = df_counties.groupby(['RegionName', 'Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df_counties = df_counties.sort_values(['RegionName', 'Year'], ascending=[True, True]).reset_index(drop=True)

    wm = lambda x: np.average(x, weights = df_mpo.loc[x.index, "Households"])
    df_mpo = df_mpo.groupby(['Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df_mpo = df_mpo.sort_values(['Year'], ascending=[True]).reset_index(drop=True)
    df_mpo['RegionName'] = 'SACOG Region'



    counties = list(df_places['CountyName'].unique())


    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_counties_sub = df_counties.copy()
        df_counties_sub = df_counties_sub[df_counties_sub['RegionName'] == county]

        df_places_sub = df_places.copy()
        df_places_sub = df_places_sub[df_places_sub['CountyName'] == county]
        df_places_sub = df_places_sub.drop('CountyName', axis=1)
        jurisdictions = df_places_sub['RegionName'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            ## Plotting ---

            df_prod = pd.concat([df_places_sub[df_places_sub['RegionName'] == jurisdiction], df_counties_sub, df_mpo])
            df_prod = df_prod.pivot_table(index=['Year'], columns='RegionName', values='ZHVI').reset_index()
            df_prod = df_prod[['Year', jurisdiction, county, 'SACOG Region']]
            if jurisdiction == 'Sacramento':
                display(df_prod.head())
            df_plot = pd.concat([df_places_sub[df_places_sub['RegionName'] == jurisdiction], df_counties_sub, df_mpo])
            
            color_map = {
                    f"{jurisdiction}":"#9DC209",
                    f"{county}":"#1E90FF",
                    "SACOG Region":"#1F45FC"
            }

            fig = px.line(df_plot, x='Year', y='ZHVI'
                        , color='RegionName'
                        , color_discrete_map=color_map
                        , markers=True)
            
            fig.update_traces(hovertemplate="%{y}")
                

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)

