





import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px

PATH_DATA = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()




if __name__ == '__main__':

    indicator = 'RHNA_POPEMP_2'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Population'
    columns = 'Race_Ethnicity'
    df_places2 = pd.read_excel(PATH_DATA / f'{indicator} Places ACS5.xlsx' , sheet_name='Places')
    df_places1 = pd.read_excel(PATH_DATA / f'{indicator} Places DEC.xlsx', sheet_name='Places')


    ## Organizing ---


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

    df_places1 = df_places1[df_places1['Race_Ethnicity'] != 'All']
    df_places2 = df_places2[df_places2['Race_Ethnicity'] != 'All']

    df_places1['NAME'] = df_places1['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places1['NAME'] = df_places1['NAME'].str.replace(' city, California', '', regex=True)
    df_places2['NAME'] = df_places2['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places2['NAME'] = df_places2['NAME'].str.replace(' city, California', '', regex=True)

    df_places1 = df_places1.rename(columns={'NAME':'Geography'})
    df_places2 = df_places2.rename(columns={'NAME':'Geography'})

    df_places1 = df_places1[['County Name', 'Geography', 'Year', columns, values, 'Percentage']]
    df_places2 = df_places2[['County Name', 'Geography', 'Year', columns, values, 'Percentage']]

    df_places1[columns] = df_places1[columns].replace(race_ethcnitiy_map)
    df_places2[columns] = df_places2[columns].replace(race_ethcnitiy_map)

    df_places1 = df_places1.groupby(['County Name', 'Geography', 'Year', columns], as_index=False)['Population'].sum()
    df_places2 = df_places2.groupby(['County Name', 'Geography', 'Year', columns], as_index=False)['Population'].sum()

    df_places1['Percentage'] = df_places1['Population'] / df_places1.groupby(['County Name', 'Geography', 'Year'])['Population'].transform('sum')
    df_places2['Percentage'] = df_places2['Population'] / df_places2.groupby(['County Name', 'Geography', 'Year'])['Population'].transform('sum')

    df_places = pd.concat([df_places1, df_places2])

    counties = df_places['County Name'].unique()

    for county in counties:
        
        rhna.print2()
        print(county)
        print()
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        df_places_sub = df_places_sub.drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            tqdm.write(jurisdiction)
            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction]

            df_prod = df_prod.drop('Geography', axis=1)
            df_prod = df_prod.pivot_table(index='Year', columns=columns, values=values).reset_index()
            df_prod = df_prod.sort_values(['Year'])
            df_prod = df_prod.reset_index(drop=True)

            df_pct = df_pct.drop('Geography', axis=1)
            df_pct = df_pct.pivot_table(index='Year', columns=columns, values='Percentage').reset_index()
            df_pct = df_pct.sort_values(['Year'])
            df_pct = df_pct.reset_index(drop=True)
            

            ## Plotting ---
            
            df_plot = df_pct.melt(id_vars=['Year'], var_name='Race_Ethnicity', value_name='Percentage')
            df_plot['Year'] = df_plot['Year'].astype(str)
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            df_plot['Sort_eth'] = pd.Categorical(df_plot['Race_Ethnicity'], [
                'American Indian or Alaska Native (NH)'
                , 'Native Hawaiian or other Pacific Islander (NH)'
                , 'Other race or multiple races (NH)'
                , 'Black or African American (NH)'
                , 'Asian (NH)'
                , 'Hispanic or Latino'
                , 'White (NH)'
            ])
            df_plot = df_plot.sort_values(['Year', 'Sort_eth'], ascending=[True, False])
            df_plot = df_plot.drop(['Sort_eth'], axis=1)
                
            color_map  = {
                'American Indian or Alaska Native (NH)': '#E56717'
                , 'Native Hawaiian or other Pacific Islander (NH)': '#006A4E'
                , 'Other race or multiple races (NH)': '#7E587E'
                , 'Black or African American (NH)': '#FBB117'
                , 'Asian (NH)': '#9DC209'
                , 'Hispanic or Latino': '#1E90FF'
                , 'White (NH)': '#1F45FC'
            }
        
            fig = px.bar(df_plot, x='Year', y='Percentage'
                        , color=columns
                        , color_discrete_map=color_map)
            
            # title = f'<b>{plot_title}</b>'
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")
        

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

