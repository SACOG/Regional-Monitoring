
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
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x



if __name__ == '__main__':
        
    indicator = 'RHNA_DISAB_3'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Population'
    columns = 'Category'


    ## Organizing
    df_places = pd.read_excel(PATH_DATA / f'{indicator} Places ACS5.xlsx')

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()]
    df_places = df_places.reset_index(drop=True)
    df_places['Category'] = df_places['Variable'].apply(re_remove_post)
    df_places['Variable'] = df_places['Variable'].apply(re_remove_pre )
    df_places['Percentage'] = df_places[values] / df_places.groupby(['County Name', 'Geography', 'Variable'])[values].transform('sum')

    df_places = df_places[['County Name', 'Geography', values, columns, 'Variable', 'Percentage']]

    df_places['Sort'] = pd.Categorical(df_places['Variable'], ['With a disability', 'No disability'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Category', 'Sort'], ascending=[True, True, True, True])
    df_places = df_places.drop(['Sort'], axis = 1)
    df_places = df_places.reset_index(drop=True)


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

            df_prod, df_pct = rhna.acs_pivot(indicator, df_places_sub, county, jurisdiction, columns, values)

            ## Plotting ---

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            
            color_map  = {
                'Employed': '#1F45FC'
                , 'Unemployed': '#9DC209'
            }

            fig = px.bar(df_plot, x='Variable', y='Percentage'
                        , color=columns
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_layout(legend={'traceorder': 'reversed'})
            

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

