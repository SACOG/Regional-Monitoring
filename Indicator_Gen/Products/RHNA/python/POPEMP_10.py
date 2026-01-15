





import numpy as np
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
    try: x = str(x.split(exp, 1)[0])
    except: pass
    return x

def re_remove_pre(x, exp = ':  '):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x



if __name__ == '__main__':

    indicator = 'RHNA_POPEMP_10'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Population'
    columns = 'Category'
    variable = 'Earnings'


    ## Organizing ---

    df_places_a = pd.read_excel(PATH_DATA / f'{indicator}a Places ACS5.xlsx')
    df_places_b = pd.read_excel(PATH_DATA / f'{indicator}b Places ACS5.xlsx')
    df_places = pd.concat([df_places_a, df_places_b])


    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': variable})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()]
    df_places = df_places.reset_index(drop=True)
    df_places['Category'] = df_places[variable].apply(re_remove_post)
    df_places[variable] = df_places[variable].apply(re_remove_pre )

    df_places = df_places[['County Name', 'Geography', values, columns, variable, 'Percentage']]

    df_places['Sort'] = pd.Categorical(df_places[variable], ['75k or more', '50k to 75k', '25k to 50k', '10k to 25k', 'Less than 10k'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Category', 'Sort'], ascending=[True, True, True, False])
    df_places = df_places.drop(['Sort'], axis = 1)
    df_places = df_places.reset_index(drop=True)

    conditions = [
        df_places[variable] == 'Less than 10k'
        , df_places[variable] == '10k to 25k'
        , df_places[variable] == '25k to 50k'
        , df_places[variable] == '50k to 75k'
        , df_places[variable] == '75k or more'
    ]

    choices = ['Less than $10k', '$10k to $25k', '$25k to $50k', '$50k to $75k', '$75k or more']

    df_places[variable] = np.select(conditions, choices, default = 'no')


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

            ## Plotting

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            
            color_map  = {
                'Place of residence': '#9DC209'
                , 'Place of work': '#1F45FC'
            }

            fig = px.bar(df_plot, x=variable, y=values
                        , color = columns
                        , barmode='group'
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_yaxes(tickprefix='$')
            fig.update_xaxes(tickvals=[0, 1, 2, 3, 4], ticktext=['Less than &#36;10k', '&#36;10k to &#36;25k', '&#36;25k to &#36;50k', '&#36;50k to &#36;75k', '&#36;75k or more'])

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

