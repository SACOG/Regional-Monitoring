


indicator = 'RHNA_AFFH_2'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]


path_in = Path(r'I:\Projects\Josh\RHNA\Geospatial Data\draft-2024-opportunity-maps-shapefile')
file_in = path_in / 'final_opp_2024_public.gpkg'
gdf_tcac = gpd.read_file(file_in)
gdf_tcac = gdf_tcac[gdf_tcac['county_name'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yuba', 'Yolo'])]

df_tcac = gdf_tcac[['county_name', 'fips', 'oppcat']]

display(df_tcac.head())

file_in = path_raw / f'{indicator} Tracts ACS5.xlsx'
df_acs = pd.read_excel(file_in)
df_acs['state' ] = df_acs['State FIPS' ].astype(str).apply('{:0>2}'.format)
df_acs['county'] = df_acs['County FIPS'].astype(str).apply('{:0>3}'.format)
df_acs['tract' ] = df_acs['Tract ID'   ].astype(str).apply('{:0>6}'.format)
df_acs['fips'  ] = df_acs['state'] + df_acs['county'] + df_acs['tract']
df_acs = df_acs[df_acs['Race_Ethnicity'] != 'All']
df_acs = df_acs[['fips', 'Race_Ethnicity', 'Population']]
display(df_acs.head())


df_tcac = df_tcac.merge(df_acs, on='fips', how='left')


## Read in opportunity map tract data
## Read in ACS population tract data
## Read in crosswalk from tracts to jurisdictions


path_geo = Path(r'I:\Projects\Josh\Geospatial Data')

file_tracts = path_geo / 'GISOWNER' / 'T2020_Census_Tracts_SACOG_Region' / 'T2020_Census_Tracts_SACOG_Region.shp'
gdf_ct = gpd.read_file(file_tracts)
gdf_ct = gdf_ct.to_crs("EPSG:2226")


file_cdp = path_geo / 'GISOWNER' / 'CityCounty' / 'CityCounty.shp'
gdf_cdp = gpd.read_file(file_cdp)
gdf_cdp = gdf_cdp.to_crs("EPSG:2226")

gdf_int = gpd.overlay(gdf_ct, gdf_cdp, how='intersection')

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


df_tcac = df_tcac.groupby(['county_name', 'JURIS', 'Race_Ethnicity', 'oppcat'], as_index=False).agg(Population=('Population', 'sum'))

df_tcac['Percentage'] = df_tcac['Population'] / df_tcac.groupby(['county_name', 'JURIS', 'oppcat'])['Population'].transform('sum')
df_tcac['sort'] = pd.Categorical(df_tcac['oppcat'], [
    'Low Resource'
    , 'Moderate Resource'
    , 'High/Highest Resource'
    , 'Unknown'
])
df_tcac = df_tcac.sort_values(['county_name', 'JURIS', 'Race_Ethnicity', 'sort'], ascending=[True, True, False, True])
df_tcac = df_tcac.drop('sort', axis=1)
df_tcac = df_tcac.reset_index(drop=True)


counties = list(df_tcac['county_name'].unique())


for county in counties:

    print(); print()
    print(county)

    path_county = path_out / county
    df_sub = df_tcac[df_tcac['county_name'] == county]
    jurisdictions = list(df_sub['JURIS'].unique())

    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        df_sub_juris = df_sub[df_sub['JURIS'] == jurisdiction]

        ## Plotting ---

        df_plot = df_sub_juris.copy()

        df_prod = df_sub_juris[['Race_Ethnicity', 'oppcat', 'Population']]
        df_prod = df_prod.pivot_table(index='oppcat', columns='Race_Ethnicity', values='Population').reset_index()

        df_pct  = df_sub_juris[['Race_Ethnicity', 'oppcat', 'Percentage']]
        df_pct = df_pct.pivot_table(index='oppcat', columns='Race_Ethnicity', values='Percentage').reset_index()

        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        df_sort = pd.DataFrame({'oppcat': ['Low Resource', 'Moderate Resource', 'High/Highest Resource', 'Unknown'], 'Sort': [1, 2, 3, 4]})
        df_plot = df_plot.merge(df_sort, on='oppcat', how='left')

        df_plot['Sort_eth'] = pd.Categorical(df_plot['Race_Ethnicity'], [
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
                     , color = 'Race_Ethnicity'
                     , color_discrete_map=color_map)
        
        fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
        fig.update_layout(legend={'traceorder': 'reversed'})
        fig.update_traces(hovertemplate="%{y}")
    
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)

        ## Exporting ---
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)

