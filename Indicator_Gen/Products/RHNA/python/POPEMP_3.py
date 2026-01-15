






import pandas as pd
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

    indicator = 'RHNA_POPEMP_3'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Population'
    columns = 'Race_Ethnicity'


    ## Organizing ---

    df_places, df_counties, df_mpo = rhna.acs_import(indicator)

    race_ethcnitiy_map = {
    'American Indian or Alaska Native (NH)': 'American Indian or Alaska Native (NH)'
    , 'Asian (NH)': 'Asian (NH)'
    , 'Black or African American (NH)': 'Black or African American (NH)'
    , 'Hispanic or Latino': 'Hispanic or Latino'
    , 'Native Hawaiian or other Pacific Islander (NH)': 'Native Hawaiian or other Pacific Islander (NH)'
    , 'White (NH)': 'White (NH)'
    , 'Some other race (NH)': 'Other race or multiple races (NH)'
    , 'Two or more races (NH)': 'Other race or multiple races (NH)'
    }

    df_places   = df_places  [df_places  ['Race_Ethnicity'] != 'All']
    df_counties = df_counties[df_counties['Race_Ethnicity'] != 'All']
    df_mpo      = df_mpo     [df_mpo     ['Race_Ethnicity'] != 'All']

    df_places, df_counties, df_mpo = rhna.acs_clean(df_places, df_counties, df_mpo, columns, values)

    df_places  [columns] = df_places  [columns].replace(race_ethcnitiy_map)
    df_counties[columns] = df_counties[columns].replace(race_ethcnitiy_map)# trying to role up to new race/ethnicity mapping, it's new so may not run properly, double check
    df_mpo     [columns] = df_mpo     [columns].replace(race_ethcnitiy_map)

    df_places   = df_places  .groupby(['County Name', 'Geography', columns], as_index=False)['Population'].sum()
    df_counties = df_counties.groupby([               'Geography', columns], as_index=False)['Population'].sum()
    df_mpo      = df_mpo     .groupby([               'Geography', columns], as_index=False)['Population'].sum()

    df_places  ['Percentage'] = df_places  ['Population'] / df_places  .groupby(['County Name', 'Geography'])['Population'].transform('sum')
    df_counties['Percentage'] = df_counties['Population'] / df_counties.groupby([               'Geography'])['Population'].transform('sum')
    df_mpo     ['Percentage'] = df_mpo     ['Population'] / df_mpo     .groupby([               'Geography'])['Population'].transform('sum')


    counties = df_counties['Geography'].unique()

    for county in counties:
        
        rhna.print2()
        print(county)
        print()
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            tqdm.write(jurisdiction)
            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub=df_counties_sub, df_mpo=df_mpo)
            
            ## Plotting ---
            
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_plot.drop('Population', axis=1)
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            df_plot['Sort'] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG'])
            df_plot['Sort_eth'] = pd.Categorical(df_plot['Race_Ethnicity'], [
                'American Indian or Alaska Native (NH)'
                , 'Native Hawaiian or other Pacific Islander (NH)'
                , 'Other race or multiple races (NH)'
                , 'Black or African American (NH)'
                , 'Asian (NH)'
                , 'Hispanic or Latino'
                , 'White (NH)'
            ])
            df_plot = df_plot.sort_values(['Sort', 'Sort_eth'], ascending=[True, False])
            df_plot = df_plot.drop(['Sort', 'Sort_eth'], axis=1)
                
            color_map  = {
                'American Indian or Alaska Native (NH)': '#E56717'
                , 'Native Hawaiian or other Pacific Islander (NH)': '#006A4E'
                , 'Other race or multiple races (NH)': '#7E587E'
                , 'Black or African American (NH)': '#FBB117'
                , 'Asian (NH)': '#9DC209'
                , 'Hispanic or Latino': '#1E90FF'
                , 'White (NH)': '#1F45FC'
            }
        
            fig = px.bar(df_plot, x='Geography', y='Percentage'
                        , color = columns
                        , color_discrete_map=color_map)
            
            # title = f'<b>{plot_title}</b>'
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")
        

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

