

indicator = 'RHNA_POPEMP_10'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Population'
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

df_places['Sort'] = pd.Categorical(df_places['Variable'], ['75k or more', '50k to 75k', '25k to 50k', '10k to 25k', 'Less than 10k'])
df_places = df_places.sort_values(['County Name', 'Geography', 'Category', 'Sort'], ascending=[True, True, True, False])
df_places = df_places.drop(['Sort'], axis = 1)
df_places = df_places.reset_index(drop=True)

conditions = [
    df_places['Variable'] == 'Less than 10k'
    , df_places['Variable'] == '10k to 25k'
    , df_places['Variable'] == '25k to 50k'
    , df_places['Variable'] == '50k to 75k'
    , df_places['Variable'] == '75k or more'
]

choices = ['Less than $10k', '$10k to $25k', '$25k to $50k', '$50k to $75k', '$75k or more']

df_places['Variable'] = np.select(conditions, choices, default = 'no')


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
        
        color_map  = {
            'Place of residence': '#9DC209'
            , 'Place of work': '#1F45FC'
        }

        fig = px.bar(df_plot, x='Variable', y=values
                     , color = columns
                     , barmode='group'
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
        fig.update_yaxes(tickprefix='$')
        fig.update_xaxes(tickvals=[0, 1, 2, 3, 4], ticktext=['Less than &#36;10k', '&#36;10k to &#36;25k', '&#36;25k to &#36;50k', '&#36;50k to &#36;75k', '&#36;75k or more'])
    
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)

