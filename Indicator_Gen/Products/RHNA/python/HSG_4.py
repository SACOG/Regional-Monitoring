

indicator = 'RHNA_HSG_4'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'


## Importing ---

df_places, df_counties, df_mpo = import_rhna(path_raw, indicator)



## Organizing ---

df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
df_places = df_places.rename(columns={'NAME':'Geography'})
df_places = df_places[df_places['Year'] == df_places['Year'].max()]
df_places = df_places.reset_index(drop=True)

df_places = df_places[['County Name', 'Geography', values, 'Variable', 'Percentage']].drop_duplicates()

df_places['Sort'] = pd.Categorical(df_places['Variable'], ['Built 2010 or later', 'Built 2000 to 2009', 'Built 1980 to 1999'
                                                           , 'Built 1960 to 1979', 'Built 1940 to 1959', 'Built 1939 or earlier'])
df_places = df_places.sort_values(['County Name', 'Geography', 'Sort'], ascending=[True, True, False])
df_places = df_places.drop(['Sort'], axis = 1)

counties = list(df_places['County Name'].unique())


for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_places_sub = df_places.copy()
    df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
    jurisdictions = df_places_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions):

        tqdm.write(jurisdiction)

        df_prod0 = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_prod = df_prod0[['Variable', values         ]].drop_duplicates()
        df_pct  = df_prod0[['Variable', 'Percentage'   ]].drop_duplicates()
        df_plot = df_prod.copy()

        ## Plotting ---

        fig = px.bar(df_plot, x='Variable', y=values)
        fig.update_traces(marker_color='#1E90FF')
        fig.update_traces(hovertemplate="%{y}")

        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
        
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)


list_indicators.append(indicator)

