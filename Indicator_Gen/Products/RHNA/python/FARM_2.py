



import pandas as pd
from pathlib import Path
from tqdm import tqdm
import plotly.express as px


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
FILE_FARMWORKERS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / 'USDA' / 'USDA_FarmWorkers_Summarized.xlsx'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()



if __name__ == '__main__':
        
    indicator = 'RHNA_FARM_2'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']

    ## Organizing

    df_usda = pd.read_excel(FILE_FARMWORKERS)


    counties = list(df_usda['County'].unique())


    for county in counties:

        print(county)

        path_county = PATH_OUT / county
        jurisdictions = [str(f.stem) for f in path_county.iterdir()]

        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_usda[df_usda['County'] == county]
            df_prod = df_prod.drop('County', axis=1)


            ## Plotting ---

            df_plot = df_prod.copy()
            df_plot = df_prod.melt(id_vars='Farm Worker', var_name='Year', value_name='Number of Workers')
            df_plot['Year'] = df_plot['Year'].str.replace('Year ', '')
            
            color_map = {
                    "2002":"#1F45FC",
                    "2007":"#1E90FF",
                    "2012":"#9DC209",
                    "2017":"#FBB117",
                    "2022":"#DC381F"
            }

            fig = px.bar(df_plot, x='Farm Worker', y='Number of Workers'
                        , color = 'Year'
                        , color_discrete_map=color_map
                        , barmode='group')
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.175,xanchor="right", x=0.55))


            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)


