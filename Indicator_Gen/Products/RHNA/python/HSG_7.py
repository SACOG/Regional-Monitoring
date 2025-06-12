

indicator = 'RHNA_HSG_7'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
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
    
    for jurisdiction in tqdm(jurisdictions):

        tqdm.write(jurisdiction)
                
        df_prod, df_pct = pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
    
    
        ## Plotting ---
        
        df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_plot = df_plot.drop(values, axis=1)
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        conditions = [
            df_plot[columns] == 'Units valued less than 250k'
            , df_plot[columns] == 'Units valued 250k-500k'
            , df_plot[columns] == 'Units valued 500k-750k'
            , df_plot[columns] == 'Units valued 750k-1M'
            , df_plot[columns] == 'Units valued 1M-1.5M'
            , df_plot[columns] == 'Units valued 1.5M-2M'
            , df_plot[columns] == 'Units valued 2M+'
        ]

        choices = ['Units valued less than &#36;250k', 'Units valued &#36;250k-&#36;500k', 'Units valued &#36;500k-&#36;750k', 'Units valued &#36;750k-&#36;1M', 'Units valued &#36;1M-&#36;1.5M', 'Units valued &#36;1.5M-&#36;2M', 'Units valued &#36;2M+']
        df_plot[columns] = np.select(conditions, choices, default='no')
        
        color_map = {
                "Units valued less than &#36;250k":"#1F45FC",
                "Units valued &#36;250k-&#36;500k":"#1E90FF",
                "Units valued &#36;500k-&#36;750k":"#9DC209",
                "Units valued &#36;750k-&#36;1M":"#FBB117",
                "Units valued &#36;1M-&#36;1.5M":"#7E587E",
                "Units valued &#36;1.5M-&#36;2M":"#DC381F",
                "Units valued &#36;2M+":"#006A4E"
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

