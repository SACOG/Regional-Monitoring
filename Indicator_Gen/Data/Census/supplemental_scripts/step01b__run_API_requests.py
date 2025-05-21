
print(); print(); print()
## Keep track of time amounted while requesting data
start_time = time.time()


## Import Census Bureau data to url mapping table
df_urls = pd.read_excel(os.path.join(path_config, 'census_configuration_file2.xlsx'), sheet_name = 'URL')


## API Request Scripts
path_request = path_code / 'supplemental_scripts' / 'requests'

# For ACS tables
if sample_type == 'ACS':
    path_request = path_request / 'ACS.py'
    
# For SUBJECT tables
if sample_type == 'SUBJECT':
    path_request = path_request / 'SUBJECT.py'

# For DEC tables
if estimate == 'DEC':
    path_request = path_request / 'DEC.py'

# For PUMS tables
if geography == 'PUMA':
    path_request = path_request / 'PUMS.py'

# For CPS Tables
if estimate == 'CPS':
    path_request = path_request / 'CPS.py'

# For LEHD Tables
if sample_type == 'LEHD':
    path_request = path_request / 'LEHD.py'

with path_request.open("r") as f:
    exec(f.read())


## Calculate time amounted while requesting data
print()
print("Finished!!")
print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
print()


## Summary of data quality
print()
print('Summary of data quality: ')
print()
print("Count of '-555555555'   values in dataframe: " + str((df_census_raw.values == '-555555555'  ).sum()))
print("Count of '-666666666'   values in dataframe: " + str((df_census_raw.values == '-666666666'  ).sum()))
print("Count of '-222222222'   values in dataframe: " + str((df_census_raw.values == '-222222222'  ).sum()))
print("Count of '-999999999.0' values in dataframe: " + str((df_census_raw.values == '-999999999.0').sum()))
print("Count of 'null'         values in dataframe: " + str((df_census_raw.values == 'null'        ).sum()))
print("Count of '-'            values in dataframe: " + str((df_census_raw.values == '-'           ).sum()))
print("Count of ''             values in dataframe: " + str((df_census_raw.values == ''            ).sum()))
print("Count of NaN            values in dataframe: " + str(df_census_raw.isna().sum()              .sum()))
print()


## View result
print()
print('Number of rows/columns: ')
print(df_census_raw.shape)
print('Years imported: ')
print(df_census_raw.Year.unique())
display(df_census_raw)
