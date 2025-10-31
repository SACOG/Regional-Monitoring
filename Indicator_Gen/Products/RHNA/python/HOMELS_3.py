




import pandas as pd
from pathlib import Path
from tqdm import tqdm

PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'General' / 'RHNA' / 'Final Products'
PATH_GEO = Path(r'I:\Projects\Josh\RHNA\Geospatial Data')


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()


def remove_subtext(x):
    x = x[:-1]
    return x


if __name__ == '__main__':
        
    indicator = 'RHNA_HOMELS_3'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]


    ## Importing

    path_in = PATH_GEO / 'HUD'
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
        df = pd.read_excel(file, skiprows=58)

        if file.stem == 'CoC_PopSub_CoC_CA-503-2024_CA_2024':
            cols_to_keep = ['Summary of all other populations reported:', 'Unnamed: 7', 'Unnamed: 9', 'Unnamed: 13']
        else:
            cols_to_keep = ['Summary of all other populations reported:', 'Unnamed: 7', 'Unnamed: 9', 'Unnamed: 12']
        
        df = df[cols_to_keep]

        if file.stem == 'CoC_PopSub_CoC_CA-503-2024_CA_2024':
            df = df.rename(columns={'Summary of all other populations reported:':'Population Characteristic', 'Unnamed: 7':'Sheltered - Emergency Shelter', 'Unnamed: 9':'Sheltered - Transitional Housing', 'Unnamed: 13':'Unsheltered'})
        else:
            df = df.rename(columns={'Summary of all other populations reported:':'Population Characteristic', 'Unnamed: 7':'Sheltered - Emergency Shelter', 'Unnamed: 9':'Sheltered - Transitional Housing', 'Unnamed: 12':'Unsheltered'})

        df = df.dropna()
        str_to_keep = 'Severely Mentally Ill|Chronic Substance Abuse|HIV/AIDS|Veterans|Victims of Domestic Violence'
        df = df[df['Population Characteristic'].str.contains(str_to_keep)]

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

            path_county = PATH_OUT / county
            jurisdictions = [str(f.stem) for f in path_county.iterdir()]
            
            for jurisdiction in tqdm(jurisdictions, position=0):

                tqdm.write(jurisdiction)

                ## Plotting
                df_prod = df_sub.copy()

                df_prod = df_prod.melt(id_vars=['Geography', 'Population Characteristic'], var_name='Variable', value_name='Number of Households')
                df_prod = df_prod.pivot_table(index=['Geography', 'Variable'], columns='Population Characteristic', values='Number of Households').reset_index()
                df_prod = df_prod.drop('Geography', axis=1)
                df_prod = df_prod.sort_values('Variable')
                df_prod = df_prod.reset_index(drop=True)

                rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)


