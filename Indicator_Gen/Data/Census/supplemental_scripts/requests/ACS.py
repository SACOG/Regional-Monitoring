

version = 2




if version == 2:

    ## For ACS tables

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

    ## Import data and concatenate onto ID fields ##
    print("Importing and compiling ACS data from the Census Bureau...")
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

        list_df_tables = []
        
        for table in tables:

            tqdm.write('')
            tqdm.write("Table ID: " + table)
            tqdm.write('')

            df_table = df_vars[((df_vars['Indicator Name'].str.contains(f'{indicator}$', regex=True).replace(np.nan, False)) | (df_vars['Indicator Name'].str.contains(f'{indicator},', regex=True).replace(np.nan, False)))
                               & (df_vars['Table'] == table) & (df_vars['Year'] == year)]
            if margin_of_error == 'Yes':
                list_table_vars  = [['NAME'] + df_table['ID_Attributes'] .to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes' ].to_list()), 20)]
                list_table_vars2 = [['NAME'] + df_table['ID_Attributes2'].to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes2'].to_list()), 20)]
            else:
                list_table_vars  = [['NAME'] + df_table['ID' ].to_list()[x:x+45] for x in range(0, len(df_table['ID' ].to_list()), 45)]
                list_table_vars2 = [['NAME'] + df_table['ID2'].to_list()[x:x+45] for x in range(0, len(df_table['ID2'].to_list()), 45)]
            
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

                tqdm.write("Variables: " + variables)
                list_df_states = []

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
                        msa_to_import = df_fips[df_fips['Year'] == year]
                        msa_to_import = list(msa_to_import['MSA_ID'].values)
                        msa_to_import = ','.join(msa_to_import)
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

                if import_tab == 'National':
                    try:
                        list_df_states.append(
                            query_census(df_urls        = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year)
                        )
                    except Exception as e: print(e)

                df_states = pd.concat(list_df_states)
                df_states = df_states.set_index(geo_id + ['Year']).reset_index()
                df_states.columns = geo_id + ['Year'] + variables2
                list_df_vars.append(df_states)

            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how='outer'), list_df_vars)

            list_df_tables.append(df_vars_all)
            tqdm.write("All variables from table ID " + table + " have been reduced together into one table")
            tqdm.write('')

        tqdm.write('')
        tqdm.write("Reducing all tables together into one final table...")
        tqdm.write('')

        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id + ['Year'], how = 'outer'), list_df_tables)
        df_census_raw = df_census_raw.set_index(geo_id + ['Year']).reset_index()
        if geography in ['Block Groups', 'Tracts', 'Counties']:
            df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                    , left_on = ['state', 'county']
                                                    , right_on = ['State FIPS', 'County FIPS'])
            df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
            df_census_raw = df_census_raw.set_index(geo_id + ['Year']).reset_index()
        if geography == 'National':
            df_census_raw = df_census_raw.drop('us', axis=1)


        list_df_years.append(df_census_raw)

    df_census_raw = pd.concat(list_df_years)
    df_census_raw = df_census_raw.drop_duplicates()
    display(df_census_raw.head())




if version == 1:

    ## For ACS tables

    ## Import data and concatenate onto ID fields ##
    print("Importing and compiling ACS data from the Census Bureau...")
    print()

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    list_df_census = []

    for table in tables:

        print()
        print("Table ID: " + table)
        print()
        list_df_tables = []

        df_table = df_vars[(df_vars['Table'] == table) & (df_vars['Year'] == 2023)]
        if margin_of_error == 'Yes':
            list_table_vars = [['NAME'] + df_table['ID_Attributes'].to_list()[x:x+20] for x in range(0, len(df_table['ID_Attributes'].to_list()), 20)]
        else:
            list_table_vars = [['NAME'] + df_table['ID'].to_list()[x:x+45] for x in range(0, len(df_table['ID'].to_list()), 45)]
        
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
                        msa_to_import = df_fips[df_fips['Year'] == year]
                        msa_to_import = list(msa_to_import['MSA_ID'].values)
                        msa_to_import = ','.join(msa_to_import)
                        list_df_years.append(
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

            if import_tab == 'National':
                for year in tqdm(years_to_import):
                    try:
                        list_df_years.append(
                            query_census(df_urls      = df_urls
                                            , api_key   = api_key
                                            , estimate  = estimate
                                            , sample    = sample_type
                                            , geography = geography
                                            , variables = variables
                                            , year      = year)
                        )
                    except Exception as e: print(e)
                df_years = pd.concat(list_df_years)

            list_df_vars.append(df_years)

        if geography == 'Places':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'place', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'Block Groups':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'block group', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'Tracts':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'Counties':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'MSA':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'Congressional Districts':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'congressional district', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'State Legislative Upper Districts':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'state legislative district (upper chamber)', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'State Legislative Lower Districts':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'state legislative district (lower chamber)', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'States':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'Year'], how = 'outer'), list_df_vars)
        if geography == 'National':
            df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'us', 'Year'], how = 'outer'), list_df_vars)

        list_df_census.append(df_vars_all)
        print("All variables from table ID " + table + " have been reduced together into one table")
        print()

    print()
    print("Reducing all tables together into one final table...")
    print()

    if geography == 'Places':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'place', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'place', 'Year']).reset_index()    
    if geography == 'Block Groups':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'block group', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'tract', 'block group', 'Year']).reset_index()    
    if geography == 'Tracts':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'tract', 'Year']).reset_index()
    if geography == 'Counties':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                                , left_on = ['state', 'county']
                                                , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'Year']).reset_index()
    if geography == 'MSA':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year']).reset_index()
    if geography == 'Congressional Districts':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'congressional district', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'congressional district', 'Year']).reset_index()
    if geography == 'State Legislative Upper Districts':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'state legislative district (upper chamber)', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'state legislative district (upper chamber)', 'Year']).reset_index()
    if geography == 'State Legislative Lower Districts':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'state legislative district (lower chamber)', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'state legislative district (lower chamber)', 'Year']).reset_index()
    if geography == 'States':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state','Year']).reset_index()
    if geography == 'National':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'us', 'Year'], how = 'outer'), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'us', 'Year']).reset_index()
        df_census_raw = df_census_raw.drop('us', axis=1)
