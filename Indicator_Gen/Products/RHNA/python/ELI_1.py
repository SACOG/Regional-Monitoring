

indicator = 'RHNA_ELI_1'


# Set indicator
source = 'CHAS'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Income Level'


## Importing ---

file_chas = path_raw / f'HUD_CHAS_2017thru2021.csv'
df_chas = pd.read_csv(file_chas, dtype=str)


## Organizing ---

df_chas['Households'] = df_chas['Households'].astype(int)

estimates = ['T7_est3', 'T7_est24', 'T7_est45', 'T7_est66', 'T7_est87', 'T7_est109', 'T7_est130', 'T7_est151', 'T7_est172', 'T7_est193']


df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
print(df_chas['Description 1'].unique())
print(df_chas['Description 2'].unique())
print(df_chas['Description 3'].unique())
print(df_chas['Description 4'].unique())


df_chas = df_chas[['County Name', 'name', 'Description 2', 'Households']]
df_chas = df_chas.rename(columns = {'Description 2':'Income Level'})
df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

conditions = [
    df_chas['Income Level'] == 'household income is less than or equal to 30% of HAMFI'
    , df_chas['Income Level'] == 'household income is greater than 30% but less than or equal to 50% of HAMFI'
    , df_chas['Income Level'] == 'household income is greater than 50% but less than or equal to 80% of HAMFI'
    , df_chas['Income Level'] == 'household income is greater than 80% but less than or equal to 100% of HAMFI'
    , df_chas['Income Level'] == 'household income is greater than 100% of HAMFI'
]

choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']

df_chas['Income Level'] = np.select(conditions, choices, default='no')


df_chas     = df_chas.groupby(['County Name', 'name', 'Income Level'], as_index=False)['Households'].sum()
df_counties = df_chas.groupby(['County Name',         'Income Level'], as_index=False)['Households'].sum()
df_mpo      = df_chas.groupby([                       'Income Level'], as_index=False)['Households'].sum()
df_mpo['MPO'] = 'SACOG Region'

df_chas    ['Percentage'] = df_chas    ['Households'] / df_chas    .groupby(['County Name', 'name'])['Households'].transform('sum')
df_counties['Percentage'] = df_counties['Households'] / df_counties.groupby(['County Name'        ])['Households'].transform('sum')
df_mpo     ['Percentage'] = df_mpo     ['Households'] / df_mpo     .groupby(['MPO'                ])['Households'].transform('sum')

df_chas     = df_chas    .rename(columns = {'name':'Geography'})
df_counties = df_counties.rename(columns = {'County Name':'Geography'})
df_mpo      = df_mpo     .rename(columns = {'MPO':'Geography'})

df_chas    = df_chas    .reset_index(drop=True)
df_counties= df_counties.reset_index(drop=True)
df_mpo     = df_mpo     .reset_index(drop=True)


counties = list(df_chas['County Name'].unique())

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)
    print()

    df_counties_sub              = df_counties    [df_counties['Geography'  ] == county]
    df_chas_sub                  = df_chas        [df_chas    ['County Name'] == county]
    df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'

    df_chas_sub = df_chas_sub.drop(['County Name'], axis=1)
    jurisdictions = df_chas_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions):

        tqdm.write(jurisdiction)

        df_prod = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_prod = df_prod.drop('Percentage', axis=1)
        df_prod = df_prod.pivot_table(index=['Geography'], columns=columns, values=values).reset_index()

        df_pct = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_pct = df_pct.drop('Households', axis=1)
        df_pct = df_pct.pivot_table(index=['Geography'], columns=columns, values='Percentage').reset_index()
        
        ## Plotting ---

        df_plot = pd.concat([df_chas_sub[df_chas_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        
        color_map  = {
            '0%-30% of AMI': '#1F45FC'
            , '31%-50% of AMI': '#1E90FF'
            , '51%-80% of AMI': '#9DC209'
            , '81%-100% of AMI': '#FBB117'
            , 'Greater than 100% of AMI': '#7E587E'
        }

        fig = px.bar(df_plot, x='Geography', y='Percentage'
                     , color = columns
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
        fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
        fig.update_layout(legend={'traceorder': 'reversed'})
    
        path_plots = path_out / county / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)
