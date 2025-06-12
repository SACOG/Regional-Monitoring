
version = 2






if version == 2:
    ## For SUBJECT tables


    if geography == 'Tracts':
        geo_id = ['NAME', 'state', 'county', 'tract']
    if geography == 'Counties':
        geo_id = ['NAME', 'state', 'county']
    if geography == 'MSA':
        geo_id = ['NAME', 'metropolitan statistical area/micropolitan statistical area']
    if geography == 'States':
        geo_id = ['NAME', 'state']

    print("Importing and compiling ACS Subject data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    file_vars = path_config / 'census_configuration_file2.xlsx'
    df_vars = pd.read_excel(file_vars, sheet_name=sample_type)

    list_df_years = []

    for year in tqdm(years_to_import):
        try:
            df_vars2 = df_vars.copy()
            df_vars2 = df_vars2[df_vars2['Year'] == year]
            df_vars2 = df_vars2[(df_vars2['Indicator Name'].str.contains(f'{indicator}$', regex=True).replace(np.nan, False)) | (df_vars2['Indicator Name'].str.contains(f'{indicator},', regex=True).replace(np.nan, False))]
            df_vars2 = df_vars2[df_vars2['Include'] == 'Yes']

            if margin_of_error == 'Yes':
                list_table_vars  = [['NAME'] + df_vars2['ID_Attributes' ].to_list()[x:x+20] for x in range(0, len(df_vars2['ID_Attributes' ].to_list()), 20)]
                list_table_vars2 = [['NAME'] + df_vars2['ID_Attributes2'].to_list()[x:x+20] for x in range(0, len(df_vars2['ID_Attributes2'].to_list()), 20)]
            else:
                list_table_vars  = [['NAME'] + df_vars2['ID' ].to_list()[x:x+45] for x in range(0, len(df_vars2['ID' ].to_list()), 45)]
                list_table_vars2 = [['NAME'] + df_vars2['ID2'].to_list()[x:x+45] for x in range(0, len(df_vars2['ID2'].to_list()), 45)]


            list_variables  = []
            list_variables2 = []
            for x, y in zip(list_table_vars, list_table_vars2):
                list_variables.append(",".join(x))
                y.remove('NAME')
                y2 = []
                for ii in y:
                    ii = ii.split(',')
                    y2 = y2 + ii
                list_variables2.append(y2)


            list_df_vars = []

            for variables, variables2 in zip(list_variables, list_variables2):

                list_df_states = []
                tqdm.write("Variables: " + variables)

                if import_tab == 'Counties':
                    for state in list(dict_fips.keys()):
                        tqdm.write('State: ' + state)
                        try:
                            list_df_states.append(
                                query_census(df_urls        = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state
                                                , county    = dict_fips[state])
                            )
                        except Exception as e: print(e)
                                
                if import_tab == 'MSA':
                    try:
                        list_df_states.append(
                            query_census(df_urls        = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year
                                            , msa       = msa_to_import)
                        )
                    except Exception as e: print(e)

                if import_tab == 'States':
                    for state in states_to_import:
                        tqdm.write('State: ' + state)
                        try:
                            list_df_states.append(
                                query_census(df_urls        = df_urls
                                                , api_key   = api_key
                                                , estimate  = estimate
                                                , sample    = sample_type
                                                , geography = geography
                                                , variables = variables
                                                , year      = year
                                                , state     = state)
                            )
                        except Exception as e: print(e)

                df_states = pd.concat(list_df_states)
                df_states = df_states.set_index(geo_id + ['Year']).reset_index()
                df_states.columns = geo_id + ['Year'] + variables2
                list_df_vars.append(df_states)

            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_vars)
            list_df_years.append(df_vars_all)

        except Exception as e: print(e)


    print()
    print("Reducing all tables together into one final table...")
    print()

    df_census_raw = pd.concat(list_df_years)
    if geography == 'Tracts':
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw = df_census_raw.drop(['State FIPS', 'County FIPS'], axis=1)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'tract', 'Year']).reset_index()
    if geography == 'Counties':
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw = df_census_raw.drop(['State FIPS', 'County FIPS'], axis=1)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'Year']).reset_index()
    if geography == 'MSA':
        df_census_raw = df_census_raw.set_index(['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year']).reset_index()
    if geography == 'States':
        df_census_raw = df_census_raw.set_index(['NAME', 'state','Year']).reset_index()





if version == 1:
    ## For SUBJECT tables

    print("Importing and compiling ACS Subject data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    list_df_census = []
    if margin_of_error == 'Yes':
        list_table_vars = [['NAME'] + df_vars['ID_Attributes'].to_list()[x:x+20] for x in range(0, len(df_vars['ID_Attributes'].to_list()), 20)]
    else:
        list_table_vars = [['NAME'] + df_vars['ID'].to_list()[x:x+45] for x in range(0, len(df_vars['ID'].to_list()), 45)]

    list_variables = []
    for x in list_table_vars:
        list_variables.append(",".join(x))

    list_df_vars = []

    for variables in list_variables:
        print("Variables: " + variables)
        list_df_years = []
        if import_tab == 'Counties':
            for state in list(dict_fips.keys()):
                print('State: ' + state)
                for year in tqdm(years_to_import):
                    try:
                        list_df_years.append(
                            query_census(df_urls      = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year
                                            , state     = state
                                            , county    = dict_fips[state])
                        )
                    except Exception as e: print(e)
            df_years = pd.concat(list_df_years)
                        
        if import_tab == 'MSA':
            for year in tqdm(years_to_import):
                try:
                    list_df_years.append(
                        query_census(df_urls      = df_urls
                                        , api_key   = api_key
                                        , estimate  = estimate
                                        , sample    = sample_type
                                        , geography = geography
                                        , variables = variables
                                        , year      = year
                                        , msa       = msa_to_import)
                    )
                except Exception as e: print(e)
            df_years = pd.concat(list_df_years)

        if import_tab == 'States':
            for state in states_to_import:
                print('State: ' + state)
                for year in tqdm(years_to_import):
                    try:
                        list_df_years.append(
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
            df_years = pd.concat(list_df_years)

        list_df_vars.append(df_years)

    if geography == 'Tracts':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'Year'], how = 'outer'), list_df_vars)
    if geography == 'Counties':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'Year'], how = 'outer'), list_df_vars)
    if geography == 'MSA':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year'], how = 'outer'), list_df_vars)
    if geography == 'States':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'Year'], how = 'outer'), list_df_vars)
    list_df_census.append(df_vars_all)

    print()
    print("Reducing all tables together into one final table...")
    print()

    if geography == 'Tracts':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'Year']), list_df_census)
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'tract', 'Year']).reset_index()
    if geography == 'Counties':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'Year']), list_df_census)
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'Year']).reset_index()
    if geography == 'MSA':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year']), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year']).reset_index()
    if geography == 'States':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state','Year']).reset_index()

