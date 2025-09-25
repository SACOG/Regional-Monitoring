



indicator = 'RHNA_FARM_2'


# Set indicator
source = 'USDA'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]


## Importing ---

file_in = path_raw / 'USDA' / 'USDA_FarmWorkers_Summarized.xlsx'
df_usda = pd.read_excel(file_in)



## Organizing

counties = list(df_usda['County'].unique())


for county in counties:

    print(county)

    path_county = path_out / county
    jurisdictions = [str(f.stem) for f in path_county.iterdir()]

    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        df_prod = df_usda[df_usda['County'] == county]
        df_prod = df_prod.drop('County', axis=1)


        ## Plotting ---

        df_plot = df_prod.copy()
        df_plot = df_prod.melt(id_vars='Farm Worker', var_name='Year', value_name='Number of Workers')
        df_plot['Year'] = df_plot['Year'].str.replace('Year ', '')
        
        color_map = {
                "2002":"#1F45FC",
                "2007":"#1E90FF",
                "2012":"#9DC209",
                "2017":"#FBB117",
                "2022":"#DC381F"
        }

        fig = px.bar(df_plot, x='Farm Worker', y='Number of Workers'
                     , color = 'Year'
                     , color_discrete_map=color_map
                     , barmode='group')
        
        fig.update_traces(hovertemplate="%{y}")
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.175,xanchor="right", x=0.55))
            
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        if export:
            export_rhna(df_prod)
        

list_indicators.append(indicator)

