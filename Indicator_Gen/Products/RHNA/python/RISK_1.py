




import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px


FILE_AREA = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'config' / 'area_codes.xlsx'
FILE_RISK = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' /  'CA Housing Partnership.xlsx'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()





if __name__ == '__main__':

    indicator = 'RHNA_RISK_1'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']
    values = 'affordable_units'
    columns = 'Risk Level'


    list_chp = []
    counties = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']
    for county in counties:
        df = pd.read_excel(FILE_RISK, sheet_name=county)
        df['County'] = county
        list_chp.append(df)

    df_chp = pd.concat(list_chp)


    df_area = pd.read_excel(FILE_AREA, sheet_name='CDPcodes')
    df_area = df_area[(df_area['Year']==2020) & (df_area['Incorporated'] == 'Yes')]
    df_area['NAME'] = df_area['NAME'].str.replace(' CDP' , '', regex=True)
    df_area['NAME'] = df_area['NAME'].str.replace(' city', '', regex=True)
    df_area['NAME'] = df_area['NAME'].str.replace(' town', '', regex=True)


    df_chp['City'] = df_chp['City'].str.title()
    df_chp.loc[df_chp['City'] == 'Unincorporated Santa Cruz', 'City'] = 'Live Oak' # This needs a manual correction, seems like some manual checks are needed each time
    df_chp.loc[~df_chp['City'].isin(df_area.NAME.unique()), 'City'] = 'Unincorporated'


    df_places, df_counties, df_mpo = rhna.chp_clean(df_chp)



    counties = df_counties['Geography'].unique()

    for county in counties:

        print();print()
        print(county); print()
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.chp_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()

        
        for jurisdiction in tqdm(jurisdictions, position=0):
            
            tqdm.write(jurisdiction)
                
            df_prod, df_pct = rhna.chp_pivot(indicator, df_places_sub, county, jurisdiction, columns, values, df_counties_sub, df_mpo)
            df_prod = df_prod[['Geography', 'Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database']]
            df_pct  = df_pct [['Geography', 'Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database']]

        
            ## Plotting
            
            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_plot[df_plot['Risk Level'] != 'Total Assisted Units in Database']
            df_plot = df_plot.drop(values, axis=1)
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)

            df_plot['sort_risk'] = pd.Categorical(df_plot['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
            df_plot['sort_geo' ] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_plot = df_plot.sort_values(['sort_geo', 'sort_risk']).reset_index(drop=True).drop(['sort_geo', 'sort_risk'], axis=1)
            
            color_map  = {
                'Low': '#1F45FC'
                , 'Moderate': '#9DC209'
                , 'High': '#FBB117'
                , 'Very High': '#DC381F'
            }
        
            fig = px.bar(df_plot, x='Geography', y='Percentage'
                        , color = columns
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)




## Code graveyard ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# indicator = 'RHNA_RISK_1'

# source='temp'
# with path_func.open("r") as f: exec(f.read())

# counties = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']

# dt_juris = {
#     'El Dorado': ['Placerville', 'South Lake Tahoe', 'Unincorporated'],
#     'Placer': ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville', 'Unincorporated'],
#     'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento', 'Unincorporated'],
#     'Sutter': ['Live Oak', 'Yuba City', 'Unincorporated'],
#     'Yolo': ['Davis', 'West Sacramento', 'Winters', 'Woodland', 'Unincorporated'],
#     'Yuba': ['Marysville', 'Wheatland', 'Unincorporated']
# }


# print()
# for county in counties:
#     print(county)
#     for jurisdiction in dt_juris[county]:
#         export_rhna_temp()



