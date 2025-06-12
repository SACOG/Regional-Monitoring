



indicator = 'RHNA_POPEMP_17'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Year'


path_places2 = path_raw / f'{indicator} Places ACS5.xlsx'
df_places2 = pd.read_excel(path_places2, sheet_name='Places')

# Set indicator
source = 'DEC'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Year'


path_places1 = path_raw / f'{indicator} Places DEC.xlsx'
df_places1 = pd.read_excel(path_places1, sheet_name='Places')




## Organizing ---


df_places1['NAME'] = df_places1['NAME'].str.replace(' CDP, California' , '', regex=True)
df_places1['NAME'] = df_places1['NAME'].str.replace(' city, California', '', regex=True)
df_places2['NAME'] = df_places2['NAME'].str.replace(' CDP, California' , '', regex=True)
df_places2['NAME'] = df_places2['NAME'].str.replace(' city, California', '', regex=True)

df_places1 = df_places1.rename(columns={'NAME':'Geography'})
df_places2 = df_places2.rename(columns={'NAME':'Geography'})

df_places1 = df_places1[['County Name', 'Geography', 'Year', 'Variable', 'Households']]
df_places2 = df_places2[['County Name', 'Geography', 'Year', 'Variable', 'Households']]

df_places1 = df_places1.pivot_table(index=['County Name', 'Geography', 'Year'], columns='Variable', values='Households').reset_index()
df_places1['Owner occupied'] = df_places1['Total'] - df_places1['Renter occupied']
df_places1 = df_places1.drop('Total', axis=1)
df_places1 = df_places1.melt(id_vars=['County Name', 'Geography', 'Year'], var_name='Variable', value_name='Households')

df_places = pd.concat([df_places1, df_places2])




df_places['Percentage'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', 'Year'])['Households'].transform('sum')

df_places['Year'] = df_places['Year'].astype(str)
df_places['Year'] = 'Year ' + df_places['Year']


counties = df_places['County Name'].unique()

for county in counties:
    
    print();print()
    print(county)
    print()
    time.sleep(2)

    df_places_sub = df_places[df_places['County Name'] == county]
    df_places_sub = df_places_sub.drop('County Name', axis=1)
    jurisdictions = df_places_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions):
                
        tqdm.write(jurisdiction)
        df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction]

        df_prod = df_prod.drop('Geography', axis=1)
        df_prod = df_prod.pivot_table(index='Variable', columns=columns, values='Households').reset_index()
        df_prod = df_prod.reset_index(drop=True)

        df_pct = df_pct.drop('Geography', axis=1)
        df_pct = df_pct.pivot_table(index='Variable', columns=columns, values='Percentage').reset_index()
        df_pct = df_pct.reset_index(drop=True)
        

        ## Plotting ---
        
        df_plot = df_pct.melt(id_vars=['Variable'], var_name='Year', value_name='Percentage')
        df_plot['Year'] = df_plot['Year'].str.replace('Year ', '')
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        df_plot = df_plot.sort_values(['Year'], ascending=[True])
            
        color_map  = {
            'Owner occupied': '#1F45FC'
            , 'Renter occupied': '#9DC209'
        }
   
        fig = px.bar(df_plot, x='Year', y='Percentage'
                     , color='Variable'
                     , color_discrete_map=color_map)
        
        # title = f'<b>{plot_title}</b>'
        fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
        fig.update_layout(legend={'traceorder': 'reversed'})
        fig.update_traces(hovertemplate="%{y}")
    
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)

