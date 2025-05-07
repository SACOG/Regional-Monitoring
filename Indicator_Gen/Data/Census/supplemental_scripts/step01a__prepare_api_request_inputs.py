
version = 2


if version == 2:
    print(); print()
    print('Census Bureau import parameters:')
    print()


    path_yaml = path_config0 / 'config_indicators.yaml'
    
    try:
        with open(path_yaml, 'r') as yaml_file:
            dict_config = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    
    if rerun:
        path_runs = path_config / 'runs'
        list_files = [str(entry) for entry in path_runs.iterdir() if entry.is_file()]
        dict_mod = {}

        for file in list_files:
            time_mod = os.path.getmtime(file)
            time_mod = datetime.fromtimestamp(time_mod).strftime("%Y-%m-%d %H:%M:%S")
            dict_mod[time_mod] = file

        most_recent = sorted(list(dict_mod.keys()), reverse=True)[0]
        file_run = dict_mod[most_recent]
        df_run = pd.read_csv(file_run, sep=': ', names=['Parameter', 'Input'])
        print(); display(df_run); print()

        def remove_colon(x):
            return x.replace(':', '')

        df_run['Parameter'] = df_run['Parameter'].apply(remove_colon)
        project         = df_run[df_run['Parameter'] == 'Project'        ]['Input'].values[0]
        indicator       = df_run[df_run['Parameter'] == 'Indicator Name' ]['Input'].values[0]
        sample_type     = df_run[df_run['Parameter'] == 'Sample'         ]['Input'].values[0]
        estimate        = df_run[df_run['Parameter'] == 'Estimate'       ]['Input'].values[0]
        geography       = df_run[df_run['Parameter'] == 'Geography'      ]['Input'].values[0]
        years_to_import = df_run[df_run['Parameter'] == 'Years Imported' ]['Input'].values[0]
        import_tab      = df_run[df_run['Parameter'] == 'Import Tab'     ]['Input'].values[0]
        margin_of_error = df_run[df_run['Parameter'] == 'Margin of Error']['Input'].values[0]
        export_loc  = dict_config['Indicators'][project][indicator]['sp_location'        ]
        folder      = dict_config['Indicators'][project][indicator]['folder'             ]
        MOE_thresh  = dict_config['Indicators'][project][indicator]['MOE_threshold'      ]
        num_vars    = dict_config['Indicators'][project][indicator]['number_of_variables']
        percentages = dict_config['Indicators'][project][indicator]['percentages'        ]
        weighted_by = dict_config['Indicators'][project][indicator]['weighted_by'        ]
        metric      = dict_config['Indicators'][project][indicator]['metric'             ]
        years_to_import = years_to_import.split(', ')
        years_to_import = [int(year) for year in years_to_import]
        year_end   = np.max(years_to_import)
        year_start = np.min(years_to_import)


    else:

        print('---------------------------------------------------------------------------------------------------------------------------------------')
        print()
        print('Projects available: ')
        display(dict_config['Project']); print()
        print('Which project are you pulling data for?'); print()
        project = input()
        assert project in dict_config['Project'], 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()
        print('Indicators available:'); print()
        display(list(dict_config['Indicators'][project].keys())); print()
        print('Which indicator do you need to rerun?'); print()
        indicator = input()
        assert indicator in list(dict_config['Indicators'][project].keys()), 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        export_loc  = dict_config['Indicators'][project][indicator]['sp_location'        ]
        folder      = dict_config['Indicators'][project][indicator]['folder'             ]
        MOE_thresh  = dict_config['Indicators'][project][indicator]['MOE_threshold'      ]
        num_vars    = dict_config['Indicators'][project][indicator]['number_of_variables']
        percentages = dict_config['Indicators'][project][indicator]['percentages'        ]
        weighted_by = dict_config['Indicators'][project][indicator]['weighted_by'        ]
        metric      = dict_config['Indicators'][project][indicator]['metric'             ]

        print()
        display(dict_config['Indicators'][project][indicator])
        sample_types = dict_config['Indicators'][project][indicator]['sample']
        if isinstance(sample_types, list):
            print('Samples available:')
            display(sample_types); print()
            print('Which sample do you want to pull data from?')
            sample_type = input()
            assert sample_type in sample_types, 'Unacceptable input, please choose from options displayed above'
        else:
            sample_type = dict_config['Indicators'][project][indicator]['sample']

        print()
        print('Estimates available:')
        display(list(dict_config['Samples'][sample_type].keys())); print()
        print('Which estimate do you want to pull data from?'); print()
        estimate = input()
        assert estimate in list(dict_config['Samples'][sample_type].keys()), 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')


        print()
        print('Geographies available:'); print()
        display(dict_config['Samples'][sample_type][estimate]['geographies_available']); print()
        print('Which geography do you want to pull data for?'); print()
        geography = input()
        assert geography in dict_config['Samples'][sample_type][estimate]['geographies_available'], 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()
        print('Years available:')
        display(dict_config['Samples'][sample_type][estimate]['years_available']); print()
        print('Do you want to pull data for all years available?  Select Yes/No: '); print()
        all_years = input()
        if all_years == 'Yes':
            years_to_import = dict_config['Samples'][sample_type][estimate]['years_available']
            years = ', '.join([str(year) for year in years_to_import])
        elif all_years == 'No':
            print()
            print('Please type which years you want to pull data from, separated by commas:'); print()
            years = input()
            if ',' in years:
                years_to_import = years.split(', ')
                years_to_import = [int(year) for year in years_to_import]
            else:
                years_to_import = [int(years)]
        else:
            assert all_years in ['Yes', 'No'], "Unacceptable input, please type 'Yes' or 'No'"

            
        print()
        year_end   = np.max(years_to_import)
        year_start = np.min(years_to_import)
        import_tab = dict_config['Import Geographies'][geography]

        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()
        print('Do you want to pull the Margin of Error estimates?  Select Yes/No: '); print()
        margin_of_error = input()
        assert margin_of_error in ['Yes', 'No'], "Unacceptable input, please type 'Yes' or 'No'"

        file_config_set = path_config / 'runs' / f'{indicator}.txt'
        with open(file_config_set, 'w') as f:
            f.write(f"Project: {project}\n")
            f.write(f"Indicator Name: {indicator}\n")
            f.write(f"Export Location: {export_loc}\n")
            f.write(f"Folder: {folder}\n")
            f.write(f"Sample: {sample_type}\n")
            f.write(f"Estimate: {estimate}\n")
            f.write(f"Geography: {geography}\n")
            f.write(f"Years Imported: {years}\n")
            f.write(f"Import Tab: {import_tab}\n")
            f.write(f"Margin of Error: {margin_of_error}\n")






## ---------------------------------------------------------------------------------------------------------------------------------------------------

    print()
    print()
    print("API request inputs:")
    print()


    ## Import Variable Mapping
    df_inputs = pd.read_excel(os.path.join(path_config, 'census_configuration_file2.xlsx'), sheet_name = import_tab)


    ## For DEC data
    if estimate == 'DEC':

        # Reset years to import for DEC
        # Set DEC variables to import
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing

        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file2.xlsx'), sheet_name = estimate)
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_vars = df_vars[df_vars['Include'] == 'Yes']

        if margin_of_error == 'Yes':
            df_vars['ID_Attributes'] = df_vars['ID_Attributes'].apply(ME_split)
            list_vars = ['NAME'] + df_vars['ID_Attributes'].to_list()
        else:
            list_vars = ['NAME'] + df_vars['ID'].to_list()
                
        dict_vars = {}
        for year in years_to_import:
            dict_vars[str(year)] = ['NAME'] + unique(df_vars[df_vars['Year'] == year]['ID'].to_list())
            
        if import_tab == 'Counties':
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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
            print()
            print('Counties set to import by state:')
            print(dict_fips)
            print()
            print('Variables set to import by year:')
            print(dict_vars)

        # For State level pull
        if import_tab == 'States':
        
            # Set MSAs to import
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                    , sheet_name = 'CountyFIPS'
                                    , dtype = {'State FIPS': object, 'County FIPS': object})
            df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values))]
            states_to_import = list(df_fips['State FIPS'].unique())
            states_to_import = [str(state) for state in states_to_import]
        
            # view
            print()
            print("States set to import:")
            print(states_to_import)
            print()
            print("List of variables to import:")
            print(list_vars)



    ## For ACS1 or ACS5 data
    if sample_type in ['ACS', 'SUBJECT']:

        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file2.xlsx'), sheet_name=sample_type)
        df_vars = df_vars[df_vars['Year'] == 2023]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_vars = df_vars[df_vars['Include'] == 'Yes']
        
        # Set tables and variables to import

        if margin_of_error == 'Yes':
            df_vars['ID_Attributes'] = df_vars['ID_Attributes'].apply(ME_split)
            list_vars = ['NAME'] + df_vars['ID_Attributes'].to_list()
        else:
            list_vars = ['NAME'] + df_vars['ID'].to_list()

        if sample_type == 'ACS':
            tables = df_vars['Table'].unique()
            print()
            print("Tables set to import:")
            print(tables)

        # For tract and county level pull
        if import_tab == 'Counties':
            
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                    , sheet_name = 'CountyFIPS'
                                    , dtype = {'State FIPS': str, 'County FIPS': str})
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
            print()
            print('Counties set to import by state:')
            print(dict_fips)
            print()
            print('Variables set to import:')
            print(list_vars)

        # For MSA level pull
        if import_tab == 'MSA':
        
            # Set MSAs to import
            msa_to_import = list(df_inputs['msa'].values)
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx'), sheet_name='MSAcodes', dtype = {'MSA_ID': object})
            df_fips = df_fips[['Year', 'MSA_ID', 'MSA', 'Abbrv']].drop_duplicates()
            df_fips = df_fips[df_fips['Abbrv'].isin(msa_to_import)]
        
            # view
            print()
            print("MSA set to import:")
            print(msa_to_import)
            print()
            print("MSA IDs:")
            display(df_fips)
            print()
            print("List of variables to import:")
            print(list_vars)

        # For State level pull
        if import_tab == 'States':
        
            # Set MSAs to import
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                    , sheet_name = 'CountyFIPS'
                                    , dtype = {'State FIPS': object, 'County FIPS': object})
            df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values))]
            states_to_import = list(df_fips['State FIPS'].unique())
            states_to_import = [str(state) for state in states_to_import]
            
            # view
            print()
            print("States set to import:")
            print(states_to_import)
            print()
            print("List of variables to import:")
            print(list_vars)

        # For National level pull
        if import_tab == 'National':
        
            print("Setting to import data at a national level")
            print()
            print("List of variables to import:")
            print(list_vars)




    ## For PUMS data
    if sample_type == 'PUMS':

        # Remove 2012-2015 if pulling PUMS tables (they only reported at the state level for PUMS on these years)
        # Create dictionary of variable mappings by year (sometimes the variable name changes over time)
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing
        file_pums = path_config / 'census_configuration_file2.xlsx'
        df_vars = pd.read_excel(file_pums, sheet_name = sample_type)
        df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        if 'H' in df_vars['Table Type'].unique():
            table_type = 'H'
            weight = 'WGTP'
        else:
            table_type = 'P'
            weight = 'PWGTP'

        print()
        print('PUMS table roll up: ' + table_type)

        if margin_of_error == 'Yes':
            df_vars.loc[(df_vars['ID'].str.contains('WGTP')) & (df_vars['Table Type'] == table_type), 'Include'] = 'Yes'
        
        df_vars = df_vars[df_vars['Include'] == 'Yes']
            
        groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
        groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

        print()
        print('PUMS variables to group by: ')
        print(groups)
        print()
        print('PUMS variables to group by (excluding integer based groups): ')
        print(groups2)
        
        df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
                
        dict_vars = {}
        for year in years_to_import:
            dict_vars[str(year)] = unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'].str.contains('group'))]['ID'].to_list()) + unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'] == 'integer')]['ID'].to_list()) + [weight]
            
        file_fips = path_git / 'config' / 'area_codes.xlsx'
        df_fips = pd.read_excel(file_fips
                                , sheet_name = 'CountyFIPS'
                                , dtype = {'State FIPS': str, 'County FIPS': str})
        # df_fips = df_fips[df_fips['Chamber Study'] == 'Yes']
        # df_fips = df_fips[df_fips['Peer MSA'     ] == 'Yes']
        df_fips_pums = pd.read_excel(file_fips
                                    , sheet_name = 'PUMAcodes'
                                    , dtype = {'STATEFP': str, 'COUNTYFP': str, 'TRACTCE': str, 'PUMA5CE': str})
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
        print()
        print("PUMA's set to import by state: ")
        print(dict_fips)
        print()
        print('Variables set to import by year:')
        print(dict_vars)



    ## For CPS data
    if estimate == 'CPS':
        
        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file2.xlsx'), sheet_name = sample_type)
        df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
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
        df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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


    ## For LEHD data
    if estimate == 'LEHD':
        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file2.xlsx'), sheet_name = estimate)
        df_vars = df_vars[df_vars['Sample'] == sample_type]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_vars = df_vars[df_vars['Include'] == 'Yes']
        variables = df_vars['ID'].unique()
        variables = ','.join(variables)

        if indicator == 'Jobs_4':
            variables = variables + '&ownercode=A05'

        print()
        print("Variables set to import:")
        print(variables)
        print()

        # For county level pull
        if import_tab == 'Counties':
            
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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
            print()
            print('Counties set to import by state:')
            print(dict_fips)
            print()

            # For MSA level pull
        if import_tab == 'MSA':
        
            # Set MSAs to import
            df_inputs['msa'] = df_inputs['msa'].astype("str")
            msa_to_import = list(df_inputs['msa'].values)

            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                    , sheet_name = 'MSAcodes'
                                    , dtype = {'State FIPS': object, 'MSA_ID': object})
            df_fips = df_fips[df_fips['MSA_ID'].isin(msa_to_import)]

            dict_fips = df_fips.copy()
            dict_fips = dict_fips[['State FIPS', 'MSA_ID']]
            dict_fips = dict_fips.groupby('State FIPS')['MSA_ID'].apply(list).to_dict()
            
            for key in list(dict_fips.keys()):
                dict_fips[key] = ",".join(dict_fips[key])
        
            # view
            print()
            print("MSA IDs set to import by state:")
            print(dict_fips)
            print()




    # view
    print()
    print('Variable Mapping table:')
    display(df_vars.head(3))











if version == 1:

    print(); print()
    print('Census Bureau import parameters:')
    print()

    # Import objects
    df_params = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name = 'Inputs', usecols='A:B')

    # Set parameters for querying Census data
    indicator     = df_params[df_params['Type'] == 'indicator' ]['Input'].values[0]
    estimate           = df_params[df_params['Type'] == 'estimate'       ]['Input'].values[0]
    sample_type        = df_params[df_params['Type'] == 'sample'         ]['Input'].values[0]
    geography          = df_params[df_params['Type'] == 'geography'      ]['Input'].values[0]
    import_tab         = df_params[df_params['Type'] == 'import_tab'     ]['Input'].values[0]
    margin_of_error    = df_params[df_params['Type'] == 'margin_of_error']['Input'].values[0]
    year_start         = df_params[df_params['Type'] == 'year_start'     ]['Input'].values[0]
    year_end           = df_params[df_params['Type'] == 'year_end'       ]['Input'].values[0]

    # View
    print('Indicator name:   ' + indicator )
    print('Sample:           ' + sample_type    )
    print('Estimate:         ' + estimate       )
    print('Final geography:  ' + geography      )
    print('Import geography: ' + import_tab     )
    print('Margin of error:  ' + margin_of_error)
    print('Start year:       ' + str(year_start))
    print('End year:         ' + str(year_end  ))




    print()
    print()
    print("API request inputs:")
    print()



    ## Import Variable Mapping
    df_inputs = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name = import_tab)

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

        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name = estimate)
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_vars = df_vars[df_vars['Include'] == 'Yes']
        
        if margin_of_error == 'Yes':
            df_vars['ID_Attributes'] = df_vars['ID_Attributes'].apply(ME_split)

        years_to_import = [2000, 2010, 2020]
        
        dict_vars = {}
        for year in years_to_import:
            dict_vars[str(year)] = ['NAME'] + unique(df_vars[df_vars['Year'] == year]['ID'].to_list())
            
        df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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
        print()
        print('Counties set to import by state:')
        print(dict_fips)
        print()
        print('Variables set to import by year:')
        print(dict_vars)



    ## For ACS1 or ACS5 data
    if sample_type in ['ACS', 'SUBJECT']:

        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name=sample_type)
        df_vars = df_vars[df_vars['Year'] == 2023]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_vars = df_vars[df_vars['Include'] == 'Yes']
        
        # Set tables and variables to import

        if margin_of_error == 'Yes':
            df_vars['ID_Attributes'] = df_vars['ID_Attributes'].apply(ME_split)
            list_vars = ['NAME'] + df_vars['ID_Attributes'].to_list()
        else:
            list_vars = ['NAME'] + df_vars['ID'].to_list()

        if sample_type == 'ACS':
            tables = df_vars['Table'].unique()
            print()
            print("Tables set to import:")
            print(tables)

        # For tract and county level pull
        if import_tab == 'Counties':
            
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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
            print()
            print('Counties set to import by state:')
            print(dict_fips)
            print()
            print('Variables set to import:')
            print(list_vars)

        # For MSA level pull
        if import_tab == 'MSA':
        
            # Set MSAs to import
            msa_to_import = list(df_inputs['msa'].values)
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx'), sheet_name='MSAcodes', dtype = {'MSA_ID': object})
            df_fips = df_fips[['Year', 'MSA_ID', 'MSA', 'Abbrv']].drop_duplicates()
            df_fips = df_fips[df_fips['Abbrv'].isin(msa_to_import)]
        
            # view
            print()
            print("MSA set to import:")
            print(msa_to_import)
            print()
            print("MSA IDs:")
            display(df_fips)
            print()
            print("List of variables to import:")
            print(list_vars)

        # For State level pull
        if import_tab == 'States':
        
            # Set MSAs to import
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                    , sheet_name = 'CountyFIPS'
                                    , dtype = {'State FIPS': object, 'County FIPS': object})
            df_fips = df_fips[(df_fips['State'].isin(df_inputs['states'].values))]
            states_to_import = list(df_fips['State FIPS'].unique())
        
            # view
            print()
            print("States set to import:")
            print(states_to_import)
            print()
            print("List of variables to import:")
            print(list_vars)

        # For National level pull
        if import_tab == 'National':
        
            print("Setting to import data at a national level")
            print()
            print("List of variables to import:")
            print(list_vars)




    ## For PUMS data
    if sample_type == 'PUMS':

        # Remove 2012-2015 if pulling PUMS tables (they only reported at the state level for PUMS on these years)
        # Create dictionary of variable mappings by year (sometimes the variable name changes over time)
        # Import County FIPS mapping
        # Convert to dictionary object for easy state-county combination importing
        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name = sample_type)
        df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        if 'H' in df_vars['Table Type'].unique():
            table_type = 'H'
            weight = 'WGTP'
        else:
            table_type = 'P'
            weight = 'PWGTP'

        print()
        print('PUMS table roll up: ' + table_type)

        if margin_of_error == 'Yes':
            df_vars.loc[(df_vars['ID'].str.contains('WGTP')) & (df_vars['Table Type'] == table_type), 'Include'] = 'Yes'
        
        df_vars = df_vars[df_vars['Include'] == 'Yes']
            
        groups  = list(df_vars[df_vars['Data Type'].str.contains('group')]['ID2'].unique())
        groups2 = list(df_vars[df_vars['Data Type'] ==           'group' ]['ID2'].unique())

        print()
        print('PUMS variables to group by: ')
        print(groups)
        print()
        print('PUMS variables to group by (excluding integer based groups): ')
        print(groups2)
        
        df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
                
        dict_vars = {}
        for year in years_to_import:
            dict_vars[str(year)] = unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'].str.contains('group'))]['ID'].to_list()) + unique(df_vars[(df_vars['Year'] == year) & (df_vars['Data Type'] == 'integer')]['ID'].to_list()) + [weight]
            
        df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                , sheet_name = 'CountyFIPS'
                                , dtype = {'State FIPS': object, 'County FIPS': object})
        # df_fips = df_fips[df_fips['Chamber Study'] == 'Yes']
        # df_fips = df_fips[df_fips['Peer MSA'     ] == 'Yes']
        df_fips_pums = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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
        print()
        print("PUMA's set to import by state: ")
        print(dict_fips)
        print()
        print('Variables set to import by year:')
        print(dict_vars)



    ## For CPS data
    if estimate == 'CPS':
        
        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name = sample_type)
        df_vars = df_vars[df_vars['Year'].isin(years_to_import)]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
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
        df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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


    ## For LEHD data
    if estimate == 'LEHD':
        df_vars = pd.read_excel(os.path.join(path_config, 'census_configuration_file.xlsm'), sheet_name = estimate)
        df_vars = df_vars[df_vars['Sample'] == sample_type]
        df_vars = df_vars[df_vars['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_vars = df_vars[df_vars['Include'] == 'Yes']
        variables = df_vars['ID'].unique()
        variables = ','.join(variables)

        if indicator == 'Jobs_4':
            variables = variables + '&ownercode=A05'

        print()
        print("Variables set to import:")
        print(variables)
        print()

        # For county level pull
        if import_tab == 'Counties':
            
            # Import County FIPS mapping
            # Convert to dictionary object for easy state-county combination importing
            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
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
            print()
            print('Counties set to import by state:')
            print(dict_fips)
            print()

            # For MSA level pull
        if import_tab == 'MSA':
        
            # Set MSAs to import
            df_inputs['msa'] = df_inputs['msa'].astype("str")
            msa_to_import = list(df_inputs['msa'].values)

            df_fips = pd.read_excel(os.path.join(path_git, 'config', 'area_codes.xlsx')
                                    , sheet_name = 'MSAcodes'
                                    , dtype = {'State FIPS': object, 'MSA_ID': object})
            df_fips = df_fips[df_fips['MSA_ID'].isin(msa_to_import)]

            dict_fips = df_fips.copy()
            dict_fips = dict_fips[['State FIPS', 'MSA_ID']]
            dict_fips = dict_fips.groupby('State FIPS')['MSA_ID'].apply(list).to_dict()
            
            for key in list(dict_fips.keys()):
                dict_fips[key] = ",".join(dict_fips[key])
        
            # view
            print()
            print("MSA IDs set to import by state:")
            print(dict_fips)
            print()




    # view
    print()
    print('Variable Mapping table:')
    display(df_vars.head(3))

