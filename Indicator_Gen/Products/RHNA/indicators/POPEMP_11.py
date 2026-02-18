


def re_remove_pre(x, exp = '('):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x


import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import io
from IPython.display import display


import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


FILE_LODES = Path(r'I:\Projects\Josh\Regional Monitoring') / 'LEHD_LODESmappings.xlsx'
FILE_CW = Path(r'I:\Projects\Josh\Geospatial Data') / 'crosswalks' / 'Census_2020_BG_Jurisdiction.csv'

BASE_YEAR = 2002
END_YEAR = 2023


if __name__ == '__main__':

    # Mapping - Block Group to Census Designated Places mapping
    df_map = pd.read_csv(FILE_CW)
    df_map = df_map[['Geographic_Code_Identifier', 'JURIS', 'COUNTY']]
    df_map['Geographic_Code_Identifier'] = df_map['Geographic_Code_Identifier'].astype('str')

    # Mapping - WAC job sector code to description mapping
    df_lodes = pd.read_excel(FILE_LODES, sheet_name='WAC')
    df_lodes = df_lodes[['Variable', 'Explanation']].rename(columns={'Variable':'job_sector_code', 'Explanation':'Desc'})

    job_sectors = ['CNS01', 'CNS02', 'CNS03', 'CNS04', 'CNS05', 'CNS06', 'CNS07', 'CNS08', 'CNS09', 'CNS10', 'CNS11', 'CNS12', 'CNS13', 'CNS14', 'CNS15', 'CNS16', 'CNS17', 'CNS18', 'CNS19', 'CNS20']


    rhna.print2()
    print('Importing Workplace Area Characteristic (WAC) data by year from zip files stored online found here:  https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/')
    print()

    years = range(BASE_YEAR, END_YEAR+1, 1)
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
        df = df.melt(id_vars=['Year', 'COUNTY', 'JURIS'], var_name='job_sector_code', value_name='Number of Jobs')
        df = df.merge(df_lodes, on='job_sector_code', how='left')
        df = df[df['job_sector_code'].isin(job_sectors)].reset_index(drop=True)
    
        df['Desc_clean'] = df['Desc'].apply(re_remove_pre)
        df['Desc_clean'] = df['Desc_clean'].str[:-1]

        conditions = [
            df['Desc_clean'].isin(['Agriculture, Forestry, Fishing and Hunting', 'Mining, Quarrying, and Oil and Gas Extraction'])
            , df['Desc_clean'].isin(['Arts, Entertainment, and Recreation', 'Accommodation and Food Services', 'Other Services [except Public Administration]'])
            , df['Desc_clean'].isin(['Construction'])
            , df['Desc_clean'].isin(['Finance and Insurance', 'Real Estate and Rental and Leasing'])
            , df['Desc_clean'].isin(['Public Administration'])
            , df['Desc_clean'].isin(['Educational Services', 'Health Care and Social Assistance'])
            , df['Desc_clean'].isin(['Information'])
            , df['Desc_clean'].isin(['Manufacturing', 'Wholesale Trade'])
            , df['Desc_clean'].isin(['Professional, Scientific, and Technical Services', 'Management of Companies and Enterprises', 'Administrative and Support and Waste Management and Remediation Services'])
            , df['Desc_clean'].isin(['Retail Trade'])
            , df['Desc_clean'].isin(['Utilities', 'Transportation and Warehousing'])
        ]
        choices = ['Agriculture & Natural Resources', 'Arts, Recreation, & Other', 'Construction', 'Financial & Leasing', 'Government', 'Health & Educational Services', 'Information', 'Manufacturing & Wholesale', 'Professional & Managerial Services', 'Retail', 'Transportation & Utilities']
        df['Industry'] = np.select(conditions, choices, default='No')
        df = df.groupby(['Year', 'COUNTY', 'JURIS', 'Industry'], as_index=False)['Number of Jobs'].sum()
        df.loc[df['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

        list_df.append(df)

    df = pd.concat(list_df).reset_index(drop=True)

    print()
    print('Data for all years: ')
    display(df.head())

    counties = df['COUNTY'].unique()


    for county in counties:

        rhna.print2()
        print(county)
        time.sleep(1)

        df_sub = df[df['COUNTY'] == county]
        jurisdictions = df_sub['JURIS'].unique()

        for jurisdiction in tqdm(jurisdictions):
            tqdm.write(jurisdiction)

            df_prod = df_sub[df_sub['JURIS'] == jurisdiction].drop('COUNTY', axis=1).pivot_table(index='Year', columns='Industry', values='Number of Jobs').reset_index()
            df_plot = df_sub[df_sub['JURIS'] == jurisdiction]

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)