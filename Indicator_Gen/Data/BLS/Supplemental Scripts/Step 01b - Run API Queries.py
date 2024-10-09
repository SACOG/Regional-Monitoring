
## Keep track of time amounted while requesting data
start_time = time.time()


print('Importing BLS data using user inputs...')
print('')
print('')

list_df_years = []
year_step = 20


# Loop through the specified range of years in step intervals
for year_range_start in range(year_start, year_end + 1, year_step):
    year_range_end = min(year_range_start + year_step - 1, year_end)
    print('')
    print('Requesting data from ' + str(year_range_start) + ' to ' + str(year_range_end))

    list_df_series = []

    # Iterate through 50 Series ID at a time
    for list_series in list_series_all:

        list_df = []

        # Set up BLS API request
        url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        url_key = '?registrationkey={}'.format(api_key)
        headers = {'Content-type': 'application/json'}
        data = json.dumps({
                    "seriesid": list_series,
                    "startyear": year_range_start,
                    "endyear": year_range_end,
                    "registrationkey": api_key
                    })

        # API request
        response = requests.post('{}{}'.format(url, url_key), headers=headers, data=data).json()

        # Translate information from dictionary results into pandas dataframe
        for i in tqdm(list_series):
            try:
                df = pd.DataFrame.from_dict(response['Results']['series'])
                df = pd.DataFrame.from_dict(df[df['seriesID'] == i]['data'].values[0])
                df = df[['year', 'periodName', 'value']]
                df = df.rename(columns = {'value': i})
                list_df.append(df)
            except Exception as e: print(i); print(e)

        # Combine all column df's together for each set of 50 Series ID's
        df_series = ft.reduce(lambda left, right: pd.merge(left, right, on = ['year', 'periodName'], how = 'left'), list_df)
        list_df_series.append(df_series)

    # Combine all sets of 50 series ID df's
    df_years = ft.reduce(lambda left, right: pd.merge(left, right, on = ['year', 'periodName'], how = 'left'), list_df_series)
    list_df_years.append(df_years)

# Combine all data from all years together
df_bls_raw = pd.concat(list_df_years)
df_bls_raw = df_bls_raw.drop_duplicates()
df_bls_raw = df_bls_raw.reset_index(drop = True)


## Calculate time amounted while requesting data
print("")
print("Finished!!")
print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
print('')


## Summary of data quality
print('')
print('Summary of data quality: ')
print('')
print("Count of '-555555555'   values in dataframe: " + str((df_bls_raw.values == '-555555555'  ).sum()))
print("Count of '-666666666'   values in dataframe: " + str((df_bls_raw.values == '-666666666'  ).sum()))
print("Count of '-222222222'   values in dataframe: " + str((df_bls_raw.values == '-222222222'  ).sum()))
print("Count of '-999999999.0' values in dataframe: " + str((df_bls_raw.values == '-999999999.0').sum()))
print("Count of 'null'         values in dataframe: " + str((df_bls_raw.values == 'null'        ).sum()))
print("Count of '-'            values in dataframe: " + str((df_bls_raw.values == '-'           ).sum()))
print("Count of ''             values in dataframe: " + str((df_bls_raw.values == ''            ).sum()))
print("Count of NaN            values in dataframe: " + str(df_bls_raw.isna().sum()              .sum()))
print('')


## View result
print('')
print('Number of rows/columns: ')
print(df_bls_raw.shape)
pd.set_option('display.max_columns', None)
display(df_bls_raw.head(3), df_bls_raw.tail(3))
