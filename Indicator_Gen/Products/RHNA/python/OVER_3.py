






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

    indicator = 'RHNA_OVER_3'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Households'
    columns = 'Race_Ethnicity'



    ## Organizing ---
    df_places, df_counties, df_mpo = rhna.acs_import(indicator)

    df_places   = df_places  [(df_places  ['Race_Ethnicity'] != 'All') & (df_places  ['Variable'] == 'More than occupant per room')].reset_index(drop=True)
    df_counties = df_counties[(df_counties['Race_Ethnicity'] != 'All') & (df_counties['Variable'] == 'More than occupant per room')].reset_index(drop=True)
    df_mpo      = df_mpo     [(df_mpo     ['Race_Ethnicity'] != 'All') & (df_mpo     ['Variable'] == 'More than occupant per room')].reset_index(drop=True)

    df_places, df_counties, df_mpo = rhna.acs_clean(df_places, df_counties, df_mpo, columns, values)


    counties = df_counties['Geography'].unique()

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):
                    
            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub=df_counties_sub, df_mpo=df_mpo)
            
            ## Plotting ---
            
            # df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction].copy()
            df_plot = df_plot.drop('Households', axis=1)
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            df_plot['Sort'] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG'])
            df_plot['Sort_eth'] = pd.Categorical(df_plot['Race_Ethnicity'], [
                'American Indian or Alaska Native'
                , 'Native Hawaiian or other Pacific Islander'
                , 'Other race or multiple races'
                , 'Black or African American'
                , 'Asian'
                , 'Hispanic or Latino'
                , 'White (NH)'
            ])
            df_plot = df_plot.sort_values(['Sort', 'Sort_eth'], ascending=[True, False])
            df_plot = df_plot.drop(['Sort', 'Sort_eth'], axis=1)

            color_map  = {
                'American Indian or Alaska Native': '#E56717'
                , 'Native Hawaiian or other Pacific Islander': '#006A4E'
                , 'Other race or multiple races': '#7E587E'
                , 'Black or African American': '#FBB117'
                , 'Asian': '#9DC209'
                , 'Hispanic or Latino': '#1E90FF'
                , 'White (NH)': '#1F45FC'
            }
        
            fig = px.bar(
                df_plot
                , x=columns
                , y='Percentage'
                , color=columns
                # , facet_col='Geography'
                , color_discrete_map=color_map
                # , barmode='group'
            )
            
            fig.update_yaxes(ticksuffix='%')
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")
            fig.update_layout(xaxis={'showticklabels': False})
            fig.update_layout(bargap=0, bargroupgap=0)

        
            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

