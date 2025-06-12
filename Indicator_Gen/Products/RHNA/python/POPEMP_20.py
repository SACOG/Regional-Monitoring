

indicator = 'RHNA_POPEMP_20'


# Set indicator
source = 'ACS5'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Households'
columns = 'Tenure'


## Importing ---

df_places, df_counties, df_mpo = import_rhna(path_raw, indicator)


## Organizing ---



race_ethcnitiy_map = {
'American Indian or Alaska Native': 'American Indian or Alaska Native'
, 'Asian': 'Asian'
, 'Black or African American': 'Black or African American'
, 'Hispanic or Latino': 'Hispanic or Latino'
, 'Native Hawaiian or other Pacific Islander': 'Native Hawaiian or other Pacific Islander'
, 'White (NH)': 'White (NH)'
, 'Some other race': 'Other race or multiple races'
, 'Two or more races': 'Other race or multiple races'
}



df_places   = df_places  [df_places  ['Race_Ethnicity'] != 'All']
df_counties = df_counties[df_counties['Race_Ethnicity'] != 'All']
df_mpo      = df_mpo     [df_mpo     ['Race_Ethnicity'] != 'All']
        
df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
df_counties['NAME'] = df_counties['NAME'].str.replace(', California'     , '', regex=True)

df_places   = df_places  .rename(columns={'Variable':'Tenure'})
df_counties = df_counties.rename(columns={'Variable':'Tenure'})
df_mpo      = df_mpo     .rename(columns={'Variable':'Tenure'})

df_places   = df_places  .rename(columns={'NAME':'Geography', 'Race_Ethnicity':'Variable'})
df_counties = df_counties.rename(columns={'NAME':'Geography', 'Race_Ethnicity':'Variable'})
df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography', 'Race_Ethnicity':'Variable'})
df_mpo = df_mpo.drop_duplicates()

df_places   = df_places  [df_places  ['Year'] == df_places  ['Year'].max()]
df_counties = df_counties[df_counties['Year'] == df_counties['Year'].max()]
df_mpo      = df_mpo     [df_mpo     ['Year'] == df_mpo     ['Year'].max()]

df_places  ['Variable'] = df_places  ['Variable'].replace(race_ethcnitiy_map)
df_counties['Variable'] = df_counties['Variable'].replace(race_ethcnitiy_map)# trying to role up to new race/ethnicity mapping, it's new so may not run properly, double check
df_mpo     ['Variable'] = df_mpo     ['Variable'].replace(race_ethcnitiy_map)

df_places   = df_places  .groupby(['County Name', 'Geography', columns, 'Variable'], as_index=False)['Households'].sum()
df_counties = df_counties.groupby([               'Geography', columns, 'Variable'], as_index=False)['Households'].sum()
df_mpo      = df_mpo     .groupby([               'Geography', columns, 'Variable'], as_index=False)['Households'].sum()

df_places  ['Percentage'] = df_places  ['Households'] / df_places  .groupby(['County Name', 'Geography', 'Variable'])['Households'].transform('sum')
df_counties['Percentage'] = df_counties['Households'] / df_counties.groupby([               'Geography', 'Variable'])['Households'].transform('sum')
df_mpo     ['Percentage'] = df_mpo     ['Households'] / df_mpo     .groupby([               'Geography', 'Variable'])['Households'].transform('sum')

df_places   = df_places  [['County Name', 'Geography', 'Variable', columns, values, 'Percentage']]
df_counties = df_counties[[               'Geography', 'Variable', columns, values, 'Percentage']]
df_mpo      = df_mpo     [[               'Geography', 'Variable', columns, values, 'Percentage']]

df_places   = df_places  .reset_index(drop=True)
df_counties = df_counties.reset_index(drop=True)
df_mpo      = df_mpo     .reset_index(drop=True)


counties = df_counties['Geography'].unique()
df_counties

for county in counties:
    
    print();print()
    print(county)
    time.sleep(2)

    df_places_sub, df_counties_sub = sub_rhna(df_places, df_counties, county)
    jurisdictions = df_places_sub['Geography'].unique()
    
    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        df_prod, df_pct = pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values)

        ## Plotting ---

        df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
        
        color_map  = {
            'Owner occupied': '#1F45FC'
            , 'Renter occupied': '#9DC209'
        }

        fig = px.bar(df_plot, x='Variable', y=values
                     , color = columns
                     , barmode='group'
                     , color_discrete_map=color_map)
        
        fig.update_traces(hovertemplate="%{y}")
    
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)
    
        ## Exporting ---
        
        if export:
            export_rhna(df_prod, df_pct)

list_indicators.append(indicator)
