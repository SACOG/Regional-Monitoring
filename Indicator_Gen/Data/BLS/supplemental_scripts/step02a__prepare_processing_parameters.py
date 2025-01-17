
# Import objects
file_config = path_config / 'bls_configuration_file.xlsm'
df_indicators = pd.read_excel(file_config, sheet_name = 'Indicators')
df_indicators = df_indicators[df_indicators['Indicator Name'] == indicator_name]


percentages = df_indicators['Percentages'    ].values[0]
export_loc  = df_indicators['Export Location'].values[0]
folder      = df_indicators['Folder'         ].values[0]

print('')
print('Calculate percentages:     ' + percentages)
print('Export location file path: ' + export_loc )
print('Folder name:               ' + folder     )
print('')