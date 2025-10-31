


import pandas as pd
from pathlib import Path
from tqdm import tqdm
import yaml
import plotly.express as px

PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
PATH_GEO = Path(r'I:\Projects\Josh\RHNA\Geospatial Data')
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'General' / 'RHNA' / 'Final Products'



import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()





if __name__ == '__main__':


    ## Organizing POPEMP_3

    indicator = 'RHNA_POPEMP_3'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Population'
    columns = 'Race_Ethnicity'


    df_places, df_counties, df_mpo = rhna.acs_import(indicator)

    race_ethcnitiy_map = {
    'American Indian or Alaska Native (NH)': 'American Indian, Alaska Native, or Indigenous'
    , 'Asian (NH)': 'Asian or Asian American'
    , 'Black or African American (NH)': 'Black, African American, or African'
    , 'Hispanic or Latino': 'Hispanic/Latina/e/o Only'
    , 'Native Hawaiian or other Pacific Islander (NH)': 'Native Hawaiian or Other Pacific Islander'
    , 'White (NH)': 'White'
    , 'Some other race (NH)': 'Other race or multiple races'
    , 'Two or more races (NH)': 'Other race or multiple races'
    }

    counties_to_geographies_map = {
        'Sacramento County':'Sacramento City and County'
        , 'Placer County': 'Roseville, Rocklin/Placer County'
        , 'Yolo County': 'Davis, Woodland/Yolo County'
        , 'Yuba County': 'Yuba City & County/Sutter County'
        , 'Sutter County': 'Yuba City & County/Sutter County'
        , 'El Dorado County': 'El Dorado County'
    }


    df_places   = df_places  [df_places  ['Race_Ethnicity'] != 'All']
    df_counties = df_counties[df_counties['Race_Ethnicity'] != 'All']
    df_mpo      = df_mpo     [df_mpo     ['Race_Ethnicity'] != 'All']

    df_places, df_counties, df_mpo = rhna.acs_clean(df_places, df_counties, df_mpo, columns, values)

    df_counties[columns] = df_counties[columns].replace(race_ethcnitiy_map)# trying to role up to new race/ethnicity mapping, it's new so may not run properly, double check
    df_counties['Geography'] = df_counties['Geography'].replace(counties_to_geographies_map)# trying to role up to new race/ethnicity mapping, it's new so may not run properly, double check

    df_counties = df_counties.groupby(['Geography', columns], as_index=False)['Population'].sum()
    df_counties['Percentage'] = df_counties['Population'] / df_counties.groupby(['Geography'])['Population'].transform('sum')

    df_counties = df_counties.rename(columns={'Population':'Overall population', 'Percentage':'Share of overall population'})




    ## Organizing HOMELS_2

    indicator = 'RHNA_HOMELS_2'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]

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

    race_ethcnitiy_map = {
    'American Indian, Alaska Native, or Indigenous': 'American Indian, Alaska Native, or Indigenous'
    , 'Asian or Asian American': 'Asian or Asian American'
    , 'Black, African American, or African': 'Black, African American, or African'
    , 'Hispanic/Latina/e/o Only': 'Hispanic/Latina/e/o Only'
    , 'Middle Eastern or North African': 'Other race or multiple races'
    , 'Native Hawaiian or Other Pacific Islander': 'Native Hawaiian or Other Pacific Islander'
    , 'White': 'White'
    , 'Hispanic and One or More Race': 'Other race or multiple races'
    , 'Non-Hispanic and Multiple Race': 'Other race or multiple races'
    }


    list_df = []
    for file in tqdm(files):
        df = pd.read_excel(file, skiprows=30)

        cols_to_keep = ['Unnamed: 2', 'Total']
        df = df[cols_to_keep]
        df = df.rename(columns={'Unnamed: 2':'Race_Ethnicity'})

        df = df.dropna()
        df = df[df['Race_Ethnicity'] != 'Total']

        df['Race_Ethnicity'] = df['Race_Ethnicity'].replace(race_ethcnitiy_map)
        df = df.groupby('Race_Ethnicity', as_index=False)['Total'].sum()

        df['Geography'] = files_to_geography[file.stem]
        df = df.set_index('Geography').reset_index()

        df['Percentage'] = df['Total'] / df.groupby('Geography')['Total'].transform('sum')
        
        list_df.append(df)

    df = pd.concat(list_df)
    df = df.rename(columns={'Total':'Homeless population', 'Percentage':'Share of homeless population'})
    df = df.merge(df_counties, on=['Geography', 'Race_Ethnicity'], how='left')


    geographies_to_counties = {
        'Sacramento City and County': ['Sacramento']
        , 'Roseville, Rocklin/Placer County': ['Placer']
        , 'Davis, Woodland/Yolo County': ['Yolo']
        , 'Yuba City & County/Sutter County': ['Yuba', 'Sutter']
        , 'El Dorado County': ['El Dorado']
    }


    geographies = list(df['Geography'].unique())



    for geography in geographies:
        
        rhna.print2()
        
        df_sub = df.copy()
        df_sub = df_sub[df_sub['Geography'] == geography]

        counties = geographies_to_counties[geography]

        for county in counties:

            print(county)

            path_county = PATH_OUT / county
            jurisdictions = [str(f.stem) for f in path_county.iterdir()]
            
            for jurisdiction in tqdm(jurisdictions, position=0):

                tqdm.write(jurisdiction)

                ## Plotting ---

                df_prod = df_sub[['Race_Ethnicity', 'Homeless population', 'Overall population']]
                df_pct  = df_sub[['Race_Ethnicity', 'Share of homeless population', 'Share of overall population']]

                df_plot = df_pct.melt(id_vars='Race_Ethnicity', var_name='Prop', value_name='Percentage')

                df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
                
                color_map  = {
                    'Share of homeless population': '#9DC209'
                    , 'Share of overall population': '#1F45FC'
                }

                fig = px.bar(df_plot, x='Race_Ethnicity', y='Percentage'
                            , color = 'Prop'
                            , barmode='group'
                            , color_discrete_map=color_map)
                
                fig.update_traces(hovertemplate="%{y}")
                fig.update_yaxes(ticksuffix='%')

                rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
                rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

