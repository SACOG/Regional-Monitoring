
print("Preparing API request inputs...")


## Import Variable Mapping
df_inputs = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = import_tab)

# Set years
if year_start == 'timeseries':
    pass
else:
    years_to_import = list(range(year_start, year_end+1))

## For DEC data
if estimate == 'DEC':

    # Reset years to import for DEC
    # Set DEC variables to import
    # Import County FIPS mapping
    # Convert to dictionary object for easy state-county combination importing

    df_vars = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = estimate)
    df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    df_vars = df_vars[df_vars['Include'] == 'Yes']
    
    if margin_of_error == 'Yes':
        df_vars['ID_Attributes'] = df_vars['ID_Attributes'].apply(ME_split)

    years_to_import = [2000, 2010, 2020]
    
    dict_vars = {}
    for year in years_to_import:
        dict_vars[str(year)] = ['NAME'] + unique(df_vars[df_vars['Year'] == year]['ID'].to_list())
        
    df_fips = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                            , sheet_name = 'CountyFIPS'
                            , dtype = {'State FIPS': object, 'County FIPS': object})
    df_fips = df_fips[df_fips['State'].isin(df_inputs['states'].values)]
    dict_fips = df_fips[
                    (df_fips['State'].isin(df_inputs['states'].values))
                    & (df_fips['County Name'].isin(df_inputs['counties'].values))
    ]
    dict_fips = dict_fips[['State FIPS', 'County FIPS']]
    dict_fips = dict_fips.groupby('State FIPS')['County FIPS'].apply(list).to_dict()
    
    for key in list(dict_fips.keys()):
        dict_fips[key] = ",".join(dict_fips[key])
    
    # view
    print('')
    print('Counties set to import by state:')
    print(dict_fips)
    print('')
    print('Variables set to import by year:')
    print(dict_vars)

## For ACS1 or ACS5 data
if sample_type in ['ACS', 'SUBJECT']:

    df_vars = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = sample_type)
    df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    df_vars = df_vars[df_vars['Include'] == 'Yes']
    
    # Set tables and variables to import

    if margin_of_error == 'Yes':
        df_vars['ID_Attributes'] = df_vars['ID_Attributes'].apply(ME_split)
        list_vars = ['NAME'] + df_vars['ID_Attributes'].to_list()
    else:
        list_vars = ['NAME'] + df_vars['ID'].to_list()

    if sample_type == 'ACS':
        tables = df_vars['Table'].unique()
        print("")
        print("Tables set to import:")
        print(tables)

    # For tract and county level pull
    if import_tab == 'Counties':
        
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing
        df_fips = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                                , sheet_name = 'CountyFIPS'
                                , dtype = {'State FIPS': object, 'County FIPS': object})
        df_fips = df_fips[
                        (df_fips['State'].isin(df_inputs['states'].values))
                        & (df_fips['County Name'].isin(df_inputs['counties'].values))
        ]
        dict_fips = df_fips.copy()
        dict_fips = dict_fips[['State FIPS', 'County FIPS']]
        dict_fips = dict_fips.groupby('State FIPS')['County FIPS'].apply(list).to_dict()
        
        for key in list(dict_fips.keys()):
            dict_fips[key] = ",".join(dict_fips[key])
    
        # view
        print('')
        print('Counties set to import by state:')
        print(dict_fips)
        print('')
        print('Variables set to import:')
        print(list_vars)

    
    # For MSA level pull
    if import_tab == 'MSA':
    
        # Set MSAs to import
        df_inputs['msa'] = df_inputs['msa'].astype("string")
        msa_to_import = df_inputs['msa'].values
        msa_to_import = ",".join(msa_to_import)
    
        # view
        print("")
        print("MSA IDs set to import:")
        print(msa_to_import)
        print("")
        print("List of variables to import:")
        print(list_vars)


## For PUMS data
if sample_type == 'PUMS':

    # Remove 2012-2015 if pulling PUMS tables (they only reported at the state level for PUMS on these years)
    # Create dictionary of variable mappings by year (sometimes the variable name changes over time)
    # Import County FIPS mapping
    # Convert to dictionary object for easy state-county combination importing
    df_vars = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = sample_type)
    df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
    df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    if 'H' in df_vars['Table Type'].unique():
        table_type = 'H'
        weight = 'WGTP'
    else:
        table_type = 'P'
        weight = 'PWGTP'

    print('')
    print('PUMS table roll up: ' + table_type)

    if margin_of_error == 'Yes':
        df_vars.loc[(df_vars['ID'].str.contains('WGTP')) & (df_vars['Table Type'] == table_type), 'Include'] = 'Yes'
    
    df_vars = df_vars[df_vars['Include'] == 'Yes']
        
    groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
    groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

    print('')
    print('PUMS variables to group by: ')
    print(groups)
    print('')
    print('PUMS variables to group by (excluding integer based groups): ')
    print(groups2)
    
    df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
            
    dict_vars = {}
    for year in years_to_import:
        dict_vars[str(year)] = unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'].str.contains('group'))]['ID'].to_list()) + unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'] == 'integer')]['ID'].to_list()) + [weight]
        
    df_fips = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                            , sheet_name = 'CountyFIPS'
                            , dtype = {'State FIPS': object, 'County FIPS': object})
    df_fips_pums = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                                 , sheet_name = 'PUMAcodes'
                                 , dtype = {'STATEFP': object, 'COUNTYFP': object, 'TRACTCE': object, 'PUMA5CE': object})
    df_fips_pums = df_fips_pums.rename(columns = {'STATEFP':'State FIPS', 'COUNTYFP':'County FIPS'})

    df_fips = df_fips.merge(df_fips_pums[['State FIPS', 'County FIPS', 'PUMA5CE']].drop_duplicates(), on = ['State FIPS', 'County FIPS'])
    df_fips = df_fips[df_fips['State'].isin(df_inputs['states'].values)]
    dict_fips = df_fips[
                    (df_fips['State'].isin(df_inputs['states'].values))
                    & (df_fips['County Name'].isin(df_inputs['counties'].values))
    ]
    dict_fips = dict_fips[['State FIPS', 'PUMA5CE']].drop_duplicates()
    
    dict_fips = dict_fips.groupby('State FIPS')['PUMA5CE'].apply(list).to_dict()
    
    for key in list(dict_fips.keys()):
        dict_fips[key] = ",".join(dict_fips[key])

    # view
    print('')
    print("PUMA's set to import by state: ")
    print(dict_fips)
    print('')
    print('Variables set to import by year:')
    print(dict_vars)



if estimate == 'CPS':
    
    df_vars = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = sample_type)
    df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
    df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    df_vars = df_vars[df_vars['Include'] == 'Yes']
    if 'H' in df_vars['Table Type'].unique():
        table_type = 'H'
        weight = 'HHSUPWGT'
    else:
        table_type = 'P'
        weight = 'PWSSWGT'
        
    
    dict_vars = {}
    for year in years_to_import:
        dict_vars[str(year)] = unique(df_vars[df_vars['Year'] == year]['ID'].to_list()) + [weight]
    
    # Import County FIPS mapping
    # Convert to dictionary object for easy state-county combination importing
    df_fips = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                            , sheet_name = 'CountyFIPS'
                            , dtype = {'State FIPS': object, 'County FIPS': object})
    
    df_fips = df_fips[
                    (df_fips['State'].isin(df_inputs['states'].values))
                    & (df_fips['County Name'].isin(df_inputs['counties'].values))
    ]
    dict_fips = df_fips.copy()
    dict_fips = dict_fips[['State FIPS', 'County FIPS']]
    dict_fips = dict_fips.groupby('State FIPS')['County FIPS'].apply(list).to_dict()
    
    for key in list(dict_fips.keys()):
        dict_fips[key] = ",".join(dict_fips[key])
        
    # view
    print(dict_fips)
    print(dict_vars)



if estimate == 'LEHD':
    df_vars = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = estimate)
    df_vars = df_vars[df_vars['Sample'] == sample_type]
    df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    df_vars = df_vars[df_vars['Include'] == 'Yes']
    variables = df_vars['ID'].unique()
    variables = ','.join(variables)
    # if sample_type == 'RH':
    #     variables = 'race,' + variables
    # if sample_type == 'SA':
    #     variables = 'agegrp,' + variables
    # if sample_type == 'SE':
    #     variables = 'sex,' + variables
    print("")
    print("Variables set to import:")
    print(variables)
    print('')

    # For county level pull
    if import_tab == 'Counties':
        
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing
        df_fips = pd.read_excel(os.path.join(path_git, 'config', 'Area Codes.xlsx')
                                , sheet_name = 'CountyFIPS'
                                , dtype = {'State FIPS': object, 'County FIPS': object})
        df_fips = df_fips[
                        (df_fips['State'].isin(df_inputs['states'].values))
                        & (df_fips['County Name'].isin(df_inputs['counties'].values))
        ]
        dict_fips = df_fips.copy()
        dict_fips = dict_fips[['State FIPS', 'County FIPS']]
        dict_fips = dict_fips.groupby('State FIPS')['County FIPS'].apply(list).to_dict()
        
        for key in list(dict_fips.keys()):
            dict_fips[key] = ",".join(dict_fips[key])
    
        # view
        print('')
        print('Counties set to import by state:')
        print(dict_fips)
        print('')

        # For MSA level pull
    if import_tab == 'MSA':
    
        # Set MSAs to import
        df_inputs['msa'] = df_inputs['msa'].astype("string")
        msa_to_import = df_inputs['msa'].values
        msa_to_import = ",".join(msa_to_import)
    
        # view
        print("")
        print("MSA IDs set to import:")
        print(msa_to_import)
        print("")
        print("List of variables to import:")
        print(list_vars)


# view
print('')
print('Variable Mapping table:')
df_vars.head(3)