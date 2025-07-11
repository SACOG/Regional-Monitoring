



version=2


print(); print()
print('Bureau of Labor Statistics import parameters:')
print()


path_yaml = path_config / 'bls_indicators.yaml'

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
    project   = df_run[df_run['Parameter'] == 'Project'  ]['Input'].values[0]
    indicator = df_run[df_run['Parameter'] == 'Indicator']['Input'].values[0]
    survey    = df_run[df_run['Parameter'] == 'Survey'   ]['Input'].values[0]

    if survey in ['SM', 'CE']:
        data_type_text = df_run[df_run['Parameter'] == 'Data Type']['Input'].values[0]
    if survey in ['LA']:
        measure_type_text = df_run[df_run['Parameter'] == 'Measure Type']['Input'].values[0]

    seasonal_code   = df_run[df_run['Parameter'] == 'Seasonal Adjustment' ]['Input'].values[0]
    geography       = df_run[df_run['Parameter'] == 'Geography'           ]['Input'].values[0]
    years_to_import = df_run[df_run['Parameter'] == 'Years Imported'      ]['Input'].values[0]

    export_loc  = dict_config['Indicators'][project][indicator]['sp_location']
    folder      = dict_config['Indicators'][project][indicator]['folder'     ]

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

    export_loc  = dict_config['Indicators'][project][indicator]['sp_location']
    folder      = dict_config['Indicators'][project][indicator]['folder'     ]
    weighted_by = dict_config['Indicators'][project][indicator]['weighted_by']

    print()
    display(dict_config['Indicators'][project][indicator])
    surveys = dict_config['Indicators'][project][indicator]['survey']
    if isinstance(surveys, list):
        print('Surveys available:')
        display(surveys); print()
        print('Which survey do you want to pull data from?')
        survey = input()
        assert survey in surveys, 'Unacceptable input, please choose from options displayed above'
    else:
        survey = dict_config['Indicators'][project][indicator]['survey']

    print('---------------------------------------------------------------------------------------------------------------------------------------')

    print()

    if survey in ['SM', 'CE']:
        print('Data types available:'); print()
        display(dict_config['Surveys'][survey]['data_type']); print()
        print('Which data type do you want to request?'); print()
        data_type_text = input()
        assert data_type_text in dict_config['Surveys'][survey]['data_type'], 'Unacceptable input, please choose from options displayed above'
    if survey in ['LA']:
        print('Measure types available:'); print()
        display(dict_config['Surveys'][survey]['measure_type']); print()
        print('Which measure type do you want to request?'); print()
        measure_type_text = input()
        assert measure_type_text in dict_config['Surveys'][survey]['measure_type'], 'Unacceptable input, please choose from options displayed above'
    print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')


    print()
    print('Do you want seasonally adjusted estimates?  Select Yes/No: '); print()
    seasonal_adj = input()
    if seasonal_adj == 'Yes':
        seasonal_code = 'S'
    if seasonal_adj == 'No':
        seasonal_code = 'U'
    assert seasonal_adj in ['Yes', 'No'], "Unacceptable input, please type 'Yes' or 'No'"
    print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')



    print()
    print('Geographies available:'); print()
    display(dict_config['Surveys'][survey]['geographies_available']); print()
    print('Which geography do you want to pull data for?'); print()
    geography = input()
    assert geography in dict_config['Surveys'][survey]['geographies_available'], 'Unacceptable input, please choose from options displayed above'
    print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')

    print()
    print('Years available:')
    display(dict_config['Surveys'][survey]['years_available']); print()
    print('Do you want to pull data for all years available?  Select Yes/No: '); print()
    all_years = input()
    if all_years == 'Yes':
        years_to_import = dict_config['Surveys'][survey]['years_available']
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



    print('---------------------------------------------------------------------------------------------------------------------------------------')

    print()


    file_config_set = path_config / 'runs' / f'{indicator}.txt'
    with open(file_config_set, 'w') as f:
        f.write(f"Project: {project}\n")
        f.write(f"Indicator: {indicator}\n")
        f.write(f"Export Location: {export_loc}\n")
        f.write(f"Folder: {folder}\n")
        f.write(f"Survey: {survey}\n")
        if survey in ['SM', 'CE']:
            f.write(f"Data Type: {data_type_text}\n")
        if survey in ['LA']:
            f.write(f"Measure Type: {measure_type_text}\n")
        f.write(f"Seasonal Adjustment: {seasonal_code}\n")
        f.write(f"Geography: {geography}\n")
        f.write(f"Years Imported: {years}\n")


print('Bureau of Labor Statistics importing parameters:')
print()

# Import objects
file_config = path_config / 'bls_configuration_file2.xlsx'



print()
print('Series ID construction for API request:')
print()

# Set parameters for querying BLS data
state_code     = dict_config['Surveys'][survey]['state_code'    ]
area_code      = dict_config['Surveys'][survey]['area_code'     ]
industry_code  = dict_config['Surveys'][survey]['industry_code' ]
data_type_code = dict_config['Surveys'][survey]['data_type_code']
measure_code   = dict_config['Surveys'][survey]['measure_code'  ]




dict_series = {}

print('Survey prefix: ' + survey)
print()

print('Seasonal code: ' + seasonal_code)
    
if area_code:
    df_area = pd.read_excel(file_config, sheet_name='area_codes', dtype={'County FIPS':str, 'MSA_ID':str})
    df_area = df_area[df_area['Survey'] == survey]
    df_area = df_area[df_area['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
    df_area = df_area[df_area['Include'] == 'Yes']
    if geography == 'MSA':
        df_area = df_area[df_area['area_type_code'] == 'B']
        if state_code:
            file_area = path_config0 / 'area_codes.xlsx'
            df_states = pd.read_excel(file_area, sheet_name='MSAcodes', dtype={'State FIPS':str, 'MSA_ID':str})
            df_states = df_states[['MSA_ID', 'State FIPS', 'MSA']].drop_duplicates()
            df_area['MSA_ID'] = df_area['MSA_ID'].astype(str)
            df_area = df_area.merge(df_states, on = 'MSA_ID', how = 'left')
            df_area = df_area[['State FIPS', 'area_code', 'area_text', 'MSA', 'MSA_ID']]
        else:
            df_area = df_area[['area_code', 'area_text', 'MSA_ID']]
    if geography == 'Counties':
        df_area = df_area[df_area['area_type_code'] == 'F']
        if state_code:
            file_area = path_config0 / 'area_codes.xlsx'
            df_states = pd.read_excel(file_area, sheet_name = 'CountyFIPS', dtype = {'State FIPS':str, 'County FIPS':str})
            df_states = df_states[['County FIPS', 'State FIPS', 'County Name']].drop_duplicates()
            df_area = df_area.merge(df_states, on = 'County FIPS', how = 'left')
            df_area = df_area[['State FIPS', 'area_code', 'area_text', 'County Name']]
        else: 
            df_area = df_area[['area_code', 'area_text']]
    df_area = df_area.reset_index(drop = True)
    print('Area codes table: ')
    display(df_area.head())

if industry_code:
    df_industries = pd.read_excel(file_config, sheet_name='industry_codes', dtype={'industry_code':str})
    df_industries = df_industries[df_industries['Survey'] == survey]
    df_industries = df_industries[df_industries['Include'] == 'Yes']
    df_industries = df_industries[df_industries['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
    list_sectors = list(df_industries['industry_code'].values)
    list_sectors = [str(sector) for sector in list_sectors]
    print('Industry codes: ')
    print(list_sectors)

if data_type_code:
    df_datatypes = pd.read_excel(file_config, sheet_name='datatype_codes', dtype=str)
    df_datatypes = df_datatypes[df_datatypes['Survey'].str.contains(survey)]
    df_datatypes['data_type_text'] = df_datatypes['data_type_text'].str.lower()
    data_type_text_sub = data_type_text.lower()
    df_datatypes = df_datatypes[df_datatypes['data_type_text'] == data_type_text_sub]
    data_type_code = df_datatypes['data_type_code'].values[0]
    print('Data type code: ' + data_type_code)

if measure_code:
    df_measures = pd.read_excel(file_config, sheet_name='measure_codes', dtype=str)
    df_measures = df_measures[df_measures['Survey'].str.contains(survey)]
    df_measures['measure_type_text'] = df_measures['measure_type_text'].str.lower()
    measure_type_text_sub = measure_type_text.lower()
    df_measures = df_measures[df_measures['measure_type_text'] == measure_type_text_sub]
    measure_code = df_measures['measure_code'].values[0]
    print('Measure code: ' + measure_code)
    



print()
print('Series IDs organized by geography: ')
print()

if survey == 'SM':
    dict_series = dict_maker(survey        = survey
                            , geography    = geography
                            , seasonal     = seasonal_code
                            , df           = df_area
                            , list_sectors = list_sectors
                            , data_type    = data_type_code)

if survey == 'CE':
    dict_series = dict_maker(survey        = survey
                            , geography    = geography
                            , seasonal     = seasonal_code
                            , list_sectors = list_sectors
                            , data_type    = data_type_code)

if survey == 'LA':
    dict_series = dict_maker(survey        = survey
                            , geography    = geography
                            , seasonal     = seasonal_code
                            , df           = df_area
                            , measure_code = measure_code)

display(dict_series)





print()
print('Geography to Series ID mapping table: ')
print()


df_series_area = pd.melt(
    pd.DataFrame.from_dict(dict_series)
    , var_name = 'area_text'
    , value_name = 'seriesID'
)



    
if survey in ['SM', 'LA']:
    df_series_area = df_series_area.merge(df_area[['area_text', 'area_code', 'MSA_ID']], on='area_text')
    
if survey == 'SM':
    df_series_area['industry_code'] = df_series_area['seriesID'].str[10:18]
    df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on='industry_code', how='left')

if survey == 'CE':
    df_series_area['industry_code'] = df_series_area['seriesID'].str[3:11]
    df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on='industry_code', how='left')
    df_series_area['area_code'] = '000000'

display(df_series_area.head())


print()
print('Series ID groupings for API request (50 at a time): ')
print()


list_series_all = []
for i in dict_series.keys():
    list_series_all.extend(dict_series[i])


list_series_all = [list_series_all[x:x+50] for x in range(0, len(list_series_all), 50)]
display(list_series_all)






if version == 1:
    print('Bureau of Labor Statistics importing parameters:')
    print()

    # Import objects
    file_config = path_config / 'bls_configuration_file.xlsm'
    df_params = pd.read_excel(file_config, sheet_name = 'Inputs', usecols='A:B')


    # Set parameters for querying BLS data
    indicator = df_params[df_params['Type'] == 'indicator']['Input'].values[0]
    survey         = df_params[df_params['Type'] == 'survey'        ]['Input'].values[0]
    geography      = df_params[df_params['Type'] == 'geography'     ]['Input'].values[0]
    year_start     = df_params[df_params['Type'] == 'year_start'    ]['Input'].values[0]
    year_end       = df_params[df_params['Type'] == 'year_end'      ]['Input'].values[0]


    # View
    print('Indicator name: ' + indicator )
    print('Survey:         ' + survey         )
    print('Geography:      ' + geography      )
    print('Start year:     ' + str(year_start))
    print('End year:       ' + str(year_end  ))



    print()
    print('Series ID construction for API request:')
    print()

    # Import objects
    df_series_map = pd.read_excel(file_config, sheet_name='Series ID Map')
    df_series_map = df_series_map[['Type', survey]]

    # Set parameters for querying BLS data
    seasonal_code  = df_series_map[df_series_map['Type'] == 'Seasonal Adjustment Code'     ][survey].values[0]
    state_code     = df_series_map[df_series_map['Type'] == 'State Code'                   ][survey].values[0]
    area_code      = df_series_map[df_series_map['Type'] == 'Area Code'                    ][survey].values[0]
    industry_code  = df_series_map[df_series_map['Type'] == 'Supersector and Industry Code'][survey].values[0]
    data_type_code = df_series_map[df_series_map['Type'] == 'Data Type Code'               ][survey].values[0]
    measure_code   = df_series_map[df_series_map['Type'] == 'Measure Code'                 ][survey].values[0]


    dict_series = {}

    print('Survey prefix: ' + survey)

    if seasonal_code == 'Yes':
        df_seasonal = pd.read_excel(file_config, sheet_name = 'seasonal_adj_codes')
        df_seasonal = df_seasonal[df_seasonal['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_seasonal = df_seasonal[df_seasonal['Include'] == 'Yes']
        seasonal_code = df_seasonal['seasonal_code'].values[0]
        print('Seasonal code: ' + seasonal_code)
        
    if area_code == 'Yes':
        df_area = pd.read_excel(file_config, sheet_name = 'area_codes', dtype = {'County FIPS': object, 'MSA_ID': object})
        df_area = df_area[df_area['Survey'] == survey]
        df_area = df_area[df_area['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        df_area = df_area[df_area['Include'] == 'Yes']
        if geography == 'MSA':
            df_area = df_area[df_area['area_type_code'] == 'B']
            if state_code == 'Yes':
                file_area = path_config0 / 'Area Codes.xlsx'
                df_states = pd.read_excel(file_area, sheet_name = 'MSAcodes', dtype = {'State FIPS': object, 'MSA_ID': object})
                df_states = df_states[['MSA_ID', 'State FIPS', 'MSA']].drop_duplicates()
                df_area['MSA_ID'] = df_area['MSA_ID'].astype(str)
                df_area = df_area.merge(df_states, on = 'MSA_ID', how = 'left')
                df_area = df_area[['State FIPS', 'area_code', 'area_text', 'MSA', 'MSA_ID']]
            else:
                df_area = df_area[['area_code', 'area_text', 'MSA_ID']]
        if geography == 'Counties':
            df_area = df_area[df_area['area_type_code'] == 'F']
            if state_code == 'Yes':
                file_area = path_config0 / 'Area Codes.xlsx'
                df_states = pd.read_excel(file_area, sheet_name = 'CountyFIPS', dtype = {'State FIPS': object, 'County FIPS': object})
                df_states = df_states[['County FIPS', 'State FIPS', 'County Name']].drop_duplicates()
                df_area = df_area.merge(df_states, on = 'County FIPS', how = 'left')
                df_area = df_area[['State FIPS', 'area_code', 'area_text', 'County Name']]
            else: 
                df_area = df_area[['area_code', 'area_text']]
        df_area = df_area.reset_index(drop = True)
        print('Area codes table: ')
        display(df_area.head())


    if industry_code == 'Yes':
        df_industries = pd.read_excel(file_config, sheet_name = 'industry_codes', dtype = {'industry_code': object})
        df_industries = df_industries[df_industries['Survey'] == survey]
        df_industries = df_industries[df_industries['Include'] == 'Yes']
        df_industries = df_industries[df_industries['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        list_sectors = list(df_industries['industry_code'].values)
        list_sectors = [str(sector) for sector in list_sectors]
        print('Industry codes: ')
        print(list_sectors)

        
    if data_type_code == 'Yes':
        df_datatypes = pd.read_excel(file_config, sheet_name = 'datatype_codes', dtype = {'data_type_code': object})
        df_datatypes = df_datatypes[df_datatypes['Survey'].str.contains(survey)]
        df_datatypes = df_datatypes[df_datatypes['Include'] == 'Yes']
        df_datatypes = df_datatypes[df_datatypes['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        data_type_code = df_datatypes['data_type_code'].values[0]
        print('Data type code: ' + data_type_code)


    if measure_code == 'Yes':
        df_measures = pd.read_excel(file_config, sheet_name = 'measure_codes', dtype = {'data_type_code': object})
        df_measures = df_measures[df_measures['Survey'].str.contains(survey)]
        df_measures = df_measures[df_measures['Include'] == 'Yes']
        df_measures = df_measures[df_measures['Indicator Name'].str.contains(indicator).replace(np.nan, False)]
        measure_code = df_measures['data_type_code'].values[0]
        print('Measure code: ' + measure_code)
        



    print()
    print('Series IDs organized by geography: ')
    print()

    if survey == 'SM':
        dict_series = dict_maker(survey         = survey
                                , geography    = geography
                                , seasonal     = seasonal_code
                                , df           = df_area
                                , list_sectors = list_sectors
                                , data_type    = data_type_code)

    if survey == 'CE':
        dict_series = dict_maker(survey          = survey
                                , geography    = geography
                                , seasonal     = seasonal_code
                                , list_sectors = list_sectors
                                , data_type    = data_type_code)

    if survey == 'LA':
        dict_series = dict_maker(survey         = survey
                                , geography    = geography
                                , seasonal     = seasonal_code
                                , df           = df_area
                                , measure_code = measure_code)

    display(dict_series)





    print()
    print('Geography to Series ID mapping table: ')
    print()


    df_series_area = pd.melt(
        pd.DataFrame.from_dict(dict_series)
        , var_name = 'area_text'
        , value_name = 'seriesID'
    )
        
    if survey in ['SM', 'LA']:
        df_series_area = df_series_area.merge(df_area[['area_text', 'area_code', 'MSA_ID']], on = 'area_text')
        
    if survey == 'SM':
        df_series_area['industry_code'] = df_series_area['seriesID'].str[10:18]
        df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on = 'industry_code', how = 'left')

    if survey == 'CE':
        df_series_area['industry_code'] = df_series_area['seriesID'].str[3:11]
        df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on = 'industry_code', how = 'left')
        df_series_area['area_code'] = '000000'

    display(df_series_area.head())


    print()
    print('Series ID groupings for API request (50 at a time): ')
    print()

    list_series_all = []
    for i in dict_series.keys():
        list_series_all.extend(dict_series[i])


    list_series_all = [list_series_all[x:x+50] for x in range(0, len(list_series_all), 50)]
    display(list_series_all)