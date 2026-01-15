





import pandas as pd
from pathlib import Path
from tqdm import tqdm
import plotly.express as px


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'General' / 'RHNA' / 'Final Products'
FILE_HCD = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA'  / 'New Data Collected' / 'HCD_annualprogressreport.xlsx'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()



if __name__ == '__main__':

    indicator = 'RHNA_HSG_11'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv']
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title']


    ## Right now, using the "5th Cycle Full Summary", but will need to update to 6th or 7th I'm guessing

    df_hcd = pd.read_excel(FILE_HCD, sheet_name='5th Cycle Full Summary', skiprows=1)

    df_hcd = df_hcd[['COUNTY', 'JURS NAME', 'ABOVE MOD PERMITS', 'MOD PERMITS', 'LI PERMITS', 'VLI PERMITS']]
    df_hcd = df_hcd[df_hcd['COUNTY'].isin(['EL DORADO', 'PLACER', 'SACRAMENTO', 'SUTTER', 'YOLO', 'YUBA'])]
    df_hcd = df_hcd.reset_index(drop=True)

    df_hcd['COUNTY'   ] = df_hcd['COUNTY'   ].str.title()
    df_hcd['JURS NAME'] = df_hcd['JURS NAME'].str.title()

    df_hcd.loc[df_hcd['JURS NAME'].str.contains('County'), 'JURS NAME'] = 'Unincorporated'



    counties = list(df_hcd['COUNTY'].unique())

    for county in counties:

        rhna.print2()
        print(county)

        path_county = PATH_OUT / county
        df_sub = df_hcd[df_hcd['COUNTY'] == county]
        jurisdictions = list(df_sub['JURS NAME'].unique())

        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_sub_juris = df_sub[df_sub['JURS NAME'] == jurisdiction]
            df_sub_juris = df_sub_juris.drop(['COUNTY', 'JURS NAME'], axis=1)

            ## Plotting ---

            df_prod = df_sub_juris.copy()
            df_prod = df_prod.T.reset_index()
            df_prod.columns = ['Income Group', 'Number of Permits']

            df_plot = df_prod.copy()

            fig = px.bar(df_plot, x='Income Group', y='Number of Permits')
            fig.update_traces(marker_color='#1E90FF')
            fig.update_traces(hovertemplate="%{y}")
        

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)

