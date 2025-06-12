

indicator = 'RHNA_POPEMP_18'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Category'


## Importing ---

df_places_a = pd.read_excel(os.path.join(path_raw, f'{indicator}a Places ACS5.xlsx'))
df_places_b = pd.read_excel(os.path.join(path_raw, f'{indicator}b Places ACS5.xlsx'))
df_places = pd.concat([df_places_a, df_places_b])


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
df_places['Category'] = df_places['Variable'].apply(re_remove_post)
df_places['Variable'] = df_places['Variable'].apply(re_remove_pre )


df_places = df_places[['County Name', 'Geography', values, columns, 'Variable', 'Percentage']]
df_places['Percentage'] = df_places[values] / df_places.groupby(['County Name', 'Geography', 'Variable'])[values].transform('sum')

df_places['Sort'] = pd.Categorical(df_places['Variable'], ['Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-59', 'Age 60-64', 'Age 65-74', 'Age 75-84', 'Age 85+'])
df_places = df_places.sort_values(['County Name', 'Geography', 'Category', 'Sort'], ascending=[True, True, True, True])
df_places = df_places.drop(['Sort'], axis = 1)
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
        
        color_map  = {
            'Owner occupied': '#1F45FC'
            , 'Renter occupied': '#9DC209'
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

