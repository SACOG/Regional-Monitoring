
## For DEC tables

print("Importing and compiling Decennial data from the Census Bureau...")
print()

# initialize empty list to store data frames
# import multiple years and counties
# iterate through each table and import all variables needed from each table
# combine all years and counties
# reduce all tables/variables pulled into one table

list_df_census = []

if import_tab == 'Counties':
    for state in list(dict_fips.keys()):
        print('State: ' + state)
        for year in tqdm(years_to_import):
            try:
                list_df_census.append(
                    query_census(df_urls       = df_urls
                                    , api_key   = api_key
                                    , estimate  = estimate
                                    , sample    = sample_type
                                    , geography = geography
                                    , variables = ','.join(dict_vars[str(year)])
                                    , year      = year
                                    , state     = state
                                    , county    = dict_fips[state])
                )
            except Exception as e: print(e)

if import_tab == 'States':
    for state in states_to_import:
        print('State: ' + state)
        for year in tqdm(years_to_import):
            try:
                list_df_census.append(
                    query_census(df_urls      = df_urls
                                    , api_key   = api_key
                                    , estimate  = estimate
                                    , sample    = sample_type
                                    , geography = geography
                                    , variables = variables
                                    , year      = year
                                    , state     = state)
                )
            except Exception as e: print(e)
                
if geography == 'Tracts':
    df_census_raw = pd.concat(list_df_census)
    df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'tract', 'Year']).reset_index()
if geography == 'Counties':
    df_census_raw = pd.concat(list_df_census)
    df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                            , left_on = ['state', 'county']
                                            , right_on = ['State FIPS', 'County FIPS'])
    df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
    df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'Year']).reset_index()