
# Create empty lists to store pulled data
list_df_state    = []
list_df_counties = []
list_df_cities   = []
list_df_balance  = []



# Import 1 decade at a time
# 2000-2010 data is organized differently than 2010-2024
for year, file_dof in dict_years.items():

    print(f"Importing data from the {year}'s...")

    if year == 2000:

        # Pull data using url and custom user agent
        # Drop missings, convert date field, create year field
        # Fill in county and city fields (the excel data sheet just has missings where it should be city/county)
        # Separate out and roll up population/household totals by city/county/balance
        # San francisco is special case that needs to be manually adjusted

        df = pd.read_excel(file_dof, sheet_name=1, skiprows=2)
        df = df.dropna(subset = ['Household'])
        df['Date'] = pd.to_datetime(df['Date'])
        df['Year'] = df['Date'].dt.year
        
        # Initialize 'County' and 'City' columns
        df['County'] = np.nan
        df['City'  ] = np.nan
        
        county_temp = None
        
        # Reset index
        df = df.reset_index(drop=True)
        
        for i in range(len(df)):
            if pd.notnull(df.loc[i, 'County / City']):
                if county_temp is not None:
                    df.loc[i, 'County'] = county_temp
                    df.loc[i, 'City'] = df.loc[i, 'County / City']
                    county_temp = None
                else:
                    county_temp = df.loc[i, 'County / City']
        
        df['County'] = df['County'].fillna(method='ffill')
        df['City'  ] = df['City'  ].fillna(method='ffill')

        # shift up and then fill the last row
        df['County'] = df['County'].shift(-1)
        df['City'  ] = df['City'  ].shift(-1)

        df['County'] = df['County'].fillna(method='ffill')
        df['City'  ] = df['City'  ].fillna(method='ffill')

        df = df.drop(columns = ['County / City'])

        df = df[df['Year'] != 2010]

        df = df.rename(columns={'Household': 'Household Population'
                                  , 'Total'  : 'Population'
                                  , 'Total.1': 'Housing Units'})
        
        df['Unoccupied'] = df['Housing Units'] - df['Occupied']
        df = df[['County', 'City', 'Date', 'Year', 'Population', 'Household Population', 'Group Quarters', 
                                  'Housing Units', 'Single'    , 'Multiple'            , 'Mobile Homes'  , 'Occupied', 'Unoccupied',
                                   'Vacancy Rate', 'Persons Per Household']].rename(columns={'Persons Per Household':'Persons per Household'})
        
        df_state = df[df['County'] == 'California'].rename(columns={'County':'State'})
        df       = df[df['County'] != 'California']
        df = df.merge(df_fips[['County Name', 'MPO']], left_on='County', right_on='County Name', how='left').drop('County Name', axis=1)
        df.loc[df['MPO'].isna(), 'MPO'] = 'Rest of CA'
        
        # Subset
        df_sf = df[df['County'] == 'San Francisco']
        df_sf.loc[:, 'City'] = 'County Total'
        df = pd.concat([df, df_sf])
        df['City'] = df['City'].str.replace(' City', '')
        df = df[~df['Year'].isna()]
        df_cities   = df[~df['City'].isin(['County Total', 'Incorporated', 'Balance of County'])].reset_index(drop=True)
        df_counties = df[ df['City'].str.contains('County Total'     )].reset_index(drop=True).drop('City', axis=1)
        df_balance  = df[ df['City'].str.contains('Balance of County')].reset_index(drop=True).drop('City', axis=1)
        
        list_df_state   .append(df_state   )
        list_df_counties.append(df_counties)
        list_df_cities  .append(df_cities  )
        list_df_balance .append(df_balance )

    else:

        # Pull data using url and custom user agent
        # Drop missings, convert date field, create year field
        # Separate out and roll up population/household totals by city/county/balance
        # San francisco is special case that needs to be manually adjusted

        df = pd.read_excel(file_dof, sheet_name=1, skiprows=2)
        df['Date'] = pd.to_datetime(df['Date'])
        df['Year'] = df['Date'].dt.year
        if year == 2010:
            df = df[df['Year'] != 2020]

        df = df.rename(columns={'Household': 'Household Population'
                                , 'Total'  : 'Population'
                                , 'Total.1': 'Housing Units'})
        if year == 2010:
            cols_to_int = ['Population', 'Household Population', 'Group Quarters', 'Housing Units', 'Single Detached', 'Single Attached',
                            'Two to Four', 'Five Plus', 'Mobile Homes', 'Occupied', 'Vacancy Rate', 'Persons per Household']
            df[cols_to_int] = df[cols_to_int].apply(pd.to_numeric, errors='coerce')
            df = df.dropna()

        df['Unoccupied'] = df['Housing Units'  ] - df['Occupied'       ]
        df['Single'    ] = df['Single Attached'] + df['Single Detached']
        df['Multiple'  ] = df['Two to Four'    ] + df['Five Plus'      ]

        df = df[['County', 'City', 'Date', 'Year', 'Population', 'Household Population', 'Group Quarters', 
                                    'Housing Units', 'Single'    , 'Single Detached'     , 'Single Attached', 'Multiple',
                                    'Two to Four', 'Five Plus' , 'Mobile Homes'        ,
                                        'Occupied', 'Unoccupied', 'Vacancy Rate'        , 'Persons per Household']]

        df_state = df[df['County'] == 'California'].rename(columns = {'County':'State'})
        df       = df[df['County'] != 'California']
        df = df.merge(df_fips[['County Name', 'MPO']], left_on='County', right_on='County Name', how='left').drop('County Name', axis=1)
        df.loc[df['MPO'].isna(), 'MPO'] = 'Rest of CA'

        # Subset
        if year == 2020:
            df_sf = df[df['County'] == 'San Francisco']
            df_sf.loc[:, 'City'] = 'San Francisco'
            df = pd.concat([df, df_sf])

        if year == 2010:
            df_sf = df[df['County'] == 'San Francisco']
            df_sf.loc[:, 'City'] = 'County Total'
            df = pd.concat([df, df_sf])
        df = df[~df['City'].isna()]
        df['City'] = df['City'].str.replace(' City', '')
        df = df[~df['Year'].isna()]
        df_cities   = df[~df['City'].isin(['County Total', 'Incorporated', 'Balance of County'])].reset_index(drop=True)
        df_counties = df[ df['City'].str.contains('County Total'     )].reset_index(drop=True).drop('City', axis=1)
        df_balance  = df[ df['City'].str.contains('Balance of County')].reset_index(drop=True).drop('City', axis=1)
        
        list_df_state   .append(df_state   )
        list_df_counties.append(df_counties)
        list_df_cities  .append(df_cities  )
        list_df_balance .append(df_balance )
            

df_state    = pd.concat(list_df_state   )
df_counties = pd.concat(list_df_counties)
df_cities   = pd.concat(list_df_cities  )
df_balance  = pd.concat(list_df_balance )

df_state    = df_state   .sort_values(['City'  , 'Year'], ascending=[True, False]).rename(columns={'City':'Jurisdiction'})
df_counties = df_counties.sort_values(['County', 'Year'], ascending=[True, False])
df_cities   = df_cities  .sort_values(['City'  , 'Year'], ascending=[True, False]).rename(columns={'City':'Jurisdiction'})
df_balance  = df_balance .sort_values(['County', 'Year'], ascending=[True, False])


df_counties = df_counties.set_index(['MPO', 'County'                ]).reset_index()
df_cities   = df_cities  .set_index(['MPO', 'County', 'Jurisdiction']).reset_index()
df_balance  = df_balance .set_index(['MPO', 'County'                ]).reset_index()


print(); print()
print('By State')
print(df_state.head())
print('By Counties')
print(df_counties.head())
print('By Cities')
print(df_cities.head())
print('By Balance')
print(df_balance.head())