





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

    indicator = 'RHNA_POPEMP_17'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Households'
    columns = 'Year'
    df_places2 = pd.read_excel(PATH_DATA / f'{indicator} Places ACS5.xlsx', sheet_name='Places')
    df_places1 = pd.read_excel(PATH_DATA / f'{indicator} Places DEC.xlsx', sheet_name='Places')


    ## Organizing

    df_places1['NAME'] = df_places1['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places1['NAME'] = df_places1['NAME'].str.replace(' city, California', '', regex=True)
    df_places2['NAME'] = df_places2['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places2['NAME'] = df_places2['NAME'].str.replace(' city, California', '', regex=True)

    df_places1 = df_places1.rename(columns={'NAME':'Geography'})
    df_places2 = df_places2.rename(columns={'NAME':'Geography'})

    df_places1 = df_places1[['County Name', 'Geography', 'Year', 'Variable', 'Households']]
    df_places2 = df_places2[['County Name', 'Geography', 'Year', 'Variable', 'Households']]

    df_places1 = df_places1.pivot_table(index=['County Name', 'Geography', 'Year'], columns='Variable', values='Households').reset_index()
    df_places1['Owner occupied'] = df_places1['Total'] - df_places1['Renter occupied']
    df_places1 = df_places1.drop('Total', axis=1)
    df_places1 = df_places1.melt(id_vars=['County Name', 'Geography', 'Year'], var_name='Variable', value_name='Households')

    df_places = pd.concat([df_places1, df_places2])


    df_places['Percentage'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', 'Year'])['Households'].transform('sum')

    df_places['Year'] = df_places['Year'].astype(str)
    df_places['Year'] = 'Year ' + df_places['Year']


    counties = df_places['County Name'].unique()

    for county in counties:
        
        rhna.print2()
        print(county); print()
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        df_places_sub = df_places_sub.drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            tqdm.write(jurisdiction)
            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction]

            df_prod = df_prod.drop('Geography', axis=1)
            df_prod = df_prod.pivot_table(index='Variable', columns=columns, values='Households').reset_index()
            df_prod = df_prod.reset_index(drop=True)

            df_pct = df_pct.drop('Geography', axis=1)
            df_pct = df_pct.pivot_table(index='Variable', columns=columns, values='Percentage').reset_index()
            df_pct = df_pct.reset_index(drop=True)
            

            ## Plotting
            
            df_plot = df_pct.melt(id_vars=['Variable'], var_name='Year', value_name='Percentage')
            df_plot['Year'] = df_plot['Year'].str.replace('Year ', '')
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            df_plot = df_plot.sort_values(['Year'], ascending=[True])
                
            color_map  = {
                'Owner occupied': '#1F45FC'
                , 'Renter occupied': '#9DC209'
            }
    
            fig = px.bar(df_plot, x='Year', y='Percentage'
                        , color='Variable'
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")
        
        
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

