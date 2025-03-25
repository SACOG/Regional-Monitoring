# let's make functions that will import, clean, and shape our data the same way the Delaware guys did it
# https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?counties=06101,06115,06113,06061,06017,06067&years=2023


def get_demographics_new(row):
    demographics = []

    if row['derived_race'] in ['Black or African American', 'White', 'Asian']:
        demographics.append(row['derived_race'])
    else:
        demographics.append('Non-White')

    if row['derived_sex'] in ['Male', 'Female']:
        demographics.append(row['derived_sex'])

    if row['derived_ethnicity'] in ['Not Hispanic or Latino', 'Hispanic or Latino']:
        demographics.append(row['derived_ethnicity'])
    return demographics

def hmda_import(years, counties, dtypes, path_raw):
    '''
    Years can only be from 2018, to 2024. County codes can be found by using the online tool: https://ffiec.cfpb.gov/data-browser/data/2023?category=counties. 
    '''
    print(''); print('Importing data from HDMA...'); print('')

    list_df = []

    for year in tqdm(years):
        if int(year) < 2018 or int(year) > int(datetime.now().year - 1): 
            print(f"Error: the year {year} does not have accessible data.") 
            continue

        url = 'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?counties=' + ','.join(counties) + '&years=' + str(year)
        
        df = pd.read_csv(url, dtype=dtypes)

        list_df.append(df)
    
    df = pd.concat(list_df, ignore_index=True)
    df.to_csv(os.path.join(path_raw, '2018-2023', 'HMDA_raw'), index=False)

    return df


def hmda_process(df):
    '''
    Years can only be from 2018, to 2024. County codes can be found by using the online tool: https://ffiec.cfpb.gov/data-browser/data/2023?category=counties. 
    '''
    
    df = df[df['loan_purpose'].isin([1, 2, 31])]
    df = df[df['action_taken'].isin([1, 3])]
    df['loan_purpose'] = df['loan_purpose'].map({1: 'Home purchase', 2: 'Home improvement', 31: 'Refinancing'})
    df['demographics'] = df.apply(get_demographics_new, axis=1)

    df = df.explode('demographics')

    df['originations'] = df['action_taken'].apply(lambda x: 1 if x == 1 else 0)
    df['denials'     ] = df['action_taken'].apply(lambda x: 1 if x == 3 else 0)

    df_initial = df.groupby(['activity_year', 'county_code', 'demographics', 'loan_purpose']).agg(
        originated=('originations', 'sum'),
        denied=('denials', 'sum')
    ).reset_index()

    df_sums = df_initial.groupby(['activity_year', 'county_code', 'demographics']).agg(
        total_originated=('originated', 'sum'),
        total_denied=('denied', 'sum')
    ).reset_index()

    df_sums['loan_purpose'] = 'All'

    df = pd.concat([df_initial, df_sums[['activity_year', 'county_code', 'loan_purpose', 'demographics', 'total_originated', 'total_denied']]], ignore_index=True)
    df['originations'] = df['originated'].fillna(df['total_originated'])
    df['denials'     ] = df['denied'    ].fillna(df['total_denied'    ])
    df.drop(columns=['total_originated', 'total_denied'], inplace=True)
    df['county_name'] = df['county_code'].map({6101: 'Sutter', 6115: 'Yuba', 6113: 'Yolo', 6061: 'Placer', 6017: 'El Dorado', 6067: 'Sacramento'})
  
    df['total'           ] = df['originations'] + df['denials']
    df['denial_rate'     ] = df['denials'     ] / df['total'  ]
    df['origination_rate'] = df['originations'] / df['total'  ]
    
    df.rename(columns = {'activity_year': 'year', 'county_code': 'county_id','loan_purpose': 'purpose', 'demographics': 'demographic'},inplace = True)

    df = df[['year', 'county_id', 'county_name', 'purpose', 'demographic', 'denials', 'originations', 'total', 'denial_rate', 'origination_rate']]
    
    print(''); print(''); print('Processed HDMA data:')
    display(df.head())
    
    return df


def get_demographics_vintage(row):
    demographics = []
    
    if row['applicant_race_name_1'] in ['Black or African American', 'White', 'Asian']:
        demographics.append(row['applicant_race_name_1'])
    else:
        demographics.append('Non-White')
    # Add gender
    if row['applicant_sex_name'] in ['Male', 'Female']:
        demographics.append(row['applicant_sex_name'])
    # Latino 
    if row['applicant_ethnicity_name'] in ['Not Hispanic or Latino', 'Hispanic or Latino']:
        demographics.append(row['applicant_ethnicity_name'])
    return demographics


def hmda_import_vintage(path, counties, dtype):
    
    print(''); print('Importing vintage HDMA data from local folder...'); print('')
    
    list_df = []

    for file_name in tqdm(os.listdir(path)):
        if file_name.endswith(".csv"):
            file_path = os.path.join(path, file_name)
            
            df = pd.read_csv(file_path, dtype=dtype)
            df = df[df['county_name'].isin(counties)]
            list_df.append(df)
            
    df = pd.concat(list_df)
    
    return df


def hmda_process_vintage(df):

    
    df = df[df['loan_purpose_name'].isin(['Home purchase', 'Home improvement', 'Refinancing'])]
    df = df[df['action_taken'].isin([1, 3])]
    df['loan_purpose'] = df['loan_purpose_name']
    df['demographics'] = df.apply(get_demographics_vintage, axis=1)

    df = df.explode('demographics')
    df['originations'] = df['action_taken'].apply(lambda x: 1 if x == 1 else 0)
    df['denials'     ] = df['action_taken'].apply(lambda x: 1 if x == 3 else 0)

    df_initial = df.groupby(['as_of_year', 'county_name', 'demographics', 'loan_purpose']).agg(
        originated=('originations', 'sum'),
        denied=('denials', 'sum')
    ).reset_index()

    df_sums = df_initial.groupby(['as_of_year', 'county_name', 'demographics']).agg(
        total_originated=('originated', 'sum'),
        total_denied=('denied', 'sum')
    ).reset_index()
    df_sums['loan_purpose'] = 'All'

    df = pd.concat([df_initial, df_sums[['as_of_year', 'county_name', 'loan_purpose', 'demographics', 'total_originated', 'total_denied']]], ignore_index=True)
    df['originations'] = df['originated'].fillna(df['total_originated'])
    df['denials'     ] = df['denied'    ].fillna(df['total_denied'    ])
    df.drop(columns=['total_originated', 'total_denied'], inplace=True)
    df['county_name'] = df['county_name'].map({'Sutter County': 'Sutter', 'Yuba County': 'Yuba', 'Yolo County': 'Yolo', 'Placer County': 'Placer', 'El Dorado County': 'El Dorado', 'Sacramento County': 'Sacramento'})
    df['county_id'  ] = df['county_name'].map({'Sutter': 6101, 'Yuba': 6115, 'Yolo': 6113, 'Placer': 6061, 'El Dorado': 6017, 'Sacramento': 6067})

    df['total'           ] = df['originations'] + df['denials']
    df['denial_rate'     ] = df['denials'     ] / df['total'  ]
    df['origination_rate'] = df['originations'] / df['total'  ]
    
    df.rename(columns = {'as_of_year': 'year', 'loan_purpose': 'purpose', 'demographics': 'demographic'}, inplace = True)

    df = df[['year', 'county_id', 'county_name', 'purpose', 'demographic', 'denials', 'originations', 'total', 'denial_rate', 'origination_rate']]
    
    print(''); print('Processed vintage HDMA data:'); print('')
    display(df.head())
       
    return df



