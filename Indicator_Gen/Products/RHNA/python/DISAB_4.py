

import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

FILE_ZIPCODES = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / 'ZIPCodes_Jan2022.xlsx'
FILE_WEIGHTS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Population Places ACS5_Unincorporated.xlsx'

PATH_GDB = Path(r"I:\Projects\Josh\Geospatial Data\aa_ArcPro\GeospatialData_V2.gdb")
FC_ZCTA = 'GISOWNER_ZCTA_2020'
FC_JURISDICTIONS = 'GISOWNER_CityCounty'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()




if __name__ == '__main__':

    indicator = 'RHNA_DISAB_4'
    title = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]


    ## Organizing

    gdf_zip = gpd.read_file(PATH_GDB, layer=FC_ZCTA)
    gdf_cc  = gpd.read_file(PATH_GDB, layer=FC_JURISDICTIONS)

    df_cdds = pd.read_excel(FILE_ZIPCODES, skiprows=7, sheet_name='AgeZip')



    gdf_zip = gdf_zip[['GEOID20', 'geometry']].rename(columns={'GEOID20':'ZIP'})
    gdf_int = gpd.overlay(gdf_cc, gdf_zip, how='intersection')


    df_cdds = df_cdds[df_cdds['ZIP'].isin(gdf_int.ZIP.unique())]

    df_cdds = df_cdds.reset_index(drop=True)


    df_cdds = df_cdds.merge(gdf_int[['COUNTY', 'JURIS', 'ZIP']], on='ZIP', how='left')
    df_cdds = df_cdds.drop('ZIP', axis=1)


    df_cdds = df_cdds.melt(id_vars=['COUNTY', 'JURIS'], var_name='Age Group', value_name='Population with Disabilities')
    df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].str.replace(' ', '')
    df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].str.replace('>', '')
    df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].str.replace('<', '')
    df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].astype(int)

    df_cdds = df_cdds.groupby(['COUNTY', 'JURIS', 'Age Group'], as_index=False)['Population with Disabilities'].sum()
    df_cdds.loc[df_cdds['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

    df_w = pd.read_excel(FILE_WEIGHTS)
    df_w = df_w[df_w['Race_Ethnicity'] == 'All']
    df_w = df_w[df_w['Year'] == 2023]
    df_w = df_w[['County Name', 'NAME', 'Population']].rename(columns={'County Name':'COUNTY', 'NAME':'JURIS'})
    df_w = df_w.reset_index(drop=True)

    df_cdds = df_cdds.merge(df_w, on=['COUNTY', 'JURIS'], how='left')

    df_cdds['Percentage'] = df_cdds['Population with Disabilities'] / df_cdds['Population']
    df_cdds = df_cdds[df_cdds['Age Group'] != 'Total Age']

    conditions = [df_cdds['Age Group'] == '00-17 yrs', df_cdds['Age Group'] == '18+ yrs']
    choices = ['Under 18', '18+']
    df_cdds['Age Group'] = np.select(conditions, choices, default='No')


    df_cdds = df_cdds.reset_index(drop=True)


    counties = list(df_cdds['COUNTY'].unique())
    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_cdds.copy()
        df_places_sub = df_places_sub[df_places_sub['COUNTY'] == county]
        df_places_sub = df_places_sub.drop('COUNTY', axis=1)
        jurisdictions = df_places_sub['JURIS'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            ## Plotting

            df_prod = df_places_sub[df_places_sub['JURIS'] == jurisdiction]
            df_prod = df_prod[['Age Group', 'Population with Disabilities']]
            df_plot = df_prod.copy()

            fig = px.bar(df_plot, x='Age Group', y='Population with Disabilities')
            fig.update_traces(marker_color='#1E90FF')
            fig.update_traces(hovertemplate="%{y}")
                
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)

