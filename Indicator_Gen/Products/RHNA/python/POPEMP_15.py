


indicator = 'RHNA_POPEMP_15'


# Set indicator
source = 'EDD'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]


## Importing ---

file_area = path_config0 / 'area_codes.xlsx'
df_codes = pd.read_excel(file_area, sheet_name='CDPcodes')
df_codes = df_codes[df_codes['MPO'] == 'SACOG']
df_codes = df_codes[['NAME', 'MPO', 'County Name', 'Incorporated']].drop_duplicates()
df_codes = df_codes.rename(columns={'NAME':'Area Name'})
df_codes = df_codes.reset_index(drop=True)


file_in = path_raw / f'laborforceandunemployment_monthly_2025422.csv'
df_places   = pd.read_csv(file_in)
df_counties = pd.read_csv(file_in)


## Organizing ---


df_places = df_places.merge(df_codes, on='Area Name', how='left')
df_places = df_places[df_places['MPO'] == 'SACOG']
df_places.loc[df_places['Incorporated'] != 'Yes', 'Area Name'] = 'Unincorporated'
df_places['Area Name'] = df_places['Area Name'].str.replace(' city', '')

wm = lambda x: np.average(x, weights = df_places.loc[x.index, "Labor Force"])
df_places = df_places.groupby(['County Name', 'Area Name', 'Year'], as_index=False).agg(unemployment_rate=('Unemployment Rate', wm))
df_places['County Name'] = df_places['County Name'] + ' County' 


df_counties = df_counties[df_counties['Area Name'].isin(['El Dorado County', 'Placer County', 'Sacramento County', 'Sutter County', 'Yolo County', 'Yuba County'])]
df_counties = df_counties[df_counties['Year'] >= 2010]
df_mpo = df_counties.copy()

wm = lambda x: np.average(x, weights = df_counties.loc[x.index, "Labor Force"])
df_counties = df_counties.groupby(['Area Name', 'Year'], as_index=False).agg(unemployment_rate=('Unemployment Rate', wm))

wm = lambda x: np.average(x, weights = df_mpo.loc[x.index, "Labor Force"])
df_mpo = df_mpo.groupby(['Year'], as_index=False).agg(unemployment_rate=('Unemployment Rate', wm))
df_mpo['Area Name'] = 'SACOG Region'



counties = list(df_places['County Name'].unique())


for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_counties_sub = df_counties.copy()
    df_counties_sub = df_counties_sub[df_counties_sub['Area Name'] == county]

    df_places_sub = df_places.copy()
    df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
    df_places_sub = df_places_sub.drop('County Name', axis=1)
    jurisdictions = df_places_sub['Area Name'].unique()
    
    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        ## Plotting ---

        df_prod = pd.concat([df_places_sub[df_places_sub['Area Name'] == jurisdiction], df_counties_sub, df_mpo])
        df_prod['unemployment_rate'] = df_prod['unemployment_rate']/100
        df_prod = df_prod.pivot_table(index=['Year'], columns='Area Name', values='unemployment_rate').reset_index()
        df_prod = df_prod[['Year', jurisdiction, county, 'SACOG Region']]
        if jurisdiction == 'Sacramento':
            display(df_prod.head())
        df_plot = pd.concat([df_places_sub[df_places_sub['Area Name'] == jurisdiction], df_counties_sub, df_mpo])
        
        color_map = {
                f"{jurisdiction}":"#9DC209",
                f"{county}":"#1E90FF",
                "SACOG Region":"#1F45FC"
        }

        fig = px.line(df_plot, x='Year', y='unemployment_rate'
                     , color='Area Name'
                     , color_discrete_map=color_map
                     , markers=True)
        
        fig.update_yaxes(ticksuffix='%')
        fig.update_traces(hovertemplate="%{y}")
            
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        if export:
            export_rhna(df_prod)

list_indicators.append(indicator)

