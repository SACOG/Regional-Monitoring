



import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import yaml
import plotly.express as px
from IPython.display import display


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
FILE_INCOME = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data') / 'Income_1 Counties ACS5.xlsx'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()


def org_ami(df):

    df = df[['Geography', 'Variable', 'Households']]

    conditions = [
        df['Variable'] == 'Less than $10,000'
        , df['Variable'] == '$10,000 to $14,999'
        , df['Variable'] == '$15,000 to $24,999'
        , df['Variable'] == '$25,000 to $34,999'
        , df['Variable'] == '$35,000 to $49,999'
        , df['Variable'] == '$50,000 to $74,999'
        , df['Variable'] == '$75,000 to $99,999'
        , df['Variable'] == '$100,000 to $149,999'
        , df['Variable'] == '$150,000 to $199,999'
        , df['Variable'] == '$200,000 or more'
    ]

    choices = ['0_9999', '10000_14999', '15000_24999', '25000_34999', '35000_49999', '50000_74999', '75000_99999', '100000_149999', '150000_199999', '200000_999999']
    df['bounds'] = np.select(conditions, choices, default=0)

    return df

def proc_ami(df, hh_bracket_acs, dt_hcd_brackets, hh_bracket_hcd, list_df_sub):
    
    df_sub = df.copy()
    df_sub = df_sub[df_sub['Variable'] == hh_bracket_acs]

    hh_sub = df_sub['Households'].values[0]

    low_acs = int(df_sub['bounds'].str.split('_').values[0][0])
    hi_acs  = int(df_sub['bounds'].str.split('_').values[0][1])

    low_hcd = dt_hcd_brackets[hh_bracket_hcd][0]
    hi_hcd  = dt_hcd_brackets[hh_bracket_hcd][1]

    if hi_hcd < hi_acs:
        if hi_hcd > low_acs:
            hh_sub = ((hi_hcd-low_acs)/(hi_acs-low_acs))*hh_sub
        else: 
            hh_sub = 0

    if low_hcd > low_acs:
        if low_hcd < hi_acs:
            hh_sub = ((hi_acs-low_hcd)/(hi_acs-low_acs))*hh_sub 
        else:
            hh_sub = 0

    if low_hcd > hi_acs:
        hh_sub = 0

    if hh_bracket_acs == '$200,000 or more' and hh_bracket_hcd == 'High income: >120 pct of AMI':
        hh_sub = df_sub['Households'].values[0]

    if hh_sub > 0:
        df_sub['HCD_var'] = hh_bracket_hcd
        df_sub['HH_adj' ] = round(hh_sub)
        df_sub['HCD_brack'] = str(dt_hcd_brackets[hh_bracket_hcd])
        list_df_sub.append(df_sub)
       
    return list_df_sub






if __name__ == '__main__':
        
    indicator = 'RHNA_ELI_4'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']


    ## Organizing

    df_places, df_counties, df_mpo = rhna.acs_import(indicator)

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()]
    df_places = df_places.reset_index(drop=True)

    df_places = df_places[['County Name', 'Geography', 'Variable', 'Households']].drop_duplicates()

    counties = list(df_places['County Name'].unique())


    df_counties_ami = pd.read_excel(FILE_INCOME, sheet_name='Counties')
    df_counties_ami = df_counties_ami[df_counties_ami['Race_Ethnicity'] == 'All']
    df_counties_ami = df_counties_ami[df_counties_ami['Year'] == df_counties_ami['Year'].max()]


    for county in counties:

        df_ami = df_counties_ami[df_counties_ami['County Name'] == county]
        ami = df_ami['Median Household Income'].values[0]

        dt_hcd_brackets = {
            'Acutely low income: 0-15 pct of AMI': [0, ami*0.15]
            , 'Extremely low income: 15-30 pct of AMI': [ami*0.15, ami*0.3]
            , 'Very low income: 30-50 pct of AMI': [ami*0.3, ami*0.5]
            , 'Lower income: 50-80 pct of AMI': [ami*0.5, ami*0.8]
            , 'Moderate income: 80 to 120 pct of AMI': [ami*0.8, ami*1.2]
            , 'High income: >120 pct of AMI': [ami*1.2, ami*10]
        }

        rhna.print2()
        print(county)

        print('County AMI: ', ami)
        display(dt_hcd_brackets)
        time.sleep(2)

        df_places_sub = df_places.copy()
        df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()

        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df = org_ami(df)

            list_brackets_acs = list(df['Variable'].unique())
            list_brackets_hcd = list(dt_hcd_brackets.keys())

            list_df_var_places = []

            for hh_bracket_acs in list_brackets_acs:

                list_df_sub_places = []

                for hh_bracket_hcd in list_brackets_hcd:
                    
                    list_df_sub_places = proc_ami(df, hh_bracket_acs, dt_hcd_brackets, hh_bracket_hcd, list_df_sub_places)
                        
                if not list_df_sub_places:
                    print('no df_sub')
                else:
                    df_sub_places_all = pd.concat(list_df_sub_places)
                    list_df_var_places.append(df_sub_places_all)

            df2 = pd.concat(list_df_var_places)

            if round(df['Households'].sum()) != round(df2['HH_adj'].sum()):
                tqdm.write(f'Something wrong - Before: {df['Households'].sum()}, After: {df2['HH_adj'].sum()}')

            df = df2.groupby(['HCD_var'], as_index=False).agg(HH_adj=('HH_adj', 'sum'))

            sort_hcd = ['Acutely low income: 0-15 pct of AMI', 'Extremely low income: 15-30 pct of AMI', 'Very low income: 30-50 pct of AMI', 
                        'Lower income: 50-80 pct of AMI', 'Moderate income: 80 to 120 pct of AMI', 'High income: >120 pct of AMI']
            
            df['HCD_var_sort'] = pd.Categorical(df['HCD_var'], sort_hcd)

            df = df.sort_values('HCD_var_sort', ascending=True)
            df = df.drop('HCD_var_sort', axis=1)

            df['Percentage'] = df['HH_adj'] / df['HH_adj'].sum()

            conditions = [
                        df['HCD_var'] == 'Acutely low income: 0-15 pct of AMI', 
                        df['HCD_var'] == 'Extremely low income: 15-30 pct of AMI', 
                        df['HCD_var'] == 'Very low income: 30-50 pct of AMI', 
                        df['HCD_var'] == 'Lower income: 50-80 pct of AMI', 
                        df['HCD_var'] == 'Moderate income: 80 to 120 pct of AMI', 
                        df['HCD_var'] == 'High income: >120 pct of AMI']
            
            choices = ['Acutely low income', 'Extremely low income', 'Very low income', 'Lower income', 'Moderate income', 'High income']
            df['HCD_var'] = np.select(conditions, choices, default='no')

            df = df.rename(columns={'HCD_var':'Income Bracket', 'HH_adj':'Households'})

            df_prod = df[['Income Bracket', 'Households']]
            df_pct  = df[['Income Bracket', 'Percentage']]

            df_plot = df_pct.copy()
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)


            ## Plotting

            fig = px.bar(df_plot, x='Income Bracket', y='Percentage')
            fig.update_traces(marker_color='#1E90FF')
            fig.update_yaxes(ticksuffix='%')
            fig.update_traces(hovertemplate="%{y}")


            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

