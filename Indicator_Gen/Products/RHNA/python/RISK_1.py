


def sub_rhna(df_places, df_counties, county):
    
    df_counties_sub = df_counties[df_counties['Geography'  ] == county]
    df_places_sub   = df_places  [df_places  ['County'     ] == county]

    df_places_sub = df_places_sub.drop('County', axis=1)
    df_places_sub   = df_places_sub  .reset_index(drop=True)
    df_counties_sub = df_counties_sub.reset_index(drop=True)

    return df_places_sub, df_counties_sub


def clean_rhna(df_chp):

    df_chp['MPO'] = 'SACOG Region'
    df_chp.loc[df_chp['Risk Level'] == 'HIgh', 'Risk Level'] = 'High'
    df_chp['County'] = df_chp['County'] + ' County'

    df_mpo      = df_chp.groupby(['MPO'           , 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'MPO':'Geography'})
    df_counties = df_chp.groupby(['County'        , 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'County':'Geography'})
    df_places   = df_chp.groupby(['County', 'City', 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'City':'Geography'})

    df_mpo2      = df_chp.groupby(['MPO'           ], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'MPO':'Geography'})
    df_counties2 = df_chp.groupby(['County'        ], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'County':'Geography'})
    df_places2   = df_chp.groupby(['County', 'City'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'City':'Geography'})

    df_mpo2     ['Risk Level'] = 'Total Assisted Units in Database'
    df_counties2['Risk Level'] = 'Total Assisted Units in Database'
    df_places2  ['Risk Level'] = 'Total Assisted Units in Database'

    df_mpo      = pd.concat([df_mpo     , df_mpo2     ])
    df_counties = pd.concat([df_counties, df_counties2])
    df_places   = pd.concat([df_places  , df_places2  ])

    df_mpo      = df_mpo     .merge(df_mpo2     .drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=[          'Geography'], how='left')
    df_counties = df_counties.merge(df_counties2.drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=[          'Geography'], how='left')
    df_places   = df_places  .merge(df_places2  .drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=['County', 'Geography'], how='left')

    df_mpo     ['Percentage'] = df_mpo     ['affordable_units']/df_mpo     ['total_affordable_units']
    df_counties['Percentage'] = df_counties['affordable_units']/df_counties['total_affordable_units']
    df_places  ['Percentage'] = df_places  ['affordable_units']/df_places  ['total_affordable_units']

    df_mpo      = df_mpo     .drop('total_affordable_units', axis=1)
    df_counties = df_counties.drop('total_affordable_units', axis=1)
    df_places   = df_places  .drop('total_affordable_units', axis=1)

    df_mpo     ['Sort'] = pd.Categorical(df_mpo     ['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
    df_counties['Sort'] = pd.Categorical(df_counties['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
    df_places  ['Sort'] = pd.Categorical(df_places  ['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])

    df_mpo      = df_mpo     .sort_values(['Geography', 'Sort']).reset_index(drop=True).drop('Sort', axis=1)
    df_counties = df_counties.sort_values(['Geography', 'Sort']).reset_index(drop=True).drop('Sort', axis=1)
    df_places   = df_places  .sort_values(['Geography', 'Sort']).reset_index(drop=True).drop('Sort', axis=1)

    return df_places, df_counties, df_mpo



def pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub=None, df_mpo=None):

    indicator = indicator.replace('RHNA_', '')

    df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
    if 'Percentage' in df_places_sub.columns:
        df_prod = df_prod.drop('Percentage', axis=1)
    df_prod = df_prod.pivot_table(index='Geography', columns=columns, values=values).reset_index()
    df_prod['Sort'] = pd.Categorical(df_prod['Geography'], [jurisdiction, county, 'SACOG Region'])
    df_prod = df_prod.sort_values(['Sort'])
    df_prod = df_prod.drop(['Sort'], axis=1)

    if 'Percentage' in df_places_sub.columns:
        df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_pct = df_pct.drop(values, axis=1)
        
        df_pct = df_pct.pivot_table(index='Geography', columns=columns, values='Percentage').reset_index()
        df_pct['Sort'] = pd.Categorical(df_pct['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_pct = df_pct.sort_values(['Sort'])
        df_pct = df_pct.drop(['Sort'], axis=1)

    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod, df_pct





indicator = 'RHNA_RISK_1'


# Set indicator
source = 'CHP'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'affordable_units'
columns = 'Risk Level'


## Importing ---

file_in = path_raw /  'CA Housing Partnership.xlsx'

list_chp = []
counties = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']
for county in counties:
    df = pd.read_excel(file_in, sheet_name=county)
    df['County'] = county
    list_chp.append(df)

df_chp = pd.concat(list_chp)


file_area = path_config0 / 'area_codes.xlsx'
df_area = pd.read_excel(file_area, sheet_name='CDPcodes')
df_area = df_area[(df_area['Year']==2020) & (df_area['Incorporated'] == 'Yes')]
df_area['NAME'] = df_area['NAME'].str.replace(' CDP' , '', regex=True)
df_area['NAME'] = df_area['NAME'].str.replace(' city', '', regex=True)
df_area['NAME'] = df_area['NAME'].str.replace(' town', '', regex=True)


df_chp['City'] = df_chp['City'].str.title()
df_chp.loc[df_chp['City'] == 'Unincorporated Santa Cruz', 'City'] = 'Live Oak' # This needs a manual correction, seems like some manual checks are needed each time
df_chp.loc[~df_chp['City'].isin(df_area.NAME.unique()), 'City'] = 'Unincorporated'


df_places, df_counties, df_mpo = clean_rhna(df_chp)



counties = df_counties['Geography'].unique()

for county in counties:

    print();print()
    print(county); print()
    time.sleep(2)

    df_places_sub, df_counties_sub = sub_rhna(df_places, df_counties, county)
    jurisdictions = df_places_sub['Geography'].unique()

    
    for jurisdiction in tqdm(jurisdictions, position=0):
        
        tqdm.write(jurisdiction)
             
        df_prod, df_pct = pivot_rhna(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
        df_prod = df_prod[['Geography', 'Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database']]
        df_pct  = df_pct [['Geography', 'Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database']]

    
        ## Plotting ---
        
        df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_plot = df_plot[df_plot['Risk Level'] != 'Total Assisted Units in Database']
        df_plot = df_plot.drop(values, axis=1)
        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)

        df_plot['sort_risk'] = pd.Categorical(df_plot['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
        df_plot['sort_geo' ] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG Region'])
        df_plot = df_plot.sort_values(['sort_geo', 'sort_risk']).reset_index(drop=True).drop(['sort_geo', 'sort_risk'], axis=1)
           
        color_map  = {
            'Low': '#1F45FC'
            , 'Moderate': '#9DC209'
            , 'High': '#FBB117'
            , 'Very High': '#DC381F'
        }
    
        fig = px.bar(df_plot, x='Geography', y='Percentage'
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





## Code graveyard ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# indicator = 'RHNA_RISK_1'

# source='temp'
# with path_func.open("r") as f: exec(f.read())

# counties = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']

# dt_juris = {
#     'El Dorado': ['Placerville', 'South Lake Tahoe', 'Unincorporated'],
#     'Placer': ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville', 'Unincorporated'],
#     'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento', 'Unincorporated'],
#     'Sutter': ['Live Oak', 'Yuba City', 'Unincorporated'],
#     'Yolo': ['Davis', 'West Sacramento', 'Winters', 'Woodland', 'Unincorporated'],
#     'Yuba': ['Marysville', 'Wheatland', 'Unincorporated']
# }


# print()
# for county in counties:
#     print(county)
#     for jurisdiction in dt_juris[county]:
#         export_rhna_temp()



