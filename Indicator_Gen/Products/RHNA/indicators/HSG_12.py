

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from IPython.display import display
import warnings; warnings.filterwarnings('ignore')

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


def clean_zhvi(df, df_codes, df_w):

    df_w = extrapolate_weights(df_w)
    df_w = df_w[df_w['Race/Ethnicity'] == 'All'][['NAME', 'Year', 'Households']].rename(columns={'NAME':'Jurisdiction'})

    df_codes = df_codes[df_codes['MPO'] == 'SACOG'][['NAME', 'Incorporated']].drop_duplicates().rename(columns={'NAME':'Jurisdiction'}).reset_index(drop=True)
    df_codes['Jurisdiction'] = df_codes['Jurisdiction'].str.replace(' city', '')
    df_codes['Jurisdiction'] = df_codes['Jurisdiction'].str.replace(' CDP' , '')
    df_codes['Jurisdiction'] = df_codes['Jurisdiction'].str.replace(' town', '')

    df = df.rename(columns={'RegionName':'Jurisdiction'})
    df = df[df['CountyName'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
    df = df.drop(['RegionID', 'SizeRank', 'RegionType', 'StateName', 'State', 'Metro'], axis=1)
    df = df.melt(id_vars=['Jurisdiction', 'CountyName'], var_name='date_', value_name='ZHVI')
    df = df.merge(df_codes, on='Jurisdiction', how='left')
    df['date_'] = pd.to_datetime(df['date_'])
    df['Year'] = df['date_'].dt.year
    df = df.drop('date_', axis=1)

    df = df.merge(df_w, on=['Jurisdiction', 'Year'], how='left')
    df = df.dropna(subset=['Households', 'ZHVI']).reset_index(drop=True)
    df.loc[df['Incorporated'] != 'Yes', 'Jurisdiction'] = 'Unincorporated'

    wm = lambda x: np.average(x, weights = df.loc[x.index, "Households"])
    df = df.groupby(['CountyName', 'Jurisdiction', 'Year'], as_index=False).agg(ZHVI=('ZHVI', wm))
    df = df.sort_values(['CountyName', 'Jurisdiction', 'Year'], ascending=[True, True, True]).reset_index(drop=True)
    
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

FILE_WEIGHTS_CDP = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Households Places ACS5.xlsx'  


if __name__ == '__main__':

    df_codes = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
    df_w = pd.read_excel(FILE_WEIGHTS_CDP)

    df_1_bed = pd.read_csv(PATH_DATA / 'City_zhvi_bdrmcnt_1_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
    df_2_bed = pd.read_csv(PATH_DATA / 'City_zhvi_bdrmcnt_2_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
    df_3_bed = pd.read_csv(PATH_DATA / 'City_zhvi_bdrmcnt_3_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
    df_4_bed = pd.read_csv(PATH_DATA / 'City_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
    df_5_bed = pd.read_csv(PATH_DATA / 'City_zhvi_bdrmcnt_5_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')

    df_1_bed = clean_zhvi(df_1_bed, df_codes, df_w); df_1_bed['Unit Size'] = '1 bedroom'
    df_2_bed = clean_zhvi(df_2_bed, df_codes, df_w); df_2_bed['Unit Size'] = '2 bedrooms'
    df_3_bed = clean_zhvi(df_3_bed, df_codes, df_w); df_3_bed['Unit Size'] = '3 bedrooms'
    df_4_bed = clean_zhvi(df_4_bed, df_codes, df_w); df_4_bed['Unit Size'] = '4 bedrooms'
    df_5_bed = clean_zhvi(df_5_bed, df_codes, df_w); df_5_bed['Unit Size'] = '5+ bedrooms'

    df_zhvi = pd.concat([df_1_bed, df_2_bed, df_3_bed, df_4_bed, df_5_bed])


    counties = list(df_zhvi['CountyName'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_zhvi_sub = df_zhvi[df_zhvi['CountyName'] == county].drop('CountyName', axis=1)
        jurisdictions = df_zhvi_sub['Jurisdiction'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_zhvi_sub[df_zhvi_sub['Jurisdiction'] == jurisdiction].pivot_table(index=['Year'], columns='Unit Size', values='ZHVI').reset_index()
            if jurisdiction == 'Sacramento':
                display(df_prod.head())
            df_plot = df_zhvi_sub[df_zhvi_sub['Jurisdiction'] == jurisdiction]

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

