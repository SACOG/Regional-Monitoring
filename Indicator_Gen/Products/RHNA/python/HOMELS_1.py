

indicator = 'RHNA_HOMELS_1'


# Set indicator
source = 'HUD'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]


def remove_subtext(x):
    x = x[:-1]
    return x


## Importing ---

path_in = path_i / 'Geospatial Data' / 'HUD'
files = [f for f in path_in.iterdir() if f.is_file()]
files = [f for f in files if '.xlsx' in str(f)]


files_to_geography = {
    'CoC_PopSub_CoC_CA-503-2024_CA_2024':'Sacramento City and County'
    , 'CoC_PopSub_CoC_CA-515-2024_CA_2024': 'Roseville, Rocklin/Placer County'
    , 'CoC_PopSub_CoC_CA-521-2024_CA_2024': 'Davis, Woodland/Yolo County'
    , 'CoC_PopSub_CoC_CA-524-2024_CA_2024': 'Yuba City & County/Sutter County'
    , 'CoC_PopSub_CoC_CA-525-2024_CA_2024': 'El Dorado County'
}




list_df = []
for file in tqdm(files):
    df = pd.read_excel(file, skiprows=2)

    cols_to_keep = ['Unnamed: 0', 'Unnamed: 4', 'Unnamed: 6', 'Unnamed: 12']
    df = df[cols_to_keep]
    df = df.rename(columns={'Unnamed: 0':'Household Type', 'Unnamed: 4':'Sheltered - Emergency Shelter', 'Unnamed: 6':'Sheltered - Transitional Housing', 'Unnamed: 12':'Unsheltered'})

    df = df.dropna()
    str_to_keep = 'Persons in households without children|Persons in households with at least one adult and one child|Persons in households with only children'
    df = df[df['Household Type'].str.contains(str_to_keep)]
    df['Household Type'] = df['Household Type'].apply(remove_subtext)


    df['Geography'] = files_to_geography[file.stem]
    df = df.set_index('Geography').reset_index()
    
    list_df.append(df)

df = pd.concat(list_df)


geographies_to_counties = {
    'Sacramento City and County': ['Sacramento']
    , 'Roseville, Rocklin/Placer County': ['Placer']
    , 'Davis, Woodland/Yolo County': ['Yolo']
    , 'Yuba City & County/Sutter County': ['Yuba', 'Sutter']
    , 'El Dorado County': ['El Dorado']
}


geographies = list(df['Geography'].unique())



for geography in geographies:
    
    print();print()
    
    df_sub = df.copy()
    df_sub = df_sub[df_sub['Geography'] == geography]

    counties = geographies_to_counties[geography]

    for county in counties:

        print(county)

        path_county = path_out / county
        jurisdictions = [str(f.stem) for f in path_county.iterdir()]
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            ## Plotting ---

            df_prod = df_sub.copy()

            df_prod = df_prod.melt(id_vars=['Geography', 'Household Type'], var_name='Variable', value_name='Number of Households')
            df_prod = df_prod.pivot_table(index=['Geography', 'Variable'], columns='Household Type', values='Number of Households').reset_index()
            df_prod = df_prod.drop('Geography', axis=1)
            df_prod = df_prod.sort_values('Variable')
            df_prod = df_prod.reset_index(drop=True)

        
            ## Exporting ---
            if export:
                export_rhna(df_prod)

list_indicators.append(indicator)

