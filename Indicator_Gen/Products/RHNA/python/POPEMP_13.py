


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
FILE_DOF = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Vibrant and Inclusive Places' / 'People and Community' / 'Pop and Demographics' / 'DOF_E5_and_E8_Jurisdictions.xlsx'


import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()



def re_remove_pre(x, exp = '('):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x




if __name__ == '__main__':

    indicator = 'RHNA_POPEMP_13'
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

    job_sectors = ['CNS01', 'CNS02', 'CNS03', 'CNS04', 'CNS05', 'CNS06', 'CNS07', 'CNS08', 'CNS09', 'CNS10', 'CNS11', 'CNS12', 'CNS13', 'CNS14', 'CNS15', 'CNS16', 'CNS17', 'CNS18', 'CNS19', 'CNS20']


    ## Organizing ---


    print(); print()
    print('Importing Workplace Area Characteristic (WAC) data by year from zip files stored online found here:  https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/')
    print()


    years = range(base_year, end_year+1, 1)


    list_df = []

    for year in tqdm(years):

        url = f'https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_{year}.csv.gz'
        data = rhna.import_gz_from_url(url)
        df = pd.read_csv(io.StringIO(data.decode('utf-8')))
        df['Year'] = year
        
        df['block_group'] = df['w_geocode'].astype('str')
        df['block_group'] = df['block_group'].str[0:11]
        df = df[df['block_group'].isin(df_map['Geographic_Code_Identifier'].unique())]
        df = df.merge(df_map, left_on='block_group', right_on='Geographic_Code_Identifier')
        df = df.drop(['w_geocode', 'createdate', 'block_group', 'Geographic_Code_Identifier'], axis=1)
        df = df.groupby(['Year', 'COUNTY', 'JURIS'], as_index=False).sum()
        df = df.melt(id_vars=['Year', 'COUNTY', 'JURIS'], var_name='job_sector_code', value_name='num_jobs')
        df = df.merge(df_lodes, on='job_sector_code', how='left')
        df = df[df['job_sector_code'].isin(job_sectors)]
        df = df.reset_index(drop=True)

        df = df.groupby(['Year', 'COUNTY', 'JURIS'], as_index=False)['num_jobs'].sum()

        df.loc[df['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

        list_df.append(df)
        time.sleep(1)

    df = pd.concat(list_df)
    df = df.reset_index(drop=True)


    ## Import DOF data by jurisdiction
    ## Merge number of occupied households onto jobs data
    ## Divide jobs data by number of occupied households
    ## Plot that ratio on a line chart comparing jurisdiction to county to region

    df_dof = pd.read_excel(FILE_DOF)
    df_dof = df_dof[df_dof['County'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba'])]
    df_dof['Jurisdiction'] = df_dof['Jurisdiction'].str.replace(' Town', '')
    df_dof = df_dof[['County', 'Jurisdiction', 'Year', 'Occupied']]
    df_dof = df_dof.rename(columns={'County':'COUNTY', 'Jurisdiction':'JURIS'})
    df_dof.loc[df_dof['JURIS'] == 'Yuba', 'JURIS'] = 'Yuba City'
    df_dof = df_dof.reset_index(drop=True)


    df = df.merge(df_dof, on=['COUNTY', 'JURIS', 'Year'], how='left')


    df_places   = df.copy()
    df_counties = df.groupby(['Year', 'COUNTY'], as_index=False).agg(num_jobs=('num_jobs', 'sum'), Occupied=('Occupied', 'sum'))
    df_mpo      = df.groupby(['Year',         ], as_index=False).agg(num_jobs=('num_jobs', 'sum'), Occupied=('Occupied', 'sum'))


    df_places  ['Ratio'] = df_places  ['num_jobs'] / df_places  ['Occupied']
    df_counties['Ratio'] = df_counties['num_jobs'] / df_counties['Occupied']
    df_mpo     ['Ratio'] = df_mpo     ['num_jobs'] / df_mpo     ['Occupied']

    df_places   = df_places  .rename(columns={'JURIS':'Geography'})
    df_counties = df_counties.rename(columns={'COUNTY':'Geography'})
    df_mpo['Geography'] = 'SACOG Region'

    df_places   = df_places  .drop(['num_jobs', 'Occupied'], axis=1)
    df_counties = df_counties.drop(['num_jobs', 'Occupied'], axis=1)
    df_mpo      = df_mpo     .drop(['num_jobs', 'Occupied'], axis=1)


    print()
    print('Data for all years: ')
    display(df_places.head())

    counties = df_counties['Geography'].unique()




    ## Plotting ---

    for county in counties:

        rhna.print2()
        print(county)
        time.sleep(1)

        df_places_sub   = df_places  [df_places  ['COUNTY'   ] == county]
        df_counties_sub = df_counties[df_counties['Geography'] == county]

        df_places_sub = df_places_sub.drop('COUNTY', axis=1)
        df_counties_sub['Geography'] = df_counties_sub['Geography'] + ' County'
        
        jurisdictions = df_places_sub['Geography'].unique()

        for jurisdiction in tqdm(jurisdictions):
            tqdm.write(jurisdiction)

            df_prod = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            # df_prod['Ratio'] = round(df_prod['Ratio'], 2)

            df_plot = df_prod.copy()
            df_prod = df_prod.pivot_table(index='Year', columns='Geography', values='Ratio').reset_index()
            df_prod = df_prod[['Year', jurisdiction, f'{county} County', 'SACOG Region']]

            color_map = {
                jurisdiction: '#9DC209'
                , f'{county} County': '#1E90FF'
                , 'SACOG Region': '#1F45FC'
            }

            fig = px.line(df_plot, x='Year', y='Ratio', color='Geography', color_discrete_map=color_map, markers=True)

            # fig.update_layout(legend={'traceorder': 'reversed'})
            fig.update_traces(hovertemplate="%{y}")

            rhna.plot_rhna(fig, county, jurisdiction, indicator, title)
            rhna.export_rhna(county, jurisdiction, indicator, title, df_prod)
