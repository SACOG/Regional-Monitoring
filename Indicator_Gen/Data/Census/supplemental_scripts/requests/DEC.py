


version = 2



if version == 2:

    ## For DEC tables

    if geography == 'Places':
        geo_id = ['NAME', 'state', 'place']
    if geography == 'Block Groups':
        geo_id = ['NAME', 'state', 'county', 'tract', 'block group']
    if geography == 'Tracts':
        geo_id = ['NAME', 'state', 'county', 'tract']
    if geography == 'Counties':
        geo_id = ['NAME', 'state', 'county']
    if geography == 'MSA':
        geo_id = ['NAME', 'metropolitan statistical area/micropolitan statistical area']
    if geography == 'States':
        geo_id = ['NAME', 'state']


    print("Importing and compiling Decennial data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties
    # reduce all tables/variables pulled into one table

    list_df_years = []

    for year in tqdm(years_to_import):

        list_df_states = []

        if import_tab == 'Counties':
            for state in list(dict_fips.keys()):
                tqdm.write('State: ' + state)
                try:
                    list_df_states.append(
                        query_census(df_urls      = df_urls
                                      , api_key   = api_key
                                      , estimate  = estimate
                                      , sample    = sample_type
                                      , geography = geography
                                      , variables = ','.join(dict_vars[str(year)]) # Should I keep variable org like this?  Then just rename with latest ID names after each pull?  or should I adjust this to ACS style
                                      , year      = year
                                      , state     = state
                                      , county    = dict_fips[state])
                    )
                except Exception as e: print(e)

        if import_tab == 'States':
            for state in states_to_import:
                tqdm.write('State: ' + state)
                try:
                    list_df_states.append(
                        query_census(df_urls      = df_urls
                                      , api_key   = api_key
                                      , estimate  = estimate
                                      , sample    = sample_type
                                      , geography = geography
                                      , variables = ','.join(dict_vars[str(year)])
                                      , year      = year
                                      , state     = state)
                    )
                except Exception as e: print(e)

        df_states = pd.concat(list_df_states)
        df_states = df_states.set_index(geo_id + ['Year']).reset_index()
        df_states.columns = geo_id + ['Year'] + dict_vars2[str(year)][1:]
        list_df_years.append(df_states)
        
    df_census_raw = pd.concat(list_df_years)

    if geography == 'Counties':
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(geo_id + ['County Name', 'Year']).reset_index()













if version == 1:


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