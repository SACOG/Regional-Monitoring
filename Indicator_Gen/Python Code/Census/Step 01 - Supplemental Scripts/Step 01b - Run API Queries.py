
## Keep track of time amounted while requesting data
start_time = time.time()


## Import Census Bureau data to url mapping table
df_urls = pd.read_excel(os.path.join(path_config, 'Census Configuration File.xlsx'), sheet_name = 'URL')


## API Request Scripts

# For ACS tables
if sample_type == 'ACS':
    exec(open(os.path.join(path_code, 'Step 01 - Supplemental Scripts', 'Queries', 'ACS.py')).read())

# For SUBJECT tables
if sample_type == 'SUBJECT':
    exec(open(os.path.join(path_code, 'Step 01 - Supplemental Scripts', 'Queries', 'SUBJECT.py')).read())

# For DEC tables
if estimate == 'DEC':
    exec(open(os.path.join(path_code, 'Step 01 - Supplemental Scripts', 'Queries', 'DEC.py')).read())

# For PUMS tables
if geography == 'PUMA':
    exec(open(os.path.join(path_code, 'Step 01 - Supplemental Scripts', 'Queries', 'PUMS.py')).read())

# For CPS Tables
if estimate == 'CPS':
    exec(open(os.path.join(path_code, 'Step 01 - Supplemental Scripts', 'Queries', 'CPS.py')).read())

# For LEHD Tables
if estimate == 'LEHD':
    exec(open(os.path.join(path_code, 'Step 01 - Supplemental Scripts', 'Queries', 'LEHD.py')).read())


## Calculate time amounted while requesting data
print("")
print("Finished!!")
print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
print('')


## Summary of data quality
print('')
print('Summary of data quality: ')
print('')
print("Count of '-555555555'   values in dataframe: " + str((df_census_raw.values == '-555555555'  ).sum()))
print("Count of '-666666666'   values in dataframe: " + str((df_census_raw.values == '-666666666'  ).sum()))
print("Count of '-999999999.0' values in dataframe: " + str((df_census_raw.values == '-999999999.0').sum()))
print("Count of 'null'         values in dataframe: " + str((df_census_raw.values == 'null'        ).sum()))
print("Count of '-'            values in dataframe: " + str((df_census_raw.values == '-'           ).sum()))
print("Count of ''             values in dataframe: " + str((df_census_raw.values == ''            ).sum()))
print("Count of NaN            values in dataframe: " + str(df_census_raw.isna().sum()              .sum()))
print('')


## View result
print('')
print('Number of rows/columns: ')
print(df_census_raw.shape)
print('Years imported: ')
print(df_census_raw.Year.unique())
pd.set_option('display.max_columns', None)
display(df_census_raw.head(3), df_census_raw.tail(3))
