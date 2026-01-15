





from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px

PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()




if __name__ == '__main__':

    indicator = 'RHNA_POPEMP_20'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Households'
    columns = 'Tenure'
    variable = 'Race/Ethnicity'


    ## Organizing

    df_places, df_counties, df_mpo = rhna.acs_import(indicator)



    race_ethcnitiy_map = {
    'American Indian or Alaska Native': 'American Indian or Alaska Native'
    , 'Asian': 'Asian'
    , 'Black or African American': 'Black or African American'
    , 'Hispanic or Latino': 'Hispanic or Latino'
    , 'Native Hawaiian or other Pacific Islander': 'Native Hawaiian or other Pacific Islander'
    , 'White (NH)': 'White (NH)'
    , 'Some other race': 'Other race or multiple races'
    , 'Two or more races': 'Other race or multiple races'
    }


    df_places   = df_places  [df_places  ['Race_Ethnicity'] != 'All']
    df_counties = df_counties[df_counties['Race_Ethnicity'] != 'All']
    df_mpo      = df_mpo     [df_mpo     ['Race_Ethnicity'] != 'All']
            
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
    df_counties['NAME'] = df_counties['NAME'].str.replace(', California'     , '', regex=True)

    df_places   = df_places  .rename(columns={'Variable':'Tenure'})
    df_counties = df_counties.rename(columns={'Variable':'Tenure'})
    df_mpo      = df_mpo     .rename(columns={'Variable':'Tenure'})

    df_places   = df_places  .rename(columns={'NAME':'Geography', 'Race_Ethnicity':variable})
    df_counties = df_counties.rename(columns={'NAME':'Geography', 'Race_Ethnicity':variable})
    df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography', 'Race_Ethnicity':variable})
    df_mpo = df_mpo.drop_duplicates()

    df_places   = df_places  [df_places  ['Year'] == df_places  ['Year'].max()]
    df_counties = df_counties[df_counties['Year'] == df_counties['Year'].max()]
    df_mpo      = df_mpo     [df_mpo     ['Year'] == df_mpo     ['Year'].max()]

    df_places  [variable] = df_places  [variable].replace(race_ethcnitiy_map)
    df_counties[variable] = df_counties[variable].replace(race_ethcnitiy_map)# trying to role up to new race/ethnicity mapping, it's new so may not run properly, double check
    df_mpo     [variable] = df_mpo     [variable].replace(race_ethcnitiy_map)

    df_places   = df_places  .groupby(['County Name', 'Geography', columns, variable], as_index=False)['Households'].sum()
    df_counties = df_counties.groupby([               'Geography', columns, variable], as_index=False)['Households'].sum()
    df_mpo      = df_mpo     .groupby([               'Geography', columns, variable], as_index=False)['Households'].sum()

    df_places  ['Percentage'] = df_places  ['Households'] / df_places  .groupby(['County Name', 'Geography', variable])['Households'].transform('sum')
    df_counties['Percentage'] = df_counties['Households'] / df_counties.groupby([               'Geography', variable])['Households'].transform('sum')
    df_mpo     ['Percentage'] = df_mpo     ['Households'] / df_mpo     .groupby([               'Geography', variable])['Households'].transform('sum')

    df_places   = df_places  [['County Name', 'Geography', variable, columns, values, 'Percentage']].reset_index(drop=True)
    df_counties = df_counties[[               'Geography', variable, columns, values, 'Percentage']].reset_index(drop=True)
    df_mpo      = df_mpo     [[               'Geography', variable, columns, values, 'Percentage']].reset_index(drop=True)

    counties = df_counties['Geography'].unique()
    df_counties

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, variable)

            ## Plotting

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            
            color_map  = {
                'Owner occupied': '#1F45FC'
                , 'Renter occupied': '#9DC209'
            }

            fig = px.bar(df_plot, x=variable, y=values
                        , color = columns
                        , barmode='group'
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
        
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

