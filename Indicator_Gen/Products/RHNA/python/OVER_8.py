

indicator_name = 'RHNA_OVER_8'


# Set indicator
source = 'CHAS'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator_name.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Cost Burden'


## Importing ---

file_chas = path_raw / f'HUD_CHAS_2017thru2021.csv'
df_chas = pd.read_csv(file_chas, dtype=str)


## Organizing ---

df_chas['Households'] = df_chas['Households'].astype(int)

estimates = [
    'T9_est4', 'T9_est5', 'T9_est6', 'T9_est7', 'T9_est9', 'T9_est10', 'T9_est11', 'T9_est12',
    'T9_est14', 'T9_est15', 'T9_est16', 'T9_est17', 'T9_est19', 'T9_est20', 'T9_est21', 'T9_est22',
    'T9_est24', 'T9_est25', 'T9_est26', 'T9_est27', 'T9_est29', 'T9_est30', 'T9_est31', 'T9_est32',
    'T9_est34', 'T9_est35', 'T9_est36', 'T9_est37', 'T9_est40', 'T9_est41', 'T9_est42', 'T9_est43',
    'T9_est45', 'T9_est46', 'T9_est47', 'T9_est48', 'T9_est50', 'T9_est51', 'T9_est52', 'T9_est53',
    'T9_est55', 'T9_est56', 'T9_est57', 'T9_est58', 'T9_est60', 'T9_est61', 'T9_est62', 'T9_est63',
    'T9_est65', 'T9_est66', 'T9_est67', 'T9_est68', 'T9_est70', 'T9_est71', 'T9_est72', 'T9_est73'
]

df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
print(df_chas['Description 1'].unique())
print(df_chas['Description 2'].unique())
print(df_chas['Description 3'].unique())
print(df_chas['Description 4'].unique())


df_chas = df_chas[['County Name', 'name', 'Description 2', 'Description 3', 'Households']]
df_chas = df_chas.rename(columns = {'Description 2':'Race Ethnicity', 'Description 3':'Cost Burden'})
df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

conditions = [
      df_chas['Cost Burden'] == ' AND housing cost burden is less than or equal to 30%'
    , df_chas['Cost Burden'] == ' AND housing cost burden is greater than 30% but less than or equal to 50%'
    , df_chas['Cost Burden'] == ' AND housing cost burden is greater than 50%'
    , df_chas['Cost Burden'] == ' AND housing cost burden not computed (no/negative income)'
]

choices = ['0%-30% of income used for housing', '30%-50% of income used for housing', '50%+ of income used for housing', 'Not computed']

df_chas['Cost Burden'] = np.select(conditions, choices, default='no')


conditions = [
      df_chas['Race Ethnicity'] == ' AND race/ethnicity is American Indian or Alaska Native alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == ' AND race/ethnicity is Asian alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == ' AND race/ethnicity is Black or African-American alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == ' AND race/ethnicity is White alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == ' AND race/ethnicity is Hispanic, any race'
    , df_chas['Race Ethnicity'] == ' AND race/ethnicity is Pacific Islander alone, non-Hispanic'
    , df_chas['Race Ethnicity'] == ' AND race/ethnicity is other (including multiple races, non-Hispanic)'
]

choices = ['American Indian or Alaska Native (NH)', 'Asian (NH)', 'Black or African American (NH)', 'White (NH)', 'Hispanic or Latino', 'Other race or multiple races (NH)', 'Other race or multiple races (NH)']

df_chas['Race Ethnicity'] = np.select(conditions, choices, default='no')


df_chas = df_chas.groupby(['County Name', 'name', 'Race Ethnicity', 'Cost Burden'], as_index=False)['Households'].sum()
df_chas['Percentage'] = round(100 * (df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Race Ethnicity'])['Households'].transform('sum')), 1)
df_chas = df_chas[df_chas['Cost Burden'] != 'Not computed']


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
        df_prod = df_prod.pivot_table(index=['Race Ethnicity'], columns=columns, values=values).reset_index()

        df_pct = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        df_pct = df_pct.drop('Households', axis=1)
        df_pct = df_pct.pivot_table(index=['Race Ethnicity'], columns=columns, values='Percentage').reset_index()
        
        ## Plotting ---

        df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
        
        color_map  = {
            '0%-30% of income used for housing': '#1F45FC'
            , '30%-50% of income used for housing': '#1E90FF'
            , '50%+ of income used for housing': '#9DC209'
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

list_indicators.append(indicator_name)

