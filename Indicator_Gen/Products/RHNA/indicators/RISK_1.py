

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna


yaml_file = rhna.load_yaml()
PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_AREA = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'config' / 'area_codes.xlsx'
FILE_RISK = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' /  'CA Housing Partnership.xlsx'


def chp_clean(df_chp):

    df_chp['MPO'] = 'SACOG Region'
    df_chp.loc[df_chp['Risk Level'] == 'HIgh', 'Risk Level'] = 'High'
    df_chp['County'] = df_chp['County'] + ' County'

    df_mpo      = df_chp.groupby(['MPO'           , 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'MPO':'Geography'})
    df_counties = df_chp.groupby(['County'        , 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'County':'Geography'})
    df_places   = df_chp.groupby(['County', 'City', 'Risk Level'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'City':'Geography'})

    df_mpo2      = df_chp.groupby(['MPO'           ], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'MPO':'Geography'})
    df_counties2 = df_chp.groupby(['County'        ], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'County':'Geography'})
    df_places2   = df_chp.groupby(['County', 'City'], as_index=False).agg(affordable_units=('Affordable Units', 'sum')).rename(columns={'City':'Geography'})

    df_mpo2     ['Risk Level'] = 'Total Assisted Units in Database'
    df_counties2['Risk Level'] = 'Total Assisted Units in Database'
    df_places2  ['Risk Level'] = 'Total Assisted Units in Database'

    df_mpo      = pd.concat([df_mpo     , df_mpo2     ])
    df_counties = pd.concat([df_counties, df_counties2])
    df_places   = pd.concat([df_places  , df_places2  ])

    df_mpo      = df_mpo     .merge(df_mpo2     .drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=[          'Geography'], how='left')
    df_counties = df_counties.merge(df_counties2.drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=[          'Geography'], how='left')
    df_places   = df_places  .merge(df_places2  .drop('Risk Level', axis=1).rename(columns={'affordable_units':'total_affordable_units'}), on=['County', 'Geography'], how='left')

    df_mpo     ['Percent'] = df_mpo     ['affordable_units']/df_mpo     ['total_affordable_units']
    df_counties['Percent'] = df_counties['affordable_units']/df_counties['total_affordable_units']
    df_places  ['Percent'] = df_places  ['affordable_units']/df_places  ['total_affordable_units']

    df_mpo      = df_mpo     .drop('total_affordable_units', axis=1)
    df_counties = df_counties.drop('total_affordable_units', axis=1)
    df_places   = df_places  .drop('total_affordable_units', axis=1)

    return df_chp, df_places, df_counties, df_mpo


def chp_pivot(df_places_sub, jurisdiction, df_counties_sub, df_mpo):

    df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
    if 'Percent' in df_places_sub.columns:
        df_prod = df_prod.drop('Percent', axis=1)
    df_prod = df_prod.pivot_table(index='Geography', columns='Risk Level', values='affordable_units').reset_index()
    df_prod = df_prod.melt(id_vars=['Geography'], var_name='Risk Level', value_name='Affordable Units')
    df_prod = df_prod.pivot_table(index='Risk Level', columns='Geography', values='Affordable Units').reset_index()
    df_prod['Sort'] = pd.Categorical(df_prod['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
    df_prod = df_prod.sort_values(['Sort']).drop(['Sort'], axis=1)

    if 'Percent' in df_places_sub.columns:
        df_pct = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
        df_pct = df_pct.drop('affordable_units', axis=1)
        df_pct = df_pct.pivot_table(index='Geography', columns='Risk Level', values='Percent').reset_index()
        df_pct = df_pct.melt(id_vars=['Geography'], var_name='Risk Level', value_name='Percent')
        df_pct = df_pct.pivot_table(index='Risk Level', columns='Geography', values='Percent').reset_index()
        df_pct['Sort'] = pd.Categorical(df_pct['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
        df_pct = df_pct.sort_values(['Sort']).drop(['Sort'], axis=1)

    if jurisdiction == 'Sacramento':
        print()
        print('Final Product:')
        display(df_prod.head())
        print()

    return df_prod, df_pct



if __name__ == '__main__':

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

    df_chp, df_places, df_counties, df_mpo = chp_clean(df_chp)

    counties = df_counties['Geography'].unique()

    for county in counties:

        print('\n'*2)
        print(county)
        print()
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography'  ] == county]
        df_places_sub   = df_places  [df_places  ['County'     ] == county]

        df_places_sub = df_places_sub.drop('County', axis=1)
        df_places_sub   = df_places_sub  .reset_index(drop=True)
        df_counties_sub = df_counties_sub.reset_index(drop=True)
        
        jurisdictions = df_places_sub['Geography'].unique()

        
        for jurisdiction in tqdm(jurisdictions, position=0):
            
            tqdm.write(jurisdiction)

            df_chp_sub = df_chp[df_chp['City']==jurisdiction].reset_index(drop=True)
            df_chp_sub = df_chp_sub[['Risk Level', 'Name', 'Address', 'Affordable Units', 'Total Units', 'Active Program(s)', 'Estimated Affordability End Year/Date', 'Notes']]
            
            df_prod, df_pct = chp_pivot(df_places_sub, jurisdiction, df_counties_sub, df_mpo)
            df_prod = rhna.cols_geo_rename(df_prod, params['Columns'].split('<>'), county, jurisdiction)
            df_pct  = rhna.cols_geo_rename(df_pct , params['Columns'].split('<>'), county, jurisdiction)

            df_plot = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df_plot = df_plot[df_plot['Risk Level'] != 'Total Assisted Units in Database']
            df_plot = df_plot.drop('affordable_units', axis=1)
            df_plot['Percent of Assisted Units'] = round(df_plot['Percent']*100, 1)

            df_plot['sort_risk'] = pd.Categorical(df_plot['Risk Level'], ['Low', 'Moderate', 'High', 'Very High', 'Total Assisted Units in Database'])
            df_plot['sort_geo' ] = pd.Categorical(df_plot['Geography'], [jurisdiction, county, 'SACOG Region'])
            df_plot = df_plot.sort_values(['sort_geo', 'sort_risk']).reset_index(drop=True).drop(['sort_geo', 'sort_risk'], axis=1)
            
            color_map  = {
                'Low': '#1F45FC'
                , 'Moderate': '#9DC209'
                , 'High': '#FBB117'
                , 'Very High': '#DC381F'
            }
        
            fig = px.bar(df_plot, x='Geography', y='Percent of Assisted Units'
                        , color = 'Risk Level'
                        , color_discrete_map=color_map)
            
            fig.update_yaxes(dtick=10, ticksuffix='%', range = [0,102])
            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)
            rhna.write_sup_table(df_chp_sub, INDICATOR, county, jurisdiction)


