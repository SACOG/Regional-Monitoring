

indicator = 'RHNA_OVER_3'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Race_Ethnicity'


## Importing ---

df_places, df_counties, df_mpo = import_rhna(path_raw, indicator)


## Organizing ---

df_places   = df_places  [df_places  ['Race_Ethnicity'] != 'All']
df_counties = df_counties[df_counties['Race_Ethnicity'] != 'All']
df_mpo      = df_mpo     [df_mpo     ['Race_Ethnicity'] != 'All']

df_places   = df_places  [df_places  ['Variable'] == 'More than occupant per room']
df_counties = df_counties[df_counties['Variable'] == 'More than occupant per room']
df_mpo      = df_mpo     [df_mpo     ['Variable'] == 'More than occupant per room']

df_places, df_counties, df_mpo = clean_rhna(df_places, df_counties, df_mpo, path_config0, columns, values)


counties = df_counties['Geography'].unique()

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_places_sub, df_counties_sub = sub_rhna(df_places, df_counties, county)
    jurisdictions = df_places_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions):
                
        df_prod, df_pct = pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
        
        ## Plotting ---
        
        # df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction].copy()
        df_plot = df_plot.drop('Households', axis=1)
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        df_plot['Sort'] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG'])
        df_plot['Sort_eth'] = pd.Categorical(df_plot['Race_Ethnicity'], [
            'American Indian or Alaska Native (NH)'
            , 'Native Hawaiian or other Pacific Islander (NH)'
            , 'Some other race (NH)'
            , 'Two or more races (NH)'
            , 'Black or African American (NH)'
            , 'Asian (NH)'
            , 'Hispanic or Latino'
            , 'White (NH)'
        ])
        df_plot = df_plot.sort_values(['Sort', 'Sort_eth'], ascending=[True, True])
        df_plot = df_plot.drop(['Sort', 'Sort_eth'], axis=1)
        df_plot = df_plot.reset_index(drop=True)
            
        color_map  = {
            'American Indian or Alaska Native (NH)': '#A97142'
            , 'Native Hawaiian or other Pacific Islander (NH)': '#006A4E'
            , 'Some other race (NH)': '#7E587E'
            , 'Two or more races (NH)': '#1F45FC'
            , 'Asian (NH)': '#9DC209'
            , 'Black or African American (NH)': '#1E90FF'
            , 'Hispanic or Latino': '#FBB117'
            , 'White (NH)': '#DC381F'
        }
    
        fig = px.bar(
            df_plot
            , x=columns
            , y='Percentage'
            , color=columns
            # , facet_col='Geography'
            , color_discrete_map=color_map
            # , barmode='group'
        )
        
        # title = f'<b>{plot_title}</b>'
        # fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
        fig.update_yaxes(ticksuffix='%')
        # fig.update_layout(legend={'traceorder': 'reversed'})
        fig.update_traces(hovertemplate="%{y}")
        fig.update_layout(xaxis={'showticklabels': False})
        fig.update_layout(bargap=0, bargroupgap=0)

        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            
            export_rhna(df_prod, df_pct)
            

list_indicators.append(indicator)

