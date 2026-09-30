

incorporated = {
    'El Dorado': ['Placerville']
    , 'Placer': ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville']
    , 'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento']
    , 'Sutter': ['Live Oak', 'Yuba City']
    , 'Yolo': ['Davis', 'West Sacramento', 'Winters', 'Woodland']
    , 'Yuba': ['Marysville', 'Wheatland']
}

def assign_county_to_jurisdiction(df, incorporated, county_col, jurisdiction_col):
    for county, jurisdiction in incorporated.items():
        df.loc[df[jurisdiction_col] == jurisdiction, county_col] = county
    return df

