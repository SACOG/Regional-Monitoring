



import numpy as np
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

    indicator = 'RHNA_HSG_9'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Households'
    columns = 'Variable'



    ## Organizing

    df_places, df_counties, df_mpo = rhna.acs_import(indicator)
    df_places, df_counties, df_mpo = rhna.acs_clean(df_places, df_counties, df_mpo, columns, values)

    counties = df_counties['Geography'].unique()

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)
                    
            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
        
        
            ## Plotting
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_plot.drop(values, axis=1)
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            conditions = [
                df_plot[columns] == "Rent less than 500"
                , df_plot[columns] == "Rent 500-1,000"
                , df_plot[columns] == "Rent 1,000-1,500"
                , df_plot[columns] == "Rent 1,500-2,000"
                , df_plot[columns] == "Rent 2,000-2,500"
                , df_plot[columns] == "Rent 2,500-3,000"
                , df_plot[columns] == "Rent 3,000 or more"
            ]

            choices = ['Rent less than &#36;500', 'Rent &#36;500-&#36;1,000', 'Rent &#36;1,000-&#36;1,500', 'Rent &#36;1,500-&#36;2,000', 'Rent &#36;2,000-&#36;2,500', 'Rent &#36;2,500-&#36;3,000', 'Rent &#36;3,000 or more']
            df_plot[columns] = np.select(conditions, choices, default='no')
            
            color_map = {
                    "Rent less than &#36;500":"#1F45FC",
                    "Rent &#36;500-&#36;1,000"    :"#1E90FF",
                    "Rent &#36;1,000-&#36;1,500"  :"#9DC209",
                    "Rent &#36;1,500-&#36;2,000"  :"#FBB117",
                    "Rent &#36;2,000-&#36;2,500"  :"#7E587E",
                    "Rent &#36;2,500-&#36;3,000"  :"#DC381F",
                    "Rent &#36;3,000 or more":"#006A4E"
            }
            
            fig = px.bar(df_plot, x='Geography', y='Percentage'
                        , color = columns
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")
    

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

