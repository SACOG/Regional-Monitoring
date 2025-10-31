


import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
from IPython.display import display
import plotly.express as px



PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

PATH_GEO = Path(r'I:\Projects\Josh\Geospatial Data')
FILE_TRACTS = PATH_GEO / 'GISOWNER' / 'T2020_Census_Tracts_SACOG_Region' / 'T2020_Census_Tracts_SACOG_Region.shp'
FILE_JURISDICTIONS = PATH_GEO / 'GISOWNER' / 'CityCounty' / 'CityCounty.shp'

PATH_RHNA_GEO = Path(r'I:\Projects\Josh\RHNA\Geospatial Data')
FILE_IN = PATH_RHNA_GEO / 'draft-2024-opportunity-maps-shapefile' / 'final_opp_2024_public.gpkg'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()




if __name__ == '__main__':

    indicator = 'RHNA_AFFH_2'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Population'
    columns = 'Race_Ethnicity'


    if __name__ == '__main__':

        gdf_tcac = gpd.read_file(FILE_IN)
        gdf_tcac = gdf_tcac[gdf_tcac['county_name'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yuba', 'Yolo'])].reset_index(drop=True)
        df_tcac = gdf_tcac[['county_name', 'fips', 'oppcat']]
        display(df_tcac.head())

        df_acs = pd.read_excel(Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / f'{indicator} Tracts ACS5.xlsx')
        df_acs['state' ] = df_acs['State FIPS' ].astype(str).apply('{:0>2}'.format)
        df_acs['county'] = df_acs['County FIPS'].astype(str).apply('{:0>3}'.format)
        df_acs['tract' ] = df_acs['Tract ID'   ].astype(str).apply('{:0>6}'.format)
        df_acs['fips'  ] = df_acs['state'] + df_acs['county'] + df_acs['tract']
        df_acs = df_acs[df_acs[columns] != 'All']

        df_acs = df_acs[['fips', columns, values]]
        display(df_acs.head())


        df_tcac = df_tcac.merge(df_acs, on='fips', how='left')

        ## Read in opportunity map tract data
        ## Read in ACS population tract data
        ## Read in crosswalk from tracts to jurisdictions

        gdf_ct  = gpd.read_file(FILE_TRACTS).to_crs("EPSG:2226")
        gdf_cdp = gpd.read_file(FILE_JURISDICTIONS).to_crs("EPSG:2226")
        gdf_int = gpd.overlay(gdf_ct, gdf_cdp, how='intersection')
        gdf_int = gdf_int[
            ((gdf_int['COUNTY_2'] ==  'El Dorado') & (gdf_int['COUNTY_1'] ==  17.0)) |
            ((gdf_int['COUNTY_2'] ==     'Placer') & (gdf_int['COUNTY_1'] ==  61.0)) |
            ((gdf_int['COUNTY_2'] == 'Sacramento') & (gdf_int['COUNTY_1'] ==  67.0)) |
            ((gdf_int['COUNTY_2'] ==     'Sutter') & (gdf_int['COUNTY_1'] == 101.0)) |
            ((gdf_int['COUNTY_2'] ==       'Yolo') & (gdf_int['COUNTY_1'] == 113.0)) |
            ((gdf_int['COUNTY_2'] ==       'Yuba') & (gdf_int['COUNTY_1'] == 115.0))
            ]


        gdf_int['COUNTY_1'] = gdf_int['COUNTY_1'].astype(str).str[:-2].apply('{:0>3}'.format)
        gdf_int['TRACT'   ] = gdf_int['TRACT'   ].astype(str).str[:-2].apply('{:0>6}'.format)
        gdf_int['fips'] = '06' + gdf_int['COUNTY_1'] + gdf_int['TRACT']
        gdf_int = gdf_int[['fips', 'JURIS']]
        gdf_int = gdf_int.reset_index(drop=True)


        gdf_int['fips'] = gdf_int['fips'].str[1:].astype('int64')
        df_tcac['fips'] = df_tcac['fips'].str[1:].astype('int64')


        df_tcac = df_tcac.merge(gdf_int, on='fips', how='left')

        df_tcac.loc[df_tcac['JURIS' ].str.contains('County'), 'JURIS' ] = 'Unincorporated'
        df_tcac.loc[df_tcac['oppcat'].isna(), 'oppcat'] = 'Unknown'
        df_tcac.loc[df_tcac['oppcat'].str.contains('High'  ), 'oppcat'] = 'High/Highest Resource'


        df_tcac = df_tcac.groupby(['county_name', 'JURIS', columns, 'oppcat'], as_index=False).agg(Population=(values, 'sum'))

        df_tcac['Percentage'] = df_tcac[values] / df_tcac.groupby(['county_name', 'JURIS', 'oppcat'])[values].transform('sum')
        df_tcac['sort'] = pd.Categorical(df_tcac['oppcat'], [
            'Low Resource'
            , 'Moderate Resource'
            , 'High/Highest Resource'
            , 'Unknown'
        ])
        df_tcac = df_tcac.sort_values(['county_name', 'JURIS', columns, 'sort'], ascending=[True, True, False, True])
        df_tcac = df_tcac.drop('sort', axis=1)
        df_tcac = df_tcac.reset_index(drop=True)


        counties = list(df_tcac['county_name'].unique())


        for county in counties:

            rhna.print2()
            print(county)

            df_sub = df_tcac[df_tcac['county_name'] == county]
            jurisdictions = list(df_sub['JURIS'].unique())

            for jurisdiction in tqdm(jurisdictions, position=0):

                tqdm.write(jurisdiction)

                df_sub_juris = df_sub[df_sub['JURIS'] == jurisdiction]

                ## Plotting

                df_plot = df_sub_juris.copy()

                df_prod = df_sub_juris[[columns, 'oppcat', values]]
                df_prod = df_prod.pivot_table(index='oppcat', columns=columns, values=values).reset_index()

                df_pct  = df_sub_juris[[columns, 'oppcat', 'Percentage']]
                df_pct = df_pct.pivot_table(index='oppcat', columns=columns, values='Percentage').reset_index()

                df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
                df_sort = pd.DataFrame({'oppcat': ['Low Resource', 'Moderate Resource', 'High/Highest Resource', 'Unknown'], 'Sort': [1, 2, 3, 4]})
                df_plot = df_plot.merge(df_sort, on='oppcat', how='left')

                df_plot['Sort_eth'] = pd.Categorical(df_plot[columns], [
                    'American Indian or Alaska Native (NH)'
                    , 'Native Hawaiian or other Pacific Islander (NH)'
                    , 'Other race or multiple races (NH)'
                    , 'Black or African American (NH)'
                    , 'Asian (NH)'
                    , 'Hispanic or Latino'
                    , 'White (NH)'
                ])

                df_plot = df_plot.sort_values(['Sort', 'Sort_eth'], ascending=[True, False])
                df_plot = df_plot.drop(['Sort', 'Sort_eth'], axis=1)
                    
                color_map  = {
                    'American Indian or Alaska Native (NH)': '#E56717'
                    , 'Native Hawaiian or other Pacific Islander (NH)': '#006A4E'
                    , 'Other race or multiple races (NH)': '#7E587E'
                    , 'Black or African American (NH)': '#FBB117'
                    , 'Asian (NH)': '#9DC209'
                    , 'Hispanic or Latino': '#1E90FF'
                    , 'White (NH)': '#1F45FC'
                }
            
                fig = px.bar(df_plot, x='oppcat', y='Percentage'
                            , color = columns
                            , color_discrete_map=color_map)
                
                fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
                fig.update_layout(legend={'traceorder': 'reversed'})
                fig.update_traces(hovertemplate="%{y}")
            
                rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
                rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)


