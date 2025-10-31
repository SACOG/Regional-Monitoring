



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

    indicator = 'RHNA_POPEMP_9'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Population'
    columns = 'Variable'



    ## Organizing ---
    df_places, df_counties, df_mpo = rhna.acs_import(indicator)
    df_places, df_counties, df_mpo = rhna.acs_clean(df_places, df_counties, df_mpo, columns, values)


    counties = df_counties['Geography'].unique()

    for county in counties:
        
        print();print()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):
            
            tqdm.write(jurisdiction)

            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
        
        
            ## Plotting ---
            
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_plot.drop(values, axis=1)
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
                
            color_map  = {
                'Private company workers': '#1F45FC'
                , 'Self-employed workers': '#7E587E'
                , 'Private not-for-profit workers': '#1E90FF'
                , 'Local and state government workers': '#9DC209'
                , 'Federal government workers': '#FBB117'
                , 'Unpaid family workers': '#7FFFD4'
            }
        
            fig = px.bar(df_plot, x='Geography', y='Percentage'
                        , color=columns
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

