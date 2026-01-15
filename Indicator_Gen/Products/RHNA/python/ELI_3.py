


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
        
    indicator = 'RHNA_ELI_3'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Population'
    columns = 'Category'
    variable = 'Race/Ethnicity'



    ## Organizing

    df_places = pd.read_excel(PATH_DATA / f'{indicator} Places ACS5.xlsx')

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': variable})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()]
    df_places = df_places.reset_index(drop=True)

    df_places['Category'] = df_places[variable].copy()
    df_places[variable] = df_places['Race_Ethnicity']

    df_places = df_places[['County Name', 'Geography', values, columns, variable, 'Percentage']]
    df_places = df_places.reset_index(drop=True)


    counties = list(df_places['County Name'].unique())


    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places.copy()
        df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, variable)

            ## Plotting ---

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            
            color_map  = {
                'Above poverty level': '#9DC209'
                , 'Below poverty level': '#1F45FC'
            }

            fig = px.bar(df_plot, x=variable, y='Percentage'
                        , color=columns
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")
                
            
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

