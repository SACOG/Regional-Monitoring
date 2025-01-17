
## For CPS tables


print("Importing and compiling CPS data from the Census Bureau...")
print()

list_df_census = []

for state in list(dict_fips.keys()):
    print('State: ' + state)
    for year in tqdm(years_to_import):
        try:
            temp = query_census(df_urls      = df_urls
                                    , api_key   = api_key
                                    , estimate  = estimate
                                    , sample    = sample_type
                                    , geography = geography
                                    , variables = 'HRHHID,HRHHID2,PERRP,'+','.join(dict_vars[str(year)])
                                    , year      = year
                                    , state     = state
                                    , county    = dict_fips[state])
            list_df_census.append(temp)
        except Exception as e: print(e)
            
df_census_raw = pd.concat(list_df_census)

# merge county name onto table
df_census_raw['state' ] = df_census_raw['state' ].astype(str).apply('{:0>2}'.format)
df_census_raw['county'] = df_census_raw['county'].astype(str).apply('{:0>3}'.format)
df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'MPO', 'County FIPS', 'County Name']]
                                        , left_on = ['state', 'county']
                                        , right_on = ['State FIPS', 'County FIPS'])
df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
df_census_raw = df_census_raw.set_index(['state', 'MPO', 'county', 'County Name', 'Year']).reset_index()

