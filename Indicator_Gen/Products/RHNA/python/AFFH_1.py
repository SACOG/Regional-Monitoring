


## Two options:
# 1) Provide county level summaries, similar to HOMELS_1
# 2) Provide jurisdiction level summaries by summarizing all tracts intersecting with jurisdiction
# - 1 is easier, 2 might be better but not sure if it's worth it, considering some tracts are gigantic and include multiple jurisdictions, unincorporated territories would share distant tracts, etc...
# - so might make more sense to just use overall county


# Use number (2)


indicator = 'RHNA_AFFH_1'


# Set indicator
source = 'FFIEC'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
values = 'Population'
columns = 'Race_Ethnicity'


## Importing ---


years    = ['2023']
counties = ['06101','06115','06113','06061','06017','06067']

dtypes = {
    'loan_to_value_ratio'           : str
    , 'interest_rate'               : str
    , 'rate_spread'                 : str
    , 'total_loan_costs'            : str
    , 'total_points_and_fees'       : str
    , 'origination_charges'         : str
    , 'discount_points'             : str
    , 'lender_credits'              : str
    , 'loan_term'                   : str
    , 'prepayment_penalty_term'     : str
    , 'intro_rate_period'           : str
    , 'property_value'              : str
    , 'total_units'                 : str
    , 'multifamily_affordable_units': str
    , 'census_tract'                : str
}

action_map = {
      1:'Loan originated'
    , 2:'Application approved but not accepted'
    , 3:'Application denied'
    , 4:'Application withdrawn by applicant'
    , 5:'File closed for incompleteness'
    , 6:'Purchased loan'
    , 7:'Preapproval request denied'
    , 8:'Preapproval request approved but not accepted'
}


def hmda_import(years, counties, dtypes, path_raw):
    '''
    Years can only be from 2018, to 2024. County codes can be found by using the online tool: https://ffiec.cfpb.gov/data-browser/data/2023?category=counties. 
    '''
    print(''); print('Importing data from HDMA...'); print('')

    list_df = []

    for year in tqdm(years):
        if int(year) < 2018 or int(year) > int(datetime.now().year - 1): 
            print(f"Error: the year {year} does not have accessible data.") 
            continue

        url = 'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?counties=' + ','.join(counties) + '&years=' + str(year)
        
        df = pd.read_csv(url, dtype=dtypes)

        list_df.append(df)
    
    df = pd.concat(list_df, ignore_index=True)

    return df

df = hmda_import(years=years, counties=counties, dtypes=dtypes, path_raw=path_raw)

df = df[['county_code', 'census_tract', 'derived_ethnicity', 'derived_race', 'action_taken']]
df['action_taken'] = df['action_taken'].replace(action_map)

df = df[~df['derived_ethnicity'].isin(['Joint', 'Free Form Text Only'])]
df = df[~df['derived_race'     ].isin(['Joint', 'Free Form Text Only'])]

df['Race_Ethnicity'] = df['derived_race'].copy()
df.loc[df['derived_ethnicity'] == 'Hispanic or Latino', 'Race_Ethnicity'] = 'Hispanic or Latino'
df.loc[df['derived_ethnicity'] == 'Not Hispanic or Latino', 'Race_Ethnicity'] = df[df['derived_ethnicity'] == 'Not Hispanic or Latino']['Race_Ethnicity'] + ' (NH)'
df.loc[(df['derived_ethnicity'] == 'Ethnicity Not Available') & (df['derived_race'] != 'Race Not Available'), 'Race_Ethnicity'] = df[(df['derived_ethnicity'] == 'Ethnicity Not Available') & (df['derived_race'] != 'Race Not Available')]['Race_Ethnicity'] + ' (NH)'
df.loc[df['Race_Ethnicity'] == 'Race Not Available', 'Race_Ethnicity'] = 'Unknown'
df.loc[df['Race_Ethnicity'] == 'Race Not Available (NH)', 'Race_Ethnicity'] = 'Unknown'

df = df.groupby(['county_code', 'census_tract', 'Race_Ethnicity', 'action_taken'], as_index=False).count()


## Read in census tracts shp
## Read in citycounty shp
## Intersect
## create crosswalk of tracts to jurisdictions
## merge jurisdictions onto mortgage lending data using census tracts

path_geo = Path(r'I:\Projects\Josh\Geospatial Data')

file_tracts = path_geo / 'GISOWNER' / 'T2020_Census_Tracts_SACOG_Region' / 'T2020_Census_Tracts_SACOG_Region.shp'
gdf_ct = gpd.read_file(file_tracts)
gdf_ct = gdf_ct.to_crs("EPSG:2226")


file_cdp = path_geo / 'GISOWNER' / 'CityCounty' / 'CityCounty.shp'
gdf_cdp = gpd.read_file(file_cdp)
gdf_cdp = gdf_cdp.to_crs("EPSG:2226")

gdf_int = gpd.overlay(gdf_ct, gdf_cdp, how='intersection')

gdf_int['COUNTY_1'] = gdf_int['COUNTY_1'].astype(str).str[:-2].apply('{:0>3}'.format)
gdf_int['TRACT'   ] = gdf_int['TRACT'   ].astype(str).str[:-2].apply('{:0>6}'.format)
gdf_int['census_tract'] = '06' + gdf_int['COUNTY_1'] + gdf_int['TRACT']
gdf_int = gdf_int[['census_tract', 'COUNTY_2', 'JURIS']]
gdf_int = gdf_int.reset_index(drop=True)


gdf_int['census_tract'] = gdf_int['census_tract'].str[1:].astype('int64')
df['census_tract'] = df['census_tract'].str[1:].astype('int64')



df = df.merge(gdf_int, on='census_tract', how='left')

df = df[['COUNTY_2', 'JURIS', 'Race_Ethnicity', 'action_taken']]

df = df.groupby(['COUNTY_2', 'JURIS', 'Race_Ethnicity', 'action_taken'], as_index=False).size()
df['Percentage'] = df['size'] / df.groupby(['COUNTY_2', 'JURIS', 'Race_Ethnicity'], as_index=False)['size'].transform('sum')
df.loc[df['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

display(df.head())

## Organizing ---



counties = list(df['COUNTY_2'].unique())


for county in counties:

    print(); print()
    print(county)

    path_county = path_out / county
    df_sub = df[df['COUNTY_2'] == county]
    jurisdictions = list(df_sub['JURIS'].unique())

    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        df_sub_juris = df_sub[df_sub['JURIS'] == jurisdiction]

        ## Plotting ---

        df_plot = df_sub_juris.copy()

        df_prod = df_sub_juris[['Race_Ethnicity', 'action_taken', 'size']]
        df_prod = df_prod.pivot_table(index='Race_Ethnicity', columns='action_taken', values='size').reset_index()

        df_pct  = df_sub_juris[['Race_Ethnicity', 'action_taken', 'Percentage']]
        df_pct = df_pct.pivot_table(index='Race_Ethnicity', columns='action_taken', values='Percentage').reset_index()

        df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            
        color_map = {
              'Loan originated':'#1E90FF'
            , 'Application approved but not accepted':'#1F45FC'
            , 'Application denied': '#9DC209'
            , 'Application withdrawn by applicant':'#7FFFD4'
            , 'File closed for incompleteness':'#7E587E'
            , 'Purchased loan': '#FBB117'
            , 'Preapproval request denied':'#008000'
            , 'Preapproval request approved but not accepted':'#DC381F'
        }
    
        fig = px.bar(df_plot, x='Race_Ethnicity', y='Percentage'
                     , color = 'action_taken'
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

