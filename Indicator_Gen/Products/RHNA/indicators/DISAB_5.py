

import pandas as pd
import geopandas as gpd
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


FILE_ZIPCODES = PATH_DATA / 'ZIPCodes_Jan2022.xlsx'
FILE_WEIGHTS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Population Places ACS5_Unincorporated.xlsx'

PATH_GDB = Path(r"I:\Projects\Josh\Geospatial Data\aa_ArcPro\GeospatialData_V2.gdb")
FC_ZCTA = 'GISOWNER_ZCTA_2020'
FC_JURISDICTIONS = 'GISOWNER_CityCounty'


if __name__ == '__main__':

    gdf_zip = gpd.read_file(PATH_GDB, layer=FC_ZCTA)
    gdf_cc  = gpd.read_file(PATH_GDB, layer=FC_JURISDICTIONS)
    df_cdds = pd.read_excel(FILE_ZIPCODES, skiprows=7, sheet_name='ResZip')

    gdf_zip = gdf_zip[['GEOID20', 'geometry']].rename(columns={'GEOID20':'ZIP'})
    gdf_int = gpd.overlay(gdf_cc, gdf_zip, how='intersection')
    df_cdds = df_cdds[df_cdds['ZIP'].isin(gdf_int.ZIP.unique())].reset_index(drop=True)
    df_cdds = df_cdds.merge(gdf_int[['COUNTY', 'JURIS', 'ZIP']], on='ZIP', how='left')
    df_cdds = df_cdds.drop('ZIP', axis=1)

    df_cdds = df_cdds.melt(id_vars=['COUNTY', 'JURIS'], var_name='Residence Type', value_name='Population')
    df_cdds['Population'] = df_cdds['Population'].str.replace(' ', '')
    df_cdds['Population'] = df_cdds['Population'].str.replace('>', '')
    df_cdds['Population'] = df_cdds['Population'].str.replace('<', '')
    df_cdds['Population'] = df_cdds['Population'].astype(int)

    df_cdds = df_cdds.groupby(['COUNTY', 'JURIS', 'Residence Type'], as_index=False)['Population'].sum()
    df_cdds.loc[df_cdds['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

    df_w = pd.read_excel(FILE_WEIGHTS)
    df_w = df_w[(df_w['Race_Ethnicity'] == 'All') & (df_w['Year'] == 2023)].reset_index(drop=True)
    df_w = df_w[['County Name', 'NAME', 'Population']].rename(columns={'County Name':'COUNTY', 'NAME':'JURIS', 'Population':'Total Population'})

    df_cdds = df_cdds.merge(df_w, on=['COUNTY', 'JURIS'], how='left')

    df_cdds['Percent'] = df_cdds['Population'] / df_cdds['Total Population']
    df_cdds = df_cdds[df_cdds['Residence Type'] != 'Total Res']
    df_cdds = df_cdds.sort_values(['COUNTY', 'JURIS', 'Percent'], ascending=[True, True, False]).reset_index(drop=True)


    counties = list(df_cdds['COUNTY'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_places_sub = df_cdds[df_cdds['COUNTY'] == county].drop('COUNTY', axis=1)
        jurisdictions = df_places_sub['JURIS'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)
            df_prod = df_places_sub[df_places_sub['JURIS'] == jurisdiction]
            df_prod = df_prod[['Residence Type', 'Population']]
            df_plot = df_prod.copy()

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

