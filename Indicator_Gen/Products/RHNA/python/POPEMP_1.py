





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

    indicator = 'RHNA_POPEMP_1'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    base_year = 2001


    # DOF E5 Population time-series, with growth rate relative to 1990
    # Compare Jurisdictions to County and MPO



    ## Organizing ---

    df_places, df_counties, df_mpo = rhna.dof_import(indicator)
    df_places, df_counties, df_mpo = rhna.dof_clean(df_places, df_counties, df_mpo)

    counties = df_counties['Geography'].unique()

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.dof_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)
        
            ## Plotting ---

            df_plot1, df_plot2, df_plot3 = rhna.dof_index(df_places_sub, df_counties_sub, df_mpo, jurisdiction)
            df_prod = rhna.dof_pivot(indicator, df_plot1, county, jurisdiction, df_plot2, df_plot3)

            df_plot2['Geography'] = df_plot2['Geography'] + ' County'
            df_plot = pd.concat([df_plot1, df_plot2, df_plot3])
            df_plot = df_plot.drop(['County', 'Population'], axis=1).rename(columns = {'growth': 'Percent Difference'})
            df_plot['Percentage Difference'] = round(df_plot['Percent Difference'], 1)
                
            color_map  = {
                'SACOG Region': '#9DC209'
                , f'{county} County': '#1E90FF'
                , jurisdiction: '#FBB117'
            }
        
            fig = px.line(df_plot, x='Year', y='Percent Difference', markers=True
                            , color = 'Geography'
                            , color_discrete_map=color_map)
            
            # title = f'<b>{plot_title}</b>'

            range_min = df_plot['Percent Difference'].min()-4
            range_max = df_plot['Percent Difference'].max()+4
            range_diff = abs(range_max-range_min)
            if range_diff <= 10:
                dtick = 1
            elif (range_diff > 10) & (range_diff <= 50):
                dtick = 5
            elif (range_diff > 50) & (range_diff <= 100):
                dtick = 10
            elif (range_diff > 100) & (range_diff <= 200):
                dtick = 25
            else:
                dtick = 50
            fig.update_yaxes(ticksuffix='%', dtick=dtick, range = [range_min, range_max])
            year_min = df_plot['Year'].min()-0.5
            year_max = df_plot['Year'].max()+0.5
            fig.update_xaxes(dtick=1, range = [year_min, year_max])
            fig.update_traces(hovertemplate="%{y}")
        

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)

