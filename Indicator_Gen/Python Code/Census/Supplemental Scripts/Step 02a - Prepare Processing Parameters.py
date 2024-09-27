print('Census Bureau processing parameters:')
print('')

# Import parameters table
df_params = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = 'Inputs')

# Import indicators table
df_indicators = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = 'Indicators')


# Set parameters for querying Census data
indicator_name     = df_params[df_params['Type'] == 'indicator_name' ]['Input'].values[0]


estimate           = df_params[df_params['Type'] == 'estimate'       ]['Input'].values[0]
sample_type        = df_params[df_params['Type'] == 'sample'         ]['Input'].values[0]
geography          = df_params[df_params['Type'] == 'geography'      ]['Input'].values[0]
import_tab         = df_params[df_params['Type'] == 'import_tab'     ]['Input'].values[0]
margin_of_error    = df_params[df_params['Type'] == 'margin_of_error']['Input'].values[0]
year_start         = df_params[df_params['Type'] == 'year_start'     ]['Input'].values[0]
year_end           = df_params[df_params['Type'] == 'year_end'       ]['Input'].values[0]

# Subset to specific indicator
df_indicators = df_indicators[df_indicators['Indicator'] == indicator_name]
percentages = df_indicators['Percentages'        ].values[0]
num_vars    = df_indicators['Number of Variables'].values[0]

# View
print('Indicator name:      ' + indicator_name )
print('Sample:              ' + sample_type    )
print('Estimate:            ' + estimate       )
print('Final geography:     ' + geography      )
print('Import geography:    ' + import_tab     )
print('Margin of error:     ' + margin_of_error)
print('Number of variables: ' + str(num_vars)  )
print('Percentages:         ' + percentages    )
print('Start year:          ' + str(year_start))
print('End year:            ' + str(year_end  ))


print('')
print('Export parameters:' )
print('')


# Set parameters for export file
project     = df_indicators['Project'        ].values[0]
export_loc  = df_indicators['Export Location'].values[0]
folder      = df_indicators['Folder'         ].values[0]
if estimate != 'LEHD':
    MOE_thresh  = df_indicators['MOE Threshold'  ].values[0]
    MOE_thresh = int(MOE_thresh)
    print('MOE threshold: ' + str(MOE_thresh) + '%')

# View
print('Project:             ' + project              )
print('Export Llcation:     ' + export_loc           )
print('Folder name:         ' + folder               )
