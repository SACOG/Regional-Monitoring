start_time = time.time()

# Import Census Bureau data to url mapping
df_urls = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = 'URL')

## For ACS tables
if sample_type == 'ACS':
  
    ## Import data and concatenate onto ID fields ##
    print("Importing and compiling ACS data from the Census Bureau...")
    print("")
    
    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties (or MSAs)
    # reduce all tables/variables pulled into one table

    list_df_census = []
    
    for table in tables:
    
        print("")
        print("Table ID: " + table)
        print("")
        list_df_tables = []
    
        df_table = df_vars[df_vars['Table'] == table]
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

        list_df_census.append(df_vars_all)
        print("All variables from table ID " + table + " have been reduced together into one table")
        print("")

    print("")
    print("Reducing all tables together into one final table...")
    print("")

    if geography == 'Places':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'place', 'Year']), list_df_census)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'place', 'Year']).reset_index()    
    if geography == 'Block Groups':
        df_census_raw = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'block group', 'Year']), list_df_census)
        df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                              , left_on = ['state', 'county']
                                              , right_on = ['State FIPS', 'County FIPS'])
        df_census_raw.drop(['State FIPS', 'County FIPS'], axis = 1, inplace = True)
        df_census_raw = df_census_raw.set_index(['NAME', 'state', 'county', 'County Name', 'tract', 'block group', 'Year']).reset_index()    
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



## For SUBJECT tables
if sample_type == 'SUBJECT':
    ## Import data and concatenate onto ID fields ##
    print("Importing and compiling ACS Subject data from the Census Bureau...")
    print("")
    
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
        list_df_vars.append(df_years)
    
    if geography == 'Tracts':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'tract', 'Year'], how = 'outer'), list_df_vars)
    if geography == 'Counties':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'state', 'county', 'Year'], how = 'outer'), list_df_vars)
    if geography == 'MSA':
        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = ['NAME', 'metropolitan statistical area/micropolitan statistical area', 'Year'], how = 'outer'), list_df_vars)
    list_df_census.append(df_vars_all)

    print("")
    print("Reducing all tables together into one final table...")
    print("")
    
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



## For DEC tables
if estimate == 'DEC':

    print("Importing and compiling Decennial data from the Census Bureau...")
    print("")

    # initialize empty list to store data frames
    # import multiple years and counties
    # iterate through each table and import all variables needed from each table
    # combine all years and counties
    # reduce all tables/variables pulled into one table
    
    list_df_census = []
    
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


## For PUMS tables
if geography == 'PUMA':
    
    print("Importing and compiling PUMS data from the Census Bureau...")
    print("")
    
    # initialize empty list to store data frames
    # import multiple years and PUMAs
    # import all variables
    # combine all years and PUMAs
    # outer join variables onto ID fields for each geography type
    # calculate margin of error using replicate weights
    
    for state in list(dict_fips.keys()):
        print('State: ' + state)
        list_df_years = []
        for year in years_to_import:
            print("")
            print('Year: ' + str(year))
            list_df_vars = []
            try:
                list_table_vars = [dict_vars[str(year)][x:x+45] for x in range(0, len(dict_vars[str(year)]), 45)]
                
                list_variables = []
                for x in list_table_vars:
                    list_variables.append(",".join(x))

                print('Querying variables...')
                for variables in tqdm(list_variables):
                    df_pums = query_census(df_urls       = df_urls
                                             , api_key   = api_key
                                             , estimate  = estimate
                                             , sample    = sample_type
                                             , geography = geography
                                             , variables = 'PUMA,SERIALNO,SPORDER,' + variables
                                             , year      = year
                                             , state     = state
                                             , puma      = dict_fips[state])
                    df_pums['state'] = state
                    df_pums = df_pums.drop(['public use microdata area'], axis = 1)
                    list_df_vars.append(df_pums)

                df_vars_years = ft.reduce(lambda left, right: pd.merge(left, right, on = ['state', 'SERIALNO', 'Year', 'PUMA', 'SPORDER'], how = 'left'), list_df_vars)
                df_vars_years = df_vars_years.set_index(['state', 'SERIALNO', 'Year', 'PUMA', 'SPORDER']).reset_index()
                df_vars_years.columns = ['state', 'SERIALNO', 'Year', 'PUMA', 'SPORDER'] + dict_vars[str(np.max(years_to_import))]
                if (table_type == 'H') & ('SPORDER' in df_vars_years.columns):
                    df_vars_years = df_vars_years[df_vars_years['SPORDER'] == '1']
                df_vars_years = df_vars_years.drop('SPORDER', axis = 1)
                if margin_of_error == 'Yes':
                    print('Calculating margin of error using replicate weights...')
                    cols = [col for col in df_vars_years.columns if weight in col]
                    df_vars_years[cols] = df_vars_years[cols].astype(int)
                    cols_to_drop = cols[:-1]
                    cols = list(df_vars_years.drop(cols_to_drop, axis = 1).columns)
                    df_me = pd.melt(df_vars_years
                                     , id_vars    = cols
                                     , var_name   = 'replicates'
                                     , value_name = 'replicate_weights')
                    df_me['sq_diff'] = (df_me['replicate_weights'] - df_me[weight])**2
                    df_me = df_me.groupby(cols, as_index = False)['sq_diff'].agg(sum)
                    df_me['variance'] = df_me['sq_diff']*(4/80)
                    df_me['SE'] = np.sqrt(df_me['variance'])
                    df_me['ME'] = df_me['SE']*1.645
                    df_me = df_me[cols + ['ME']].drop_duplicates()
                    df_vars_years = df_vars_years.drop(cols_to_drop, axis = 1)
                    df_vars_years = df_vars_years.drop_duplicates()
                    df_vars_years = df_vars_years.merge(df_me, on = cols, how = 'left')
                    df_vars_years = df_vars_years.drop_duplicates()
                list_df_years.append(df_vars_years)
                
                print('Success!')
                
            except Exception as e: print(e)
                                
    df_census_raw = pd.concat(list_df_years)


## For CPS tables
if estimate == 'CPS':

    
    print("Importing and compiling CPS data from the Census Bureau...")
    print("")
    
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


print("")
print("Finished!!")
print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")


print('')
print('Summary of data quality: ')
print('')
print("Count of '-555555555'   values in dataframe: " + str((df_census_raw.values == '-555555555'  ).sum()))
print("Count of '-666666666'   values in dataframe: " + str((df_census_raw.values == '-666666666'  ).sum()))
print("Count of '-999999999.0' values in dataframe: " + str((df_census_raw.values == '-999999999.0').sum()))
print("Count of 'null'         values in dataframe: " + str((df_census_raw.values == 'null'        ).sum()))
print("Count of '-'            values in dataframe: " + str((df_census_raw.values == '-'           ).sum()))
print("Count of ''             values in dataframe: " + str((df_census_raw.values == ''            ).sum()))
print("Count of NaN            values in dataframe: " + str(df_census_raw.isna().sum()              .sum()))


