

indicator = 'RHNA_DISAB_5'


# Set indicator
source = 'DDS'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]


## Importing ---

path_gdb = Path(r"I:\Projects\Josh\Geospatial Data\aa_ArcPro\GeospatialData_V2.gdb")

fc_zip = 'GISOWNER_ZCTA_2020'
fc_cc  = 'GISOWNER_CityCounty'

gdf_zip = gpd.read_file(path_gdb, layer=fc_zip)
gdf_cc  = gpd.read_file(path_gdb, layer=fc_cc )


file_in = path_raw / 'ZIPCodes_Jan2022.xlsx'
df_cdds = pd.read_excel(file_in, skiprows=7, sheet_name='ResZip')


## Organizing ---


gdf_zip = gdf_zip[['GEOID20', 'geometry']].rename(columns={'GEOID20':'ZIP'})
gdf_int = gpd.overlay(gdf_cc, gdf_zip, how='intersection')


df_cdds = df_cdds[df_cdds['ZIP'].isin(gdf_int.ZIP.unique())]



df_cdds = df_cdds.reset_index(drop=True)


df_cdds = df_cdds.merge(gdf_int[['COUNTY', 'JURIS', 'ZIP']], on='ZIP', how='left')
df_cdds = df_cdds.drop('ZIP', axis=1)


df_cdds = df_cdds.melt(id_vars=['COUNTY', 'JURIS'], var_name='Residence Type', value_name='Population with Disabilities')


df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].str.replace(' ', '')
df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].str.replace('>', '')
df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].str.replace('<', '')
df_cdds['Population with Disabilities'] = df_cdds['Population with Disabilities'].astype(int)

df_cdds = df_cdds.groupby(['COUNTY', 'JURIS', 'Residence Type'], as_index=False)['Population with Disabilities'].sum()
df_cdds.loc[df_cdds['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

df_cdds['Residence Type'].unique()

file_w = path_sp / 'Data' / 'Reference' / 'Weights' / 'Total_Population Places ACS5_Unincorporated.xlsx'
df_w = pd.read_excel(file_w)
df_w = df_w[df_w['Race_Ethnicity'] == 'All']
df_w = df_w[df_w['Year'] == 2023]
df_w = df_w[['County Name', 'NAME', 'Population']].rename(columns={'County Name':'COUNTY', 'NAME':'JURIS'})
df_w = df_w.reset_index(drop=True)

df_cdds = df_cdds.merge(df_w, on=['COUNTY', 'JURIS'], how='left')

df_cdds['Percentage'] = df_cdds['Population with Disabilities'] / df_cdds['Population']
df_cdds = df_cdds[df_cdds['Residence Type'] != 'Total Res']


df_cdds['Sort'] = pd.Categorical(df_cdds['Residence Type'], [
    'Home of Parent /Family /Guardian', 'Community Care Facility', 'Independent /Supported Living', 'Foster /Family Home', 'Intermediate Care Facility', 'Other'
])
df_cdds = df_cdds.sort_values(['COUNTY', 'JURIS', 'Sort'], ascending=[True, True, True])
df_cdds = df_cdds.drop('Sort', axis=1)
df_cdds = df_cdds.reset_index(drop=True)

counties = list(df_cdds['COUNTY'].unique())



for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_places_sub = df_cdds.copy()
    df_places_sub = df_places_sub[df_places_sub['COUNTY'] == county]
    df_places_sub = df_places_sub.drop('COUNTY', axis=1)
    jurisdictions = df_places_sub['JURIS'].unique()
    
    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        ## Plotting ---

        df_prod = df_places_sub[df_places_sub['JURIS'] == jurisdiction]
        df_prod = df_prod[['Residence Type', 'Population with Disabilities']]
        df_plot = df_prod.copy()

        fig = px.bar(df_plot, x='Residence Type', y='Population with Disabilities')
        fig.update_traces(marker_color='#1E90FF')
        fig.update_traces(hovertemplate="%{y}")
            
        path_plots = path_out / county / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        if export:
            export_rhna(df_prod)

list_indicators.append(indicator)

