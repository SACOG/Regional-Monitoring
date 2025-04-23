## For ACS tables

## Import data and concatenate onto ID fields ##
print(); print()
print("Importing and compiling ACS data from the Census Bureau...")
print()

# initialize empty list to store data frames
# import multiple years and counties
# iterate through each table and import all variables needed from each table
# combine all years and counties (or MSAs)
# reduce all tables/variables pulled into one table

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
if geography == 'Congressional Districts':
    geo_id = ['NAME', 'state', 'congressional district']
if geography == 'State Legislative Upper Districts':
    geo_id = ['NAME', 'state', 'state legislative district (upper chamber)']
if geography == 'State Legislative Lower Districts':
    geo_id = ['NAME', 'state', 'state legislative district (lower chamber)']
if geography == 'States':
    geo_id = ['NAME', 'state']
if geography == 'National':
    geo_id = ['NAME', 'us']


list_df_years = []

# for year in tqdm(years_to_import, position=0, leave=True):
for year in tqdm(years_to_import, position=0):
    tqdm.write("")
    tqdm.write(f'Year: {year}')
    list_df_tables = []

    for table in tables:

        tqdm.write("")
        tqdm.write("Table ID: " + table)

        df_table = df_vars[(df_vars['Table'] == table) & (df_vars['Year'] == 2023)]
        if margin_of_error == 'Yes':
            list_table_vars = [['NAME'] + df_table['ID_Attributes'].to_list()[x:x+24] for x in range(0, len(df_table['ID_Attributes'].to_list()), 24)]
        else:
            list_table_vars = [['NAME'] + df_table['ID'].to_list()[x:x+45] for x in range(0, len(df_table['ID'].to_list()), 48)]
        
        list_variables = []
        for x in list_table_vars:
            list_variables.append(",".join(x))

        list_df_vars = []
                
        for variables in list_variables:
            tqdm.write("Variables: " + variables)

            if geography != 'MSA':
                list_df_states = []
                if import_tab != 'States':
                    states_to_import = list(dict_fips.keys())
                for state in states_to_import:
                    if geography in ['Block Groups', 'Tracts', 'Counties']:
                        counties = dict_fips[state]
                    tqdm.write('State: ' + state)
                    c = Census(api_key, year=year)
                    params = set_parameters(geography=geography, year=year)
                    if estimate == 'ACS5':
                        result = c.acs5.get(('NAME', variables), params)
                    else:
                        result = c.acs1.get(('NAME', variables), params)
                    df_state = pd.DataFrame(result)
                    list_df_states.append(df_state)
                df_states = pd.concat(list_df_states)
                 
            if geography == 'MSA':
                msa = df_fips[df_fips['Year'] == year]
                msa = list(msa['MSA_ID'].values)
                msa = ','.join(msa)
                c = Census(api_key, year=year)
                params = set_parameters(geography=geography, year=year)
                result = c.acs5.get(('NAME', variables), params)
                df_states = pd.DataFrame(result)

            list_df_vars.append(df_states)

        df_vars_all = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id, how = 'outer'), list_df_vars)
        list_df_tables.append(df_vars_all)

    
    tqdm.write(""); tqdm.write("All variables from table ID " + table + " have been reduced together into one table"); tqdm.write("")

    df_year = ft.reduce(lambda left, right: pd.merge(left, right, on = geo_id, how = 'outer'), list_df_tables)
    df_year['Year'] = year
    list_df_years.append(df_year)

print(); print("Reducing all tables together into one final table..."); print()

df_census_raw = pd.concat(list_df_years)

df_census_raw = df_census_raw.set_index(geo_id + ['Year']).reset_index()
if geography in ['Block Groups', 'Tracts', 'Counties']:
    df_census_raw = df_census_raw.merge(df_fips[['State FIPS', 'County FIPS', 'County Name']]
                                            , left_on = ['state', 'county']
                                            , right_on = ['State FIPS', 'County FIPS'])
    df_census_raw.drop(['State FIPS', 'County FIPS'], axis=1, inplace=True)
    df_census_raw = move_column_after(df_census_raw, 'County Name', 'county')
