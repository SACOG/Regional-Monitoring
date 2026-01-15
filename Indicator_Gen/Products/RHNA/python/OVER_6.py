





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



def re_remove_post(x, exp = ':'):
    try: x = x.split(exp, 1)[0]
    except: pass
    return x

def re_remove_pre(x, exp = ':  '):
    try: x = x.split(exp, 1)[1]
    except: pass
    return x


if __name__ == '__main__':

    indicator = 'RHNA_OVER_6'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Households'
    columns = 'Burden'
    variable = 'Housing Tenure'



    ## Organizing ---

    df_places = pd.read_excel(PATH_DATA / f'{indicator} Places ACS5.xlsx')

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': variable})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()]
    df_places = df_places.reset_index(drop=True)
    df_places['Tenure'  ] = df_places[variable].apply(re_remove_post)
    df_places['Burden'  ] = df_places[variable].apply(re_remove_pre )
    df_places[variable] = df_places['Tenure'].copy()
    df_places['Percentage'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', variable])['Households'].transform('sum')

    df_places = df_places[['County Name', 'Geography', values, variable, columns, 'Percentage']]

    df_places['Sort'] = pd.Categorical(df_places['Burden'], ['0%-30% of income used for housing', '30%-50% of income used for housing', '50% or more of income used for housing', 'Not computed'])
    df_places = df_places.sort_values(['County Name', 'Geography', variable, 'Sort'], ascending=[True, True, True, True])
    df_places = df_places.drop(['Sort'], axis = 1)
    df_places = df_places.reset_index(drop=True)
    # df_places


    counties = list(df_places['County Name'].unique())


    for county in counties:
        
        print();print()
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
            
            color_map = {
                    "0%-30% of income used for housing":"#1F45FC",
                    "30%-50% of income used for housing":"#1E90FF",
                    "50% or more of income used for housing":"#9DC209",
                    "Not computed":"#9B9A96"
            }

            fig = px.bar(df_plot, x=variable, y='Percentage'
                        , color = columns
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

