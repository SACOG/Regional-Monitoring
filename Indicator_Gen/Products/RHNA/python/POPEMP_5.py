

indicator = 'RHNA_POPEMP_5'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Population'
columns = 'Variable'


## Importing ---

df_places, df_counties, df_mpo = import_rhna(path_raw, indicator)


## Organizing ---

df_places, df_counties, df_mpo = clean_rhna(df_places, df_counties, df_mpo, path_config0, columns, values)


counties = df_counties['Geography'].unique()

for county in counties:

    print();print()
    print(county)
    time.sleep(2)

    df_places_sub, df_counties_sub = sub_rhna(df_places, df_counties, county)
    jurisdictions = df_places_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions, position=0):
        
        tqdm.write(jurisdiction)
                
        df_prod, df_pct = pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
        df_prod = df_prod[['Abroad', 'Elsewhere in U.S.', 'Elsewhere in CA', 'Same County', 'Same city or town', 'Same house']] # this reordering is new but should work
        df_pct  = df_pct [['Abroad', 'Elsewhere in U.S.', 'Elsewhere in CA', 'Same County', 'Same city or town', 'Same house']]

    
        ## Plotting ---
        
        df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_plot = df_plot.drop(values, axis=1)
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            
        color_map  = {
            'Same house': '#1E90FF'
            , 'Same city or town': '#1F45FC'
            , 'Same county': '#9DC209'
            , 'Elsewhere in CA': '#7E587E'
            , 'Elsewhere in U.S.': '#FBB117'
            , 'Abroad': '#DC381F'
        }
    
        fig = px.bar(df_plot, x='Geography', y='Percentage'
                     , color = columns
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

