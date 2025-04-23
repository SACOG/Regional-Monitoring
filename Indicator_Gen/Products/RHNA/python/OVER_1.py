

indicator = 'RHNA_OVER_1'


# Set indicator
source = 'CHAS'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Severity'


## Importing ---

file_chas = path_raw / f'HUD_CHAS_2017thru2021.csv'
df_chas = pd.read_csv(file_chas, dtype=str)


## Organizing ---

df_chas['Households'] = df_chas['Households'].astype(int)

estimates = ['T10_est3', 'T10_est24', 'T10_est45', 'T10_est67', 'T10_est88', 'T10_est109']

df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
print(df_chas['Description 1'].unique())
print(df_chas['Description 2'].unique())
print(df_chas['Description 3'].unique())
print(df_chas['Description 4'].unique())


df_chas = df_chas[['County Name', 'name', 'Description 1', 'Description 2', 'Households']]
df_chas = df_chas.rename(columns = {'Description 1':'Tenure', 'Description 2':'Severity'})
df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

conditions = [
      df_chas['Severity'] == ' AND persons per room is less than or equal to 1'
    , df_chas['Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
    , df_chas['Severity'] == ' AND persons per room is greater than 1.5'
]

choices = ['Less than or equal to 1 person per room', '1 to 1.5 occupants per room', 'More than 1.5 occupants per room']

df_chas['Severity'] = np.select(conditions, choices, default='no')
df_chas['Percentage'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Tenure'])['Households'].transform('sum')
df_chas = df_chas[df_chas['Severity'] != 'Less than or equal to 1 person per room']
df_chas = df_chas.reset_index(drop=True)

display(df_chas)


counties = list(df_chas['County Name'].unique())

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_chas_sub = df_chas[df_chas['County Name'] == county]
    jurisdictions = df_chas_sub['name'].unique()
    
    for jurisdiction in tqdm(jurisdictions):

        tqdm.write(jurisdiction)

        df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_prod = df_prod.drop('Percentage', axis=1)
        df_prod = df_prod.pivot_table(index=['Tenure'], columns=columns, values=values).reset_index()

        df_pct = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_pct = df_pct.drop('Households', axis=1)
        df_pct = df_pct.pivot_table(index=['Tenure'], columns=columns, values='Percentage').reset_index()
        
        ## Plotting ---

        df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        
        color_map  = {
            '1 to 1.5 occupants per room': '#9DC209'
            , 'More than 1.5 occupants per room': '#1F45FC'
        }

        fig = px.bar(df_plot, x='Tenure', y=values
                     , color = columns
                     , barmode='group'
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
    
        path_plots = path_out / county / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)

