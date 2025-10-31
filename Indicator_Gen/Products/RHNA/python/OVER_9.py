






import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import plotly.express as px


FILE_CHAS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / f'HUD_CHAS_2017thru2021.csv'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()




if __name__ == '__main__':

    indicator = 'RHNA_OVER_9'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    values = 'Households'
    columns = 'Cost Burden'



    ## Organizing

    df_chas = pd.read_csv(FILE_CHAS, dtype=str)
    df_chas['Households'] = df_chas['Households'].astype(int)

    estimates = [
        'T7_est5', 'T7_est6', 'T7_est7', 'T7_est9', 'T7_est10', 'T7_est11', 'T7_est13', 'T7_est14', 'T7_est15', 'T7_est17',
        'T7_est18', 'T7_est19', 'T7_est21', 'T7_est22', 'T7_est23', 'T7_est26', 'T7_est27', 'T7_est28', 'T7_est30', 'T7_est31',
        'T7_est32', 'T7_est34', 'T7_est35', 'T7_est36', 'T7_est38', 'T7_est39', 'T7_est40', 'T7_est42', 'T7_est43', 'T7_est44',
        'T7_est47', 'T7_est48', 'T7_est49', 'T7_est51', 'T7_est52', 'T7_est53', 'T7_est55', 'T7_est56', 'T7_est57', 'T7_est59',
        'T7_est60', 'T7_est61', 'T7_est63', 'T7_est64', 'T7_est65', 'T7_est68', 'T7_est69', 'T7_est70', 'T7_est72', 'T7_est73',
        'T7_est74', 'T7_est76', 'T7_est77', 'T7_est78', 'T7_est80', 'T7_est81', 'T7_est82', 'T7_est84', 'T7_est85', 'T7_est86',
        'T7_est89', 'T7_est90', 'T7_est91', 'T7_est93', 'T7_est94', 'T7_est95', 'T7_est97', 'T7_est98', 'T7_est99', 'T7_est101',
        'T7_est102', 'T7_est103', 'T7_est105', 'T7_est106', 'T7_est107', 'T7_est111', 'T7_est112', 'T7_est113', 'T7_est115', 'T7_est116',
        'T7_est117', 'T7_est119', 'T7_est120', 'T7_est121', 'T7_est123', 'T7_est124', 'T7_est125', 'T7_est127', 'T7_est128', 'T7_est129',
        'T7_est132', 'T7_est133', 'T7_est134', 'T7_est136', 'T7_est137', 'T7_est138', 'T7_est140', 'T7_est141', 'T7_est142', 'T7_est144',
        'T7_est145', 'T7_est146', 'T7_est148', 'T7_est149', 'T7_est150', 'T7_est153', 'T7_est154', 'T7_est155', 'T7_est157', 'T7_est158',
        'T7_est159', 'T7_est161', 'T7_est162', 'T7_est163', 'T7_est165', 'T7_est166', 'T7_est167', 'T7_est169', 'T7_est170', 'T7_est171',
        'T7_est174', 'T7_est175', 'T7_est176', 'T7_est178', 'T7_est179', 'T7_est180', 'T7_est182', 'T7_est183', 'T7_est184', 'T7_est186',
        'T7_est187', 'T7_est188', 'T7_est190', 'T7_est191', 'T7_est192', 'T7_est195', 'T7_est196', 'T7_est197', 'T7_est199', 'T7_est200',
        'T7_est201', 'T7_est203', 'T7_est204', 'T7_est205', 'T7_est207', 'T7_est208', 'T7_est209', 'T7_est211', 'T7_est212', 'T7_est213'
    ]

    df_chas = df_chas[df_chas['Estimate'].isin(estimates)]
    print(df_chas['Description 1'].unique())
    print(df_chas['Description 2'].unique())
    print(df_chas['Description 3'].unique())
    print(df_chas['Description 4'].unique())


    df_chas = df_chas[['County Name', 'name', 'Description 3', 'Description 4', 'Households']]
    df_chas = df_chas.rename(columns = {'Description 3':'Household Size', 'Description 4':'Cost Burden'})
    df_chas['name'] = df_chas['name'].str.replace(' city, California', '', regex=True)
    df_chas['name'] = df_chas['name'].str.replace(' town, California', '', regex=True)

    conditions = [
        df_chas['Cost Burden'] == 'housing cost burden is less than or equal to 30%'
        , df_chas['Cost Burden'] == 'housing cost burden is greater than 30% but less than or equal to 50%'
        , df_chas['Cost Burden'] == 'housing cost burden is greater than 50%'
        , df_chas['Cost Burden'] == 'housing cost burden not computed (no/negative income)'
    ]

    choices = ['0%-30% of income used for housing', '30%-50% of income used for housing', '50%+ of income used for housing', 'Not computed']

    df_chas['Cost Burden'] = np.select(conditions, choices, default='no')


    conditions = [
        df_chas['Household Size'] == 'household type is elderly family (2 persons, with either or both age 62 or over)'
        , df_chas['Household Size'] == 'household type is small family (2 persons, neither person 62 years or over, or 3 or 4 persons)'
        , df_chas['Household Size'] == 'household type is large family (5 or more persons)'
        , df_chas['Household Size'] == 'household type is elderly non-family'
        , df_chas['Household Size'] == 'other household type (non-elderly non-family)'
    ]

    choices = ['All other household types', 'All other household types', 'Large family with 5+ persons', 'All other household types', 'All other household types']

    df_chas['Household Size'] = np.select(conditions, choices, default='no')


    df_chas = df_chas.groupby(['County Name', 'name', 'Household Size', 'Cost Burden'], as_index=False)['Households'].sum()

    df_chas['Percentage'] = df_chas['Households'] / df_chas.groupby(['County Name', 'name', 'Household Size'])['Households'].transform('sum')
    # df_chas = df_chas[df_chas['Cost Burden'] != 'Not computed']


    df_chas = df_chas.reset_index(drop=True)


    counties = list(df_chas['County Name'].unique())

    for county in counties:
        
        print();print()
        print(county)
        time.sleep(2)

        df_chas_sub = df_chas[df_chas['County Name'] == county]
        jurisdictions = df_chas_sub['name'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_prod = df_prod.drop('Percentage', axis=1)
            df_prod = df_prod.pivot_table(index=['Household Size'], columns=columns, values=values).reset_index()

            df_pct = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_pct = df_pct.drop('Households', axis=1)
            df_pct = df_pct.pivot_table(index=['Household Size'], columns=columns, values='Percentage').reset_index()
            
            ## Plotting ---

            df_plot = df_chas_sub[df_chas_sub['name'] == jurisdiction]
            df_plot['Percentage'] = round(df_plot['Percentage']*100, 1)
            
            color_map  = {
                'Not computed': '#9B9A96'
                , '0%-30% of income used for housing': '#1F45FC'
                , '30%-50% of income used for housing': '#1E90FF'
                , '50%+ of income used for housing': '#9DC209'
            }

            fig = px.bar(df_plot, x='Household Size', y='Percentage'
                        , color = columns
                        # , barmode='group'
                        , color_discrete_map=color_map)
            
            fig.update_traces(hovertemplate="%{y}")
            fig.update_yaxes(ticksuffix='%')
            fig.update_layout(legend={'traceorder': 'reversed'})


            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod, df_pct)

