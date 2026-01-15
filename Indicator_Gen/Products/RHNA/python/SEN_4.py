


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

    indicator = 'RHNA_SEN_4'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'Population'
    variable = 'Disability Type'



    ## Organizing

    df_places, df_counties, df_mpo = rhna.acs_import(indicator)
    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': variable})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()]
    df_places = df_places.reset_index(drop=True)


    df_places['Category'] = df_places[variable].copy()
    df_places['Category'] = df_places['Category'].str.replace('With a ', '')
    df_places['Category'] = df_places['Category'].str.replace('With an ', '')
    df_places['Category'] = df_places['Category'].str.replace('No ', '')
    df_places['Category'] = df_places['Category'].str.replace(' difficulty', '')

    df_places['Percentage'] = df_places['Population'] / df_places.groupby(['County Name', 'Geography', 'Category'])['Population'].transform('sum')

    df_places = df_places[~df_places[variable].str.contains('No')]
    df_places = df_places[['County Name', 'Geography', variable,  values, 'Percentage']].drop_duplicates()


    df_places['Sort'] = pd.Categorical(df_places[variable], ['With an ambulatory difficulty', 'With an independent living difficulty', 'With a hearing difficulty'
                                                            , 'With a self-care difficulty', 'With a cognitive difficulty', 'With a vision difficulty'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Sort'], ascending=[True, True, True])
    df_places = df_places.drop(['Sort'], axis = 1)
    df_places = df_places.reset_index(drop=True)

    counties = list(df_places['County Name'].unique())


    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places.copy()
        df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod0 = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_prod = df_prod0[[variable, values      ]].drop_duplicates()
            df_pct  = df_prod0[[variable, 'Percentage']].drop_duplicates()
            df_plot = df_pct.copy()
            df_plot['Percentage'] = round(df_plot['Percentage'] * 100, 1)

            ## Plotting ---

            fig = px.bar(df_plot, x=variable, y='Percentage')
            fig.update_traces(marker_color='#1E90FF')
            fig.update_traces(hovertemplate="%{y}")
            fig.update_yaxes(ticksuffix='%')

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)


