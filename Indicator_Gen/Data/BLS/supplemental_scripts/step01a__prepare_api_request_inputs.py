




print(); print()
print('Bureau of Labor Statistics import parameters:')
print()


path_yaml = path_config / 'bls.yaml'

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

    if survey in ['SM', 'CE', 'EN']:
        data_type_text = df_run[df_run['Parameter'] == 'Data Type']['Input'].values[0]
        if survey in ['EN']:
            size_code_text  = df_run[df_run['Parameter'] == 'Employer Size' ]['Input'].values[0]
            owner_code_text = df_run[df_run['Parameter'] == 'Ownership Type']['Input'].values[0]

    if survey in ['LA']:
        measure_type_text = df_run[df_run['Parameter'] == 'Measure Type']['Input'].values[0]

    seasonal_code   = df_run[df_run['Parameter'] == 'Seasonal Adjustment' ]['Input'].values[0]
    geography       = df_run[df_run['Parameter'] == 'Geography'           ]['Input'].values[0]
    years_to_import = df_run[df_run['Parameter'] == 'Years Imported'      ]['Input'].values[0]

    export_loc  = dict_config['Indicators'][project][indicator]['sp_location']
    folder      = dict_config['Indicators'][project][indicator]['folder'     ]
    percentages = dict_config['Indicators'][project][indicator]['percentages']

    years_to_import = years_to_import.split(', ')
    years_to_import = [int(year) for year in years_to_import]
    year_end   = np.max(years_to_import)
    year_start = np.min(years_to_import)


else:

    while True:
        try:
            print('---------------------------------------------------------------------------------------------------------------------------------------')
            print()
            print('Projects available: ')
            projects = dict_config['Project']
            display(projects); print()
            print('Which project are you pulling data for?'); print()
            project = input()
            if project in projects:
                print()
                break
            else:
                print()
                print("Invalid choice. Please try again.")
        except ValueError:
            print()
            print("Invalid choice. Please choose from options outlined here: ");print(projects)
            print()
            print('---------------------------------------------------------------------------------------------------------------------------------------')


    while True:
        try:
            print()
            print('Indicators available:'); print()
            indicators = list(dict_config['Indicators'][project].keys())
            display(indicators); print()
            print('Which indicator do you need to rerun?'); print()
            indicator = input()
            if indicator in indicators:
                print()
                break
            else:
                print()
                print("Invalid choice. Please try again.")
        except ValueError:
            print()
            print("Invalid choice. Please choose from options outlined here: ");print(indicators)
            print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')

    export_loc  = dict_config['Indicators'][project][indicator]['sp_location']
    folder      = dict_config['Indicators'][project][indicator]['folder'     ]
    percentages = dict_config['Indicators'][project][indicator]['percentages']
    weighted_by = dict_config['Indicators'][project][indicator]['weighted_by']


    while True:
        try:
            print()
            display(dict_config['Indicators'][project][indicator])
            surveys = dict_config['Indicators'][project][indicator]['survey']
            if isinstance(surveys, list):
                print('Surveys available:')
                display(surveys); print()
                print('Which survey do you want to pull data from?')
                survey = input()            
            else:
                survey = dict_config['Indicators'][project][indicator]['survey']
            if survey in surveys:
                print()
                break
            else:
                print()
                print("Invalid choice. Please try again.")
        except ValueError:
            print()
            print("Invalid choice. Please choose from options outlined here: ");print(surveys)
            print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')

    print()

    if survey in ['SM', 'CE', 'EN']:
        while True:
            try:
                print('Data types available:'); print()
                data_types = dict_config['Surveys'][survey]['data_type']
                display(data_types); print()
                print('Which data type do you want to request?'); print()
                data_type_text = input()
                if data_type_text in data_types:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(data_types)
                print()
    else:
        pass

    if survey in ['EN']:
        while True:
            try:
                print()
                print('Employer sizes available:'); print()
                size_types = dict_config['Surveys'][survey]['size_type']
                display(size_types); print()
                print('Which employer size category do you want to request?'); print()
                size_code_text = input()
                if size_code_text in size_types:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(size_types)
                print()
    else:
        pass

    if survey in ['EN']:
        while True:
            try:
                print()
                print('Ownership categories available:'); print()
                owner_types = dict_config['Surveys'][survey]['owner_type']
                display(owner_types); print()
                print('Which ownership category do you want to request?'); print()
                owner_code_text = input()
                if owner_code_text in owner_types:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(owner_types)
                print()
    else:
        pass
    
    if survey in ['LA']:
        while True:
            try:
                print('Measure types available:'); print()
                measure_types = dict_config['Surveys'][survey]['measure_type']
                display(measure_types); print()
                print('Which measure type do you want to request?'); print()
                measure_type_text = input()
                if measure_type_text in measure_types:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(measure_types)
                print()
    else:
        pass



    print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')


    while True:
        try:
            print()
            print('Do you want seasonally adjusted estimates?  Select Yes/No: '); print()
            seasonal_adj = input()
            if seasonal_adj == 'Yes':
                seasonal_code = 'S'
            if seasonal_adj == 'No':
                seasonal_code = 'U'
            if seasonal_code in ['U', 'S']:
                print()
                break
            else:
                print()
                print("Invalid choice. Please try again.")
        except ValueError:
            print()
            print("Invalid choice. Please choose from options outlined here: ");print(['U', 'S'])
            print()
    print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')



    while True:
        try:
            print()
            print('Geographies available:'); print()
            geographies = dict_config['Surveys'][survey]['geographies_available']
            display(geographies); print()
            print('Which geography do you want to pull data for?'); print()
            geography = input()
            if geography in geographies:
                print()
                break
            else:
                print()
                print("Invalid choice. Please try again.")
        except ValueError:
            print()
            print("Invalid choice. Please choose from options outlined here: ");print(['U', 'S'])
            print()

    print()
    print('---------------------------------------------------------------------------------------------------------------------------------------')

    while True:
        try:
            print()
            print('Years available:')
            display(dict_config['Surveys'][survey]['years_available']); print()
            print('Do you want to pull data for all years available?  Select Yes/No: '); print()
            all_years = input()
            if all_years == 'Yes':
                years_to_import = dict_config['Surveys'][survey]['years_available']
                years = ', '.join([str(year) for year in years_to_import])
            if all_years == 'No':
                print()
                print('Please type which years you want to pull data from, separated by commas:'); print()
                years = input()
                if ',' in years:
                    years_to_import = years.split(', ')
                    years_to_import = [int(year) for year in years_to_import]
                else:
                    years_to_import = [int(years)]
            if all_years in ['Yes', 'No']:
                print()
                break
            else:
                print()
                print("Invalid choice. Please try again.")
        except ValueError:
            print()
            print("Invalid choice. Please choose from options outlined here: ");print(['U', 'S'])
            print()
    
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
        if survey in ['SM', 'CE', 'EN']:
            f.write(f"Data Type: {data_type_text}\n")
            if survey in ['EN']:
                f.write(f"Employer Size: {size_code_text}\n")
                f.write(f"Ownership Type: {owner_code_text}\n")
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
size_code      = dict_config['Surveys'][survey]['size_code'     ]
owner_code     = dict_config['Surveys'][survey]['owner_code'    ]
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
    df_area['area_text'] = df_area['area_text'].str.strip()
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

if size_code:
    df_sizes = pd.read_excel(file_config, sheet_name='size_codes', dtype=str)
    df_sizes = df_sizes[df_sizes['Survey'].str.contains(survey)]
    df_sizes['size_code_text'] = df_sizes['size_code_text'].str.lower()
    size_code_text_sub = size_code_text.lower()
    df_sizes = df_sizes[df_sizes['size_code_text'] == size_code_text_sub]
    size_code = df_sizes['size_code'].values[0]
    print('Employer size code: ' + data_type_code)

if owner_code:
    df_owners = pd.read_excel(file_config, sheet_name='owner_codes', dtype=str)
    df_owners = df_owners[df_owners['Survey'].str.contains(survey)]
    df_owners['owner_code_text'] = df_owners['owner_code_text'].str.lower()
    owner_code_text_sub = owner_code_text.lower()
    df_owners = df_owners[df_owners['owner_code_text'] == owner_code_text_sub]
    owner_code = df_owners['owner_code'].values[0]
    print('Ownership type code: ' + owner_code)

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

if survey == 'EN':
    dict_series = dict_maker(survey        = survey
                            , geography    = geography
                            , seasonal     = seasonal_code
                            , df           = df_area
                            , data_type    = data_type_code
                            , size_code    = size_code
                            , owner_code   = owner_code
                            , list_sectors = list_sectors)

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
df_series_area = df_series_area.drop_duplicates().reset_index(drop=True)


    
if survey in ['SM', 'LA']:
    if geography == 'MSA':
        area_id = 'MSA_ID'
    if geography == 'Counties':
        area_id = 'County FIPS'
    df_series_area = df_series_area.merge(df_area[['area_text', 'area_code', area_id]], on='area_text')
    

if survey == 'SM':
    df_series_area['industry_code'] = df_series_area['seriesID'].str[10:18]
    df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on='industry_code', how='left')

if survey == 'CE':
    df_series_area['industry_code'] = df_series_area['seriesID'].str[3:11]
    df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on='industry_code', how='left')
    df_series_area['area_code'] = '000000'

df_series_area = df_series_area.drop_duplicates().reset_index(drop=True)
display(df_series_area.head())


print()
print('Series ID groupings for API request (50 at a time): ')
print()


list_series_all = []
for i in dict_series.keys():
    list_series_all.extend(dict_series[i])


list_series_all = [list_series_all[x:x+50] for x in range(0, len(list_series_all), 50)]
display(list_series_all)



