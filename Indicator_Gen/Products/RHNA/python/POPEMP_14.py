





import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import io
import plotly.express as px
from IPython.display import display


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

FILE_LODES = Path(r'I:\Projects\Josh\Regional Monitoring') / 'LEHD_LODESmappings.xlsx'
FILE_CW = Path(r'I:\Projects\Josh\Geospatial Data') / 'crosswalks' / 'Census_2020_BG_Jurisdiction.csv'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()



def re_remove_pre(x, exp = '('):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x



if __name__ == '__main__':

    indicator = 'RHNA_POPEMP_14'
    source = FILE_YAML[indicator.replace('RHNA_', '')]['Abbrv'][0]
    title  = FILE_YAML[indicator.replace('RHNA_', '')]['Title'][0]
    base_year = 2002
    end_year = 2022


    ## Mappings

    # Block Group to Census Designated Places mapping
    df_map = pd.read_csv(FILE_CW)
    df_map = df_map[['Geographic_Code_Identifier', 'JURIS', 'COUNTY']]
    df_map['Geographic_Code_Identifier'] = df_map['Geographic_Code_Identifier'].astype('str')


    # WAC job sector code to description mapping
    df_lodes = pd.read_excel(FILE_LODES, sheet_name='WAC')
    df_lodes = df_lodes[['Variable', 'Explanation']].rename(columns={'Variable':'job_sector_code', 'Explanation':'Desc'})

    job_sectors = ['CE01', 'CE02', 'CE03']


    years = range(base_year, end_year+1, 1)


    ## Organizing

    rhna.print2()
    print('Importing Workplace Area Characteristic (WAC) data by year from zip files stored online found here:  https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/')
    print()

    list_df_wac = []

    for year in tqdm(years):

        url = f'https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_{year}.csv.gz'
        data = rhna.import_gz_from_url(url)
        df_wac = pd.read_csv(io.StringIO(data.decode('utf-8')))
        df_wac['Year'] = year
        
        df_wac['block_group'] = df_wac['w_geocode'].astype('str')
        df_wac['block_group'] = df_wac['block_group'].str[0:11]
        df_wac = df_wac[df_wac['block_group'].isin(df_map['Geographic_Code_Identifier'].unique())]
        df_wac = df_wac.merge(df_map, left_on='block_group', right_on='Geographic_Code_Identifier')
        df_wac = df_wac.drop(['w_geocode', 'createdate', 'block_group', 'Geographic_Code_Identifier'], axis=1)
        df_wac = df_wac.groupby(['Year', 'COUNTY', 'JURIS'], as_index=False).sum()
        df_wac = df_wac.melt(id_vars=['Year', 'COUNTY', 'JURIS'], var_name='job_sector_code', value_name='num_jobs_wac')
        df_wac = df_wac.merge(df_lodes, on='job_sector_code', how='left')
        df_wac = df_wac[df_wac['job_sector_code'].isin(job_sectors)]
        df_wac = df_wac.reset_index(drop=True)

        breakpoint()

        conditions = [
            df_wac['Desc'].isin(['Number of jobs with earnings $1250/month or less'])
            , df_wac['Desc'].isin(['Number of jobs with earnings $1251/month to $3333/month'])
            , df_wac['Desc'].isin(['Number of jobs with earnings greater than $3333/month'])
        ]

        choices = ['Earnings &#36;1250/month or less', 'Earnings &#36;1251/month to &#36;3333/month', 'Earnings greater than &#36;3333/month']

        df_wac['Desc_final'] = np.select(conditions, choices, default='No')

        df_wac = df_wac.groupby(['Year', 'COUNTY', 'JURIS', 'Desc_final'], as_index=False)['num_jobs_wac'].sum()

        df_wac.loc[df_wac['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

        list_df_wac.append(df_wac)
        time.sleep(1)

    df_wac = pd.concat(list_df_wac)
    df_wac = df_wac.reset_index(drop=True)


    rhna.print2()
    print('Importing Residential Area Characteristic (RAC) data by year from zip files stored online found here:  https://lehd.ces.census.gov/data/lodes/LODES8/ca/rac/')
    print()

    list_df_rac = []

    for year in tqdm(years):

        url = f'https://lehd.ces.census.gov/data/lodes/LODES8/ca/rac/ca_rac_S000_JT00_{year}.csv.gz'
        data = rhna.import_gz_from_url(url)
        df_rac = pd.read_csv(io.StringIO(data.decode('utf-8')))
        df_rac['Year'] = year
        
        df_rac['block_group'] = df_rac['h_geocode'].astype('str')
        df_rac['block_group'] = df_rac['block_group'].str[0:11]
        df_rac = df_rac[df_rac['block_group'].isin(df_map['Geographic_Code_Identifier'].unique())]
        df_rac = df_rac.merge(df_map, left_on='block_group', right_on='Geographic_Code_Identifier')
        df_rac = df_rac.drop(['h_geocode', 'createdate', 'block_group', 'Geographic_Code_Identifier'], axis=1)
        df_rac = df_rac.groupby(['Year', 'COUNTY', 'JURIS'], as_index=False).sum()
        df_rac = df_rac.melt(id_vars=['Year', 'COUNTY', 'JURIS'], var_name='job_sector_code', value_name='num_jobs_rac')
        df_rac = df_rac.merge(df_lodes, on='job_sector_code', how='left')
        df_rac = df_rac[df_rac['job_sector_code'].isin(job_sectors)]
        df_rac = df_rac.reset_index(drop=True)

        conditions = [
            df_rac['Desc'].isin(['Number of jobs with earnings $1250/month or less'])
            , df_rac['Desc'].isin(['Number of jobs with earnings $1251/month to $3333/month'])
            , df_rac['Desc'].isin(['Number of jobs with earnings greater than $3333/month'])
        ]

        choices = ['Earnings &#36;1250/month or less', 'Earnings &#36;1251/month to &#36;3333/month', 'Earnings greater than &#36;3333/month']

        df_rac['Desc_final'] = np.select(conditions, choices, default='No')

        df_rac = df_rac.groupby(['Year', 'COUNTY', 'JURIS', 'Desc_final'], as_index=False)['num_jobs_rac'].sum()

        df_rac.loc[df_rac['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

        list_df_rac.append(df_rac)
        time.sleep(1)

    df_rac = pd.concat(list_df_rac)
    df_rac = df_rac.reset_index(drop=True)

    df = df_wac.merge(df_rac, on=['Year', 'COUNTY', 'JURIS', 'Desc_final'], how='left')
    df['Ratio'] = df['num_jobs_wac'] / df['num_jobs_rac']



    df = df.drop(['num_jobs_wac', 'num_jobs_rac'], axis=1)


    print()
    print('Data for all years: ')
    display(df)

    counties = df['COUNTY'].unique()



    ## Plotting

    for county in counties:

        rhna.print2()
        print(county)
        time.sleep(1)

        df_sub = df[df['COUNTY'] == county]
        jurisdictions = df_sub['JURIS'].unique()

        for jurisdiction in tqdm(jurisdictions):
            tqdm.write(jurisdiction)

            df_prod = df_sub.copy()
            df_prod = df_prod[df_prod['JURIS'] == jurisdiction]
            df_prod = df_prod.drop('COUNTY', axis=1)
            df_prod = df_prod.pivot_table(index='Year', columns='Desc_final', values='Ratio').reset_index()
            df_prod.columns = ['Year', 'Earnings $1250/month or less', 'Earnings $1251/month to $3333/month', 'Earnings greater than $3333/month']

            df_plot = df_sub.copy()
            df_plot = df_plot[df_plot['JURIS'] == jurisdiction]


            color_map = {
                'Earnings &#36;1250/month or less': '#1F45FC'
                , 'Earnings &#36;1251/month to &#36;3333/month': '#1E90FF'
                , 'Earnings greater than &#36;3333/month': '#9DC209'
            }

            fig = px.line(df_plot, x='Year', y='Ratio'
                            , color = 'Desc_final'
                            , color_discrete_map=color_map)

            fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)



