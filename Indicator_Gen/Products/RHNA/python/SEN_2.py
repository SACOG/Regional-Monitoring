


indicator = 'RHNA_SEN_2'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Population'
columns = 'Race_Ethnicity'


## Importing ---

df_places = pd.read_excel(os.path.join(path_raw, f'{indicator} Places ACS5.xlsx'))


## Organizing ---

df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
df_places = df_places.rename(columns={'NAME':'Geography'})
df_places = df_places[df_places['Year'] == df_places['Year'].max()]
df_places = df_places.reset_index(drop=True)

df_places = df_places[['County Name', 'Geography', values, columns, 'Variable', 'Percentage']]

df_places['Sort'] = pd.Categorical(df_places['Variable'], ['Age 0-17', 'Age 18-64', 'Age 65+'])
df_places['Sort_eth'] = pd.Categorical(df_places['Race_Ethnicity'], [
    'American Indian or Alaska Native'
    , 'Asian'
    , 'Black or African American'
    , 'Hispanic or Latino'
    , 'Native Hawaiian or other Pacific Islander'
    , 'Some other race'
    , 'Two or more races'
    , 'White (NH)'
])
df_places = df_places.sort_values(['County Name', 'Geography', 'Sort_eth', 'Sort'], ascending=[True, True, False, True])
df_places = df_places.drop(['Sort', 'Sort_eth'], axis = 1)

df_places['Percentage'] = df_places['Population'] / df_places.groupby(['County Name', 'Geography', 'Variable'])['Population'].transform('sum')

df_places = df_places.reset_index(drop=True)


counties = list(df_places['County Name'].unique())

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_places_sub = df_places.copy()
    df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
    jurisdictions = df_places_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        df_prod, df_pct = pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values)

        ## Plotting ---

        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)

        df_plot['Sort_eth'] = pd.Categorical(df_plot['Race_Ethnicity'], [
            'American Indian or Alaska Native'
            , 'Native Hawaiian or other Pacific Islander'
            , 'Other race or multiple races'
            , 'Black or African American'
            , 'Asian'
            , 'Hispanic or Latino'
            , 'White (NH)'
        ])
        df_plot = df_plot.sort_values(['Variable', 'Sort_eth'], ascending=[True, False])
        df_plot = df_plot.drop(['Sort_eth'], axis=1)
            
        color_map  = {
            'American Indian or Alaska Native': '#E56717'
            , 'Native Hawaiian or other Pacific Islander': '#006A4E'
            , 'Other race or multiple races': '#7E587E'
            , 'Black or African American': '#FBB117'
            , 'Asian': '#9DC209'
            , 'Hispanic or Latino': '#1E90FF'
            , 'White (NH)': '#1F45FC'
        }

        fig = px.bar(df_plot, x='Variable', y='Percentage'
                     , color=columns
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

