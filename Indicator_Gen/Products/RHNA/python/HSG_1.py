

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
FILE_DOF = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / 'DOF_E5_and_E8_Jurisdictions.xlsx'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()





if __name__ == '__main__':

    indicator = 'RHNA_HSG_1'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Housing Units'
    columns = 'Year'



    ## Importing
    df_dof = pd.read_excel(FILE_DOF)
    df_dof = df_dof[df_dof['MPO'] == 'SACOG']
    df_dof['MPO'] = df_dof['MPO'] + ' Region'
    df_dof = df_dof[df_dof['Year'].isin([2010, 2020, 2024])]
    df_dof = df_dof.sort_values('Year')
    df_dof['Year'] = df_dof['Year'].astype(str)

    df_dof = df_dof[['County', 'Jurisdiction', 'Year', 'Single Attached', 'Single Detached', 'Two to Four', 'Five Plus', 'Mobile Homes']]

    df_dof = df_dof.melt(id_vars=['County', 'Jurisdiction', 'Year'], var_name='Housing Type', value_name='Housing Units')
    df_dof = df_dof.reset_index(drop=True)

    conditions = [
        df_dof['Housing Type'] == 'Single Attached'
        , df_dof['Housing Type'] == 'Single Detached'
        , df_dof['Housing Type'] == 'Two to Four'    
        , df_dof['Housing Type'] == 'Five Plus'      
        , df_dof['Housing Type'] == 'Mobile Homes'   
    ]

    choices = ['Single Family Attached', 'Single Family Detached', 'Multifamily: Two to Four Units', 'Multifamily: 5+ Units', 'Mobile Homes']

    df_dof['Housing Type'] = np.select(conditions, choices, default='no')

    counties = list(df_dof['County'].unique())

    for county in counties:
        
        print();print()
        print(county)
        time.sleep(2)

        df_dof_sub = df_dof[df_dof['County'] == county]
        jurisdictions = df_dof_sub['Jurisdiction'].unique()

        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_dof_sub[df_dof_sub['Jurisdiction'] == jurisdiction]
            df_prod['Year'] = 'Year ' + df_prod['Year']
            df_prod = df_prod.pivot_table(index=['Housing Type'], columns=columns, values=values).reset_index()

            
            ## Plotting ---

            df_plot = df_dof_sub[df_dof_sub['Jurisdiction'] == jurisdiction]
            
            color_map = {
                    "2010":"#1F45FC",
                    "2020":"#1E90FF",
                    "2024": "#9DC209",
            }

            fig = px.bar(df_plot, x='Housing Type', y=values
                        , color = columns
                        , barmode='group'
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
            # fig.update_layout(legend={'traceorder': 'reversed'})


            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)

