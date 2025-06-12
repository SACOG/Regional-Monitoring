

indicator = 'RHNA_ELI_2'


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

estimates = [
    'T1_est5', 'T1_est6', 'T1_est7', 'T1_est8', 'T1_est9', 'T1_est10', 'T1_est12', 'T1_est13', 'T1_est14',
    'T1_est15', 'T1_est16', 'T1_est17', 'T1_est19', 'T1_est20', 'T1_est21', 'T1_est22', 'T1_est23', 'T1_est24',
    'T1_est26', 'T1_est27', 'T1_est28', 'T1_est29', 'T1_est30', 'T1_est31', 'T1_est33', 'T1_est34', 'T1_est35',
    'T1_est36', 'T1_est37', 'T1_est38', 'T1_est41', 'T1_est42', 'T1_est43', 'T1_est44', 'T1_est45', 'T1_est46',
    'T1_est48', 'T1_est49', 'T1_est50', 'T1_est51', 'T1_est52', 'T1_est53', 'T1_est55', 'T1_est56', 'T1_est57',
    'T1_est58', 'T1_est59', 'T1_est60', 'T1_est62', 'T1_est63', 'T1_est64', 'T1_est65', 'T1_est66', 'T1_est67',
    'T1_est69', 'T1_est70', 'T1_est71', 'T1_est72', 'T1_est73', 'T1_est74', 'T1_est78', 'T1_est79', 'T1_est80',
    'T1_est81', 'T1_est82', 'T1_est83', 'T1_est85', 'T1_est86', 'T1_est87', 'T1_est88', 'T1_est89', 'T1_est90',
    'T1_est92', 'T1_est93', 'T1_est94', 'T1_est95', 'T1_est96', 'T1_est97', 'T1_est99', 'T1_est100', 'T1_est101',
    'T1_est102', 'T1_est103', 'T1_est104', 'T1_est106', 'T1_est107', 'T1_est108', 'T1_est109', 'T1_est110', 'T1_est111',
    'T1_est114', 'T1_est115', 'T1_est116', 'T1_est117', 'T1_est118', 'T1_est119', 'T1_est121', 'T1_est122', 'T1_est123',
    'T1_est124', 'T1_est125', 'T1_est126', 'T1_est128', 'T1_est129', 'T1_est130', 'T1_est131', 'T1_est132', 'T1_est133',
    'T1_est135', 'T1_est136', 'T1_est137', 'T1_est138', 'T1_est139', 'T1_est140', 'T1_est142', 'T1_est143', 'T1_est144',
    'T1_est145', 'T1_est146', 'T1_est147'
]

df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
print(df_chas['Description 1'].unique())
print(df_chas['Description 2'].unique())
print(df_chas['Description 3'].unique())
print(df_chas['Description 4'].unique())


df_chas = df_chas[['County Name', 'name', 'Description 4', 'Description 3', 'Households']]
df_chas = df_chas.rename(columns = {'Description 4':'Race Ethnicity', 'Description 3':'Income Level'})
df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

conditions = [
    df_chas['Income Level'  ] == 'less than or equal to 30% of HAMFI'
    , df_chas['Income Level'] == 'greater than 30% but less than or equal to 50% of HAMFI'
    , df_chas['Income Level'] == 'greater than 50% but less than or equal to 80% of HAMFI'
    , df_chas['Income Level'] == 'greater than 80% but less than or equal to 100% of HAMFI'
    , df_chas['Income Level'] == 'greater than 100% of HAMFI'
]

choices = ['0%-30% of AMI', '31%-50% of AMI', '51%-80% of AMI', '81%-100% of AMI', 'Greater than 100% of AMI']

df_chas['Income Level'] = np.select(conditions, choices, default='no')


conditions = [
      df_chas['Race Ethnicity'] == 'American Indian or Alaska Native alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == 'Asian alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == 'Black or African-American alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == 'White alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == 'Hispanic, any race'
    , df_chas['Race Ethnicity'] == 'Pacific Islander alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == 'other (including multiple races, non-Hispanic)'
]

choices = ['American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'White (NH)', 'Hispanic or Latino', 'Other race or multiple races (NH)', 'Other race or multiple races (NH)']

df_chas['Race Ethnicity'] = np.select(conditions, choices, default='no')


df_chas = df_chas.groupby(['County Name', 'name', 'Race Ethnicity', 'Income Level'], as_index=False)['Households'].sum()
df_chas['Percentage'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Race Ethnicity'])['Households'].transform('sum')


df_chas = df_chas.reset_index(drop=True)


counties = list(df_chas['County Name'].unique())

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)
    print()

    df_chas_sub = df_chas[df_chas['County Name'] == county]
    jurisdictions = df_chas_sub['name'].unique()
    
    for jurisdiction in tqdm(jurisdictions):

        tqdm.write(jurisdiction)

        df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_prod = df_prod.drop('Percentage', axis=1)
        df_prod = df_prod.pivot_table(index=['Race Ethnicity'], columns=columns, values=values).reset_index()

        df_pct = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_pct = df_pct.drop('Households', axis=1)
        df_pct = df_pct.pivot_table(index=['Race Ethnicity'], columns=columns, values='Percentage').reset_index()
        
        ## Plotting ---

        df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
        
        color_map  = {
            '0%-30% of AMI': '#1F45FC'
            , '31%-50% of AMI': '#1E90FF'
            , '51%-80% of AMI': '#9DC209'
            , '81%-100% of AMI': '#FBB117'
            , 'Greater than 100% of AMI': '#7E587E'
        }

        fig = px.bar(df_plot, x='Race Ethnicity', y='Percentage'
                     , color = columns
                     # , barmode='group'
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
        fig.update_yaxes(ticksuffix='%')
        fig.update_layout(legend={'traceorder': 'reversed'})

        path_plots = path_out / county / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)

