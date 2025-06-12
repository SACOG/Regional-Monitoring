


indicator = 'RHNA_OVER_6'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Burden'


## Importing ---

df_places = pd.read_excel(os.path.join(path_raw, f'{indicator} Places ACS5.xlsx'))


## Organizing ---

def re_remove_post(x, exp = ':'):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[0]

def re_remove_pre(x, exp = ':  '):
    if x == 'nan':
        return 'nan'
    else:
        return str(x.split(exp, 1)[1])

df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
df_places = df_places.rename(columns={'NAME':'Geography'})
df_places = df_places[df_places['Year'] == df_places['Year'].max()]
df_places = df_places.reset_index(drop=True)
df_places['Tenure'  ] = df_places['Variable'].apply(re_remove_post)
df_places['Burden'  ] = df_places['Variable'].apply(re_remove_pre )
df_places['Variable'] = df_places['Tenure'].copy()
df_places['Percentage'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', 'Variable'])['Households'].transform('sum')

df_places = df_places[['County Name', 'Geography', values, 'Variable', columns, 'Percentage']]

df_places['Sort'] = pd.Categorical(df_places['Burden'], ['0%-30% of income used for housing', '30%-50% of income used for housing', '50% or more of income used for housing', 'Not computed'])
df_places = df_places.sort_values(['County Name', 'Geography', 'Variable', 'Sort'], ascending=[True, True, True, True])
df_places = df_places.drop(['Sort'], axis = 1)
df_places = df_places.reset_index(drop=True)
# df_places


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
        
        color_map = {
                "0%-30% of income used for housing":"#1F45FC",
                "30%-50% of income used for housing":"#1E90FF",
                "50% or more of income used for housing":"#9DC209",
                "Not computed":"#9B9A96"
        }

        fig = px.bar(df_plot, x='Variable', y='Percentage'
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

