


import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px
from IPython.display import display


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
FILE_SCHOOLS = Path(r'I:/Projects/Warren/Schools_data_update/2024_Data/Data_Cleaning/Sch_Combined') / 'SACOG_Schools_Merged_Data_Final.csv'
FILE_AREA = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'  / 'config' / 'area_codes.xlsx'
FILE_CDP = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\geojson') / 'tl_2022_us_place_SACOG.geojson'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()




def clean_years(df):
    
    df['2020-21'] = df['2020-21'].astype(int)
    df['2021-22'] = df['2021-22'].astype(int)
    df['2022-23'] = df['2022-23'].astype(int)
    df['2023-24'] = df['2023-24'].astype(int)

    return df





if __name__ == '__main__':
        
    indicator = 'RHNA_HOMELS_4'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']


    # Use URLs to import enrollment total files
    urls = [
        'https://www3.cde.ca.gov/demo-downloads/homeless/hse2324.txt'
        , 'https://www3.cde.ca.gov/demo-downloads/homeless/hse2223.txt'
        , 'https://www3.cde.ca.gov/demo-downloads/homeless/hse2122.txt'
        , 'https://www3.cde.ca.gov/demo-downloads/homeless/hse2021.txt'
        ]


    list_df_edu = []

    for url in tqdm(urls):

        df_edu = pd.read_csv(url, sep='\t', encoding='latin-1')
        # df_edu = df_edu.rename(columns={'ï»¿AcademicYear':'AcademicYear'})
        df_edu.columns = ['AcademicYear'] + list(df_edu.columns[1:])

        df_edu = df_edu[df_edu['County Name'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba'])]
        df_edu = df_edu[df_edu['Aggregate Level'] == 'S']

        list_df_edu.append(df_edu)
        time.sleep(3)


    df_edu = pd.concat(list_df_edu)
    df_edu = df_edu[['AcademicYear', 'County Name', 'School Name', 'Homeless Student Enrollment']]
    

    # Import the schools layer
    gdf_schools = pd.read_csv(FILE_SCHOOLS)
    gdf_schools['cdscode'] = gdf_schools['cdscode'].astype(str)
    gdf_schools = gdf_schools[gdf_schools['latitude' ] != 'No Data']
    gdf_schools = gdf_schools[gdf_schools['longitude'] != 'No Data']
    gdf_schools = gdf_schools.reset_index(drop=True)
    geometry = gpd.points_from_xy(gdf_schools['longitude'], gdf_schools['latitude'])
    gdf_schools = gpd.GeoDataFrame(gdf_schools, geometry=geometry, crs="EPSG:4326")
    gdf_schools = gdf_schools.to_crs("EPSG:2226")
    gdf_schools = gdf_schools[['cdscode', 'county',  'school', 'geometry']]
    gdf_schools = gdf_schools.rename(columns={'school':'School Name', 'county':'County Name'})


    # Merge schools with enrollment total files to get geometries
    df_edu = df_edu.merge(gdf_schools, on=['County Name', 'School Name'], how='left')

    gdf_edu = gpd.GeoDataFrame(
        df_edu,
        geometry='geometry',
        crs="EPSG:2226"
    )

    # print(len(gdf_edu[gdf_edu['cdscode'].isna()]['SchoolName'].unique())) # some schools are missing
    gdf_edu['Homeless Student Enrollment'] = gdf_edu['Homeless Student Enrollment'].replace('*', '0')
    gdf_edu['Homeless Student Enrollment'] = gdf_edu['Homeless Student Enrollment'].astype(int)


    # Roll up enrollment to SACOG region and county level enrollment totals
    df_counties = gdf_edu.groupby(['AcademicYear', 'County Name'], as_index=False)['Homeless Student Enrollment'].sum()
    df_sacog    = gdf_edu.groupby(['AcademicYear'               ], as_index=False)['Homeless Student Enrollment'].sum()
    df_counties = df_counties.rename(columns={'County Name':'Geography'})
    df_sacog['Geography'] = 'SACOG Region'


    # Intersect schools file with CDP polygon file to get jurisdiction level enrollment totals
    gdf_cdp = gpd.read_file(FILE_CDP)
    gdf_cdp = gdf_cdp[['GEOID', 'NAME', 'geometry']].rename(columns = {'GEOID':'place_id'})
    df_places = gpd.overlay(gdf_edu, gdf_cdp, how='intersection', keep_geom_type=False)

    df_area = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
    df_area['place'] = df_area['place'].astype(str).apply('{:0>5}'.format)
    df_area = df_area[(df_area['MPO'].str.contains('SACOG')) & (df_area['Incorporated'] != 'Yes') & (df_area['Year'] == 2020)]
    unincorporated_places = list(df_area['place'].unique())
    df_places['place_id'] = df_places['place_id'].str[2:].astype(str).apply('{:0>5}'.format)
    df_places.loc[df_places['place_id'].isin(unincorporated_places), 'NAME'] = 'Unincorporated'

    df_places = df_places.groupby(['AcademicYear', 'County Name', 'NAME'], as_index=False)['Homeless Student Enrollment'].sum()
    df_places = df_places.rename(columns={'NAME':'Geography'})


    # Combine
    df_places   = df_places  .pivot_table(index = ['County Name', 'Geography'], columns='AcademicYear', values='Homeless Student Enrollment').reset_index()
    df_counties = df_counties.pivot_table(index = [               'Geography'], columns='AcademicYear', values='Homeless Student Enrollment').reset_index()
    df_sacog    = df_sacog   .pivot_table(index = [               'Geography'], columns='AcademicYear', values='Homeless Student Enrollment').reset_index()

    df_places   = df_places  .fillna(0)
    df_counties = df_counties.fillna(0)
    df_sacog    = df_sacog   .fillna(0)


    df_places   = clean_years(df_places  )
    df_counties = clean_years(df_counties)
    df_sacog    = clean_years(df_sacog   )

    df_places = df_places.sort_values(['County Name', 'Geography'])
    df_places = df_places[~((df_places['County Name'] == 'Sacramento') & (df_places['Geography'] == 'Roseville'))]

    df_places   = df_places  .reset_index(drop=True)
    df_counties = df_counties.reset_index(drop=True)
    df_sacog    = df_sacog   .reset_index(drop=True)

    display(df_places  .head())
    display(df_counties.head())
    display(df_sacog   .head())



    # Organize and export
    counties = list(df_counties['Geography'].unique())

    for county in counties:

        rhna.print2()
        print(county)
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography'] == county]
        df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'

        df_places_sub = df_places[df_places['County Name'] == county]
        df_places_sub = df_places_sub.drop('County Name', axis=1)

        df_places_sub   = df_places_sub  .reset_index(drop=True)
        df_counties_sub = df_counties_sub.reset_index(drop=True)

        jurisdictions = list(df_places_sub['Geography'].unique())

        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_sacog])
            df_prod = df_prod.reset_index(drop=True)

            ## Plotting ---

            df_plot = df_prod.copy()
            df_plot = df_prod.melt(id_vars='Geography', var_name='Year', value_name='County')
            
            color_map = {
                    "2020-21":"#1F45FC",
                    "2021-22":"#1E90FF",
                    "2022-23":"#9DC209",
                    "2023-24":"#FBB117"
            }

            fig = px.bar(df_plot, x='Geography', y='County'
                        , color = 'Year'
                        , color_discrete_map=color_map
                        , barmode='group')
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.175,xanchor="right", x=0.75))
                
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)


