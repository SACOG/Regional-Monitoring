
## LEHD

print("Importing and compiling LEHD data from the Census Bureau...")
print("")

list_df_states = []
if import_tab == 'Counties':

    print('Importing by state: ' + ', '.join(list(dict_fips.keys())))
    for state in tqdm(list(dict_fips.keys())):
        try:
            df_census_raw = query_census(df_urls      = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = 'year,'+variables
                                            , year      = 'timeseries'
                                            , state     = state
                                            , county    = dict_fips[state])
            df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                            , left_on = ['state', 'county']
                                            , right_on = ['State FIPS', 'County FIPS'])
            df_census_raw = df_census_raw.drop(['state', 'county'], axis = 1)
            df_census_raw = df_census_raw.set_index(['State FIPS', 'County FIPS', 'County Name', 'year', 'time']).reset_index()
            list_df_states.append(df_census_raw)
        except Exception as e: print(e)

if import_tab == 'MSA':

    print('Importing by state: ' + ', '.join(list(dict_fips.keys())))
    for state in tqdm(list(dict_fips.keys())):
        try:
            df_census_raw = query_census(df_urls      = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = 'year,'+variables
                                            , year      = 'timeseries'
                                            , state     = state
                                            , msa       = dict_fips[state])
            df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'MSA_ID', 'MSA']]
                                                , left_on = ['state', 'metropolitan statistical area/micropolitan statistical area']
                                                , right_on = ['State FIPS', 'MSA_ID'])
            df_census_raw = df_census_raw.drop(['state', 'metropolitan statistical area/micropolitan statistical area'], axis = 1)
            df_census_raw = df_census_raw.set_index(['State FIPS', 'MSA_ID', 'MSA', 'time']).reset_index()
            list_df_states.append(df_census_raw)
        except Exception as e: print(e)
df_census_raw = pd.concat(list_df_states)
df_census_raw = df_census_raw.rename(columns = {'year':'Year'})


