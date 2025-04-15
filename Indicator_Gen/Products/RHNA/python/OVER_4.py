

indicator_name = 'RHNA_OVER_4'


# Set indicator
source = 'CHAS'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator_name.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Severity'


## Importing ---

file_chas = path_raw / f'HUD_CHAS_2017thru2021.csv'
df_chas = pd.read_csv(file_chas, dtype=str)


## Organizing ---

df_chas['Households'] = df_chas['Households'].astype(int)

estimates = [
    'T10_est4', 'T10_est8', 'T10_est12', 'T10_est16', 'T10_est20', 'T10_est25', 'T10_est29', 'T10_est33',
    'T10_est37', 'T10_est41', 'T10_est46', 'T10_est50', 'T10_est54', 'T10_est58', 'T10_est62', 'T10_est68',
    'T10_est72', 'T10_est76', 'T10_est80', 'T10_est84', 'T10_est89', 'T10_est93', 'T10_est97', 'T10_est101',
    'T10_est105', 'T10_est110', 'T10_est114', 'T10_est118', 'T10_est122', 'T10_est126'
]

df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
print(df_chas['Description 1'].unique())
print(df_chas['Description 2'].unique())
print(df_chas['Description 3'].unique())
print(df_chas['Description 4'].unique())


df_chas = df_chas[['County Name', 'name', 'Description 2', 'Description 3', 'Households']]
df_chas = df_chas.rename(columns = {'Description 3':'Income Level', 'Description 2':'Severity'})
df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

conditions = [
      df_chas['Severity'] == ' AND persons per room is less than or equal to 1'
    , df_chas['Severity'] == ' AND persons per room is greater than 1 but less than or equal to 1.5'
    , df_chas['Severity'] == ' AND persons per room is greater than 1.5'
]

choices = ['Less than or equal to 1 person per room', '1 to 1.5 occupants per room', 'More than 1.5 occupants per room']

df_chas['Severity'] = np.select(conditions, choices, default='no')

conditions = [
    df_chas['Income Level'  ] == ' AND household income is less than or equal to 30% of HAMFI'
    , df_chas['Income Level'] == ' AND household income is greater than 30% but less than or equal to 50% of HAMFI'
    , df_chas['Income Level'] == ' AND household income is greater than 50% but less than or equal to 80% of HAMFI'
    , df_chas['Income Level'] == ' AND household income is greater than 80% but less than or equal to 100% of HAMFI'
    , df_chas['Income Level'] == ' AND household income is greater than 100% of HAMFI'
]

choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']

df_chas['Income Level'] = np.select(conditions, choices, default='no')


df_chas = df_chas.groupby(['County Name', 'name', 'Income Level', 'Severity'], as_index=False)['Households'].sum()

df_chas['Percentage'] = round(100 * (df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Income Level'])['Households'].transform('sum')), 1)
df_chas = df_chas[df_chas['Severity'] != 'Less than or equal to 1 person per room']


df_chas = df_chas.reset_index(drop=True)



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
        df_prod = df_prod.pivot_table(index=['Income Level'], columns=columns, values=values).reset_index()

        df_pct = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_pct = df_pct.drop('Households', axis=1)
        df_pct = df_pct.pivot_table(index=['Income Level'], columns=columns, values='Percentage').reset_index()
        
        ## Plotting ---

        df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        
        color_map  = {
            '1 to 1.5 occupants per room': '#9DC209'
            , 'More than 1.5 occupants per room': '#1F45FC'
        }

        fig = px.bar(df_plot, x='Income Level', y='Percentage'
                     , color = columns
                     , barmode='group'
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
        fig.update_yaxes(ticksuffix='%')

        path_plots = path_out / county / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator_name)


