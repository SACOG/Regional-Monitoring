print('Bureau of Labor Statistics importing parameters:')
print('')

# Import objects
df_params = pd.read_excel(os.path.join(path_config, 'BLS Configuration File.xlsx'), sheet_name = 'Inputs')


# Set parameters for querying BLS data
indicator_name = df_params[df_params['Type'] == 'indicator_name']['Input'].values[0]
survey         = df_params[df_params['Type'] == 'survey'        ]['Input'].values[0]
geography      = df_params[df_params['Type'] == 'geography'     ]['Input'].values[0]
percentages    = df_params[df_params['Type'] == 'percentages'   ]['Input'].values[0]
year_start     = df_params[df_params['Type'] == 'year_start'    ]['Input'].values[0]
year_end       = df_params[df_params['Type'] == 'year_end'      ]['Input'].values[0]


# View
print('Indicator name: ' + indicator_name )
print('Survey:         ' + survey         )
print('Geography:      ' + geography      )
print('Percentages:    ' + percentages    )
print('Start year:     ' + str(year_start))
print('End year:       ' + str(year_end  ))



print('')
print('Series ID construction for API request:')
print('')

# Import objects
df_series_map = pd.read_excel(os.path.join(path_config, 'BLS Configuration File.xlsx'), sheet_name = 'Series ID Map')
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
    df_seasonal = pd.read_excel(os.path.join(path_config, 'BLS Configuration File.xlsx'), sheet_name = 'seasonal_adj_codes')
    df_seasonal = df_seasonal[df_seasonal['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    df_seasonal = df_seasonal[df_seasonal['Include'] == 'Yes']
    seasonal_code = df_seasonal['seasonal_code'].values[0]
    print('Seasonal code: ' + seasonal_code)
    
if area_code == 'Yes':
    df_area = pd.read_excel(os.path.join(path_config, 'BLS Configuration File.xlsx'), sheet_name = 'area_codes', dtype = {'County FIPS': object, 'MSA_ID': object})
    df_area = df_area[df_area['Survey'] == survey]
    df_area = df_area[df_area['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    df_area = df_area[df_area['Include'] == 'Yes']
    if geography == 'MSA':
        df_area = df_area[df_area['area_type_code'] == 'B']
        if state_code == 'Yes':
            df_states = pd.read_excel(os.path.join(path_config0, "Area Codes.xlsx"), sheet_name = 'MSAcodes', dtype = {'State FIPS': object, 'MSA_ID': object})
            df_states = df_states[['MSA_ID', 'State FIPS', 'MSA']].drop_duplicates()
            df_area['MSA_ID'] = df_area['MSA_ID'].astype(str)
            df_area = df_area.merge(df_states, on = 'MSA_ID', how = 'left')
            df_area = df_area[['State FIPS', 'area_code', 'area_text', 'MSA']]
        else:
            df_area = df_area[['area_code', 'area_text']]
    if geography == 'Counties':
        df_area = df_area[df_area['area_type_code'] == 'F']
        if state_code == 'Yes':
            df_states = pd.read_excel(os.path.join(path_config0, "Area Codes.xlsx"), sheet_name = 'CountyFIPS', dtype = {'State FIPS': object, 'County FIPS': object})
            df_states = df_states[['County FIPS', 'State FIPS', 'County Name']].drop_duplicates()
            df_area = df_area.merge(df_states, on = 'County FIPS', how = 'left')
            df_area = df_area[['State FIPS', 'area_code', 'area_text', 'County Name']]
        else: 
            df_area = df_area[['area_code', 'area_text']]
    df_area = df_area.reset_index(drop = True)
    print('Area codes table: ')
    display(df_area.head())


if industry_code == 'Yes':
    df_industries = pd.read_excel(os.path.join(path_config, "BLS Configuration File.xlsx")
                              , sheet_name = 'industry_codes'
                              , dtype = {'industry_code': object})
    df_industries = df_industries[df_industries['Include'] == 'Yes']
    df_industries = df_industries[df_industries['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    list_sectors = list(df_industries['industry_code'].values)
    list_sectors = [str(sector) for sector in list_sectors]
    print('Industry codes: ')
    print(list_sectors)

    
if data_type_code == 'Yes':
    df_datatypes = pd.read_excel(os.path.join(path_config, "BLS Configuration File.xlsx")
                             , sheet_name = 'datatype_codes'
                              , dtype = {'data_type_code': object})
    df_datatypes = df_datatypes[df_datatypes['Survey'].str.contains(survey)]
    df_datatypes = df_datatypes[df_datatypes['Include'] == 'Yes']
    df_datatypes = df_datatypes[df_datatypes['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    data_type_code = df_datatypes['data_type_code'].values[0]
    print('Data type code: ' + data_type_code)


if measure_code == 'Yes':
    df_measures = pd.read_excel(os.path.join(path_config, "BLS Configuration File.xlsx")
                             , sheet_name = 'measure_codes'
                              , dtype = {'data_type_code': object})
    df_measures = df_measures[df_measures['Survey'].str.contains(survey)]
    df_measures = df_measures[df_measures['Include'] == 'Yes']
    df_measures = df_measures[df_measures['Indicator Name'].str.contains(indicator_name).replace(np.nan, False)]
    measure_code = df_measures['data_type_code'].values[0]
    print('Measure code: ' + measure_code)
    



print('')
print('Series IDs organized by geography: ')
print('')

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





print('')
print('Geography to Series ID mapping table: ')
print('')

df_series_area = pd.melt(
    pd.DataFrame.from_dict(dict_series)
    , var_name = 'area_text'
    , value_name = 'seriesID'
)
    
if survey in ['SM', 'LA']:
    df_series_area = df_series_area.merge(df_area[['area_text', 'area_code']], on = 'area_text')
    
if survey == 'SM':
    df_series_area['industry_code'] = df_series_area['seriesID'].str[10:18]
    df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on = 'industry_code', how = 'left')

if survey == 'CE':
    df_series_area['industry_code'] = df_series_area['seriesID'].str[3:11]
    df_series_area = df_series_area.merge(df_industries[['industry_code', 'industry_name', 'Variable']], on = 'industry_code', how = 'left')
    df_series_area['area_code'] = '000000'

display(df_series_area.head())


print('')
print('Series ID groupings for API request (50 at a time): ')
print('')

list_series_all = []
for i in dict_series.keys():
    list_series_all.extend(dict_series[i])


list_series_all = [list_series_all[x:x+50] for x in range(0, len(list_series_all), 50)]
display(list_series_all)