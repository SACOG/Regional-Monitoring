

indicator = 'RHNA_HSG_1'


# Set indicator
source = 'DOF'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values='Housing Units'
columns='Year'


## Importing ---

file_in = path_raw / 'DOF_E5_and_E8_Jurisdictions.xlsx'
df_dof = pd.read_excel(file_in)


## Organizing ---

df_dof = df_dof[df_dof['MPO'] == 'SACOG']
df_dof['MPO'] = df_dof['MPO'] + ' Region'
df_dof = df_dof[df_dof['Year'].isin([2010, 2020, 2024])]
df_dof = df_dof.sort_values('Year')
df_dof['Year'] = df_dof['Year'].astype(str)

df_dof = df_dof[['County', 'Jurisdiction', 'Year', 'Single Attached', 'Single Detached', 'Two to Four', 'Five Plus', 'Mobile Homes']]

df_dof = df_dof.melt(id_vars=['County', 'Jurisdiction', 'Year'], var_name='Housing Type', value_name='Housing Units')
df_dof = df_dof.reset_index(drop=True)



conditions = [
      df_dof['Housing Type'] == 'Single Attached'
    , df_dof['Housing Type'] == 'Single Detached'
    , df_dof['Housing Type'] == 'Two to Four'    
    , df_dof['Housing Type'] == 'Five Plus'      
    , df_dof['Housing Type'] == 'Mobile Homes'   
]

choices = ['Single Family Attached', 'Single Family Detached', 'Multifamily: Two to Four Units', 'Multifamily: 5+ Units', 'Mobile Homes']

df_dof['Housing Type'] = np.select(conditions, choices, default='no')

counties = list(df_dof['County'].unique())

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_dof_sub = df_dof[df_dof['County'] == county]
    jurisdictions = df_dof_sub['Jurisdiction'].unique()

    for jurisdiction in tqdm(jurisdictions):

        tqdm.write(jurisdiction)

        df_prod = df_dof_sub[df_dof_sub['Jurisdiction'] == jurisdiction]
        df_prod['Year'] = 'Year ' + df_prod['Year']
        df_prod = df_prod.pivot_table(index=['Housing Type'], columns=columns, values=values).reset_index()

        
        ## Plotting ---

        df_plot = df_dof_sub[df_dof_sub['Jurisdiction'] == jurisdiction]
        
        color_map = {
                 "2010":"#1F45FC",
                 "2020":"#1E90FF",
                 "2024": "#9DC209",
        }

        fig = px.bar(df_plot, x='Housing Type', y=values
                     , color = columns
                     , barmode='group'
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
        # fig.update_layout(legend={'traceorder': 'reversed'})

        path_plots = path_out / county / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod)

list_indicators.append(indicator)

