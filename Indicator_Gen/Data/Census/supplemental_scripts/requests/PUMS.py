
## For PUMS tables

print("Importing and compiling PUMS data from the Census Bureau...")
print()

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
        print()
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
                df_vars_years[cols] = df_vars_years[cols].replace('', np.nan)
                df_vars_years[cols] = df_vars_years[cols].astype(int)
                cols_to_drop = cols[:-1]
                cols = list(df_vars_years.drop(cols_to_drop, axis = 1).columns)
                df_me = pd.melt(df_vars_years
                                    , id_vars    = cols
                                    , var_name   = 'replicates'
                                    , value_name = 'replicate_weights')
                df_me['sq_diff'] = (df_me['replicate_weights'] - df_me[weight])**2
                df_me = df_me.groupby(cols, as_index = False)['sq_diff'].agg('sum') # Change from sum to 'sum'
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

