

from pathlib import Path
from tqdm import tqdm
import time
import warnings

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

warnings.filterwarnings("ignore")

if __name__ == '__main__':

    df_places, df_counties, df_mpo = rhna.acs_import(INDICATOR)
    race_ethcnitiy_map = {
    'American Indian or Alaska Native': 'American Indian or Alaska Native'
    , 'Asian': 'Asian'
    , 'Black or African American': 'Black or African American'
    , 'Hispanic or Latino': 'Hispanic or Latino'
    , 'Native Hawaiian or other Pacific Islander': 'Native Hawaiian or other Pacific Islander'
    , 'White (NH)': 'White (NH)'
    , 'Some other race': 'Other race or multiple races'
    , 'Two or more races': 'Other race or multiple races'
    }

    df_places   = df_places  [(df_places  ['Race/Ethnicity'] != 'All') & (df_places  ['Year'] == df_places  ['Year'].max())]
    df_counties = df_counties[(df_counties['Race/Ethnicity'] != 'All') & (df_counties['Year'] == df_counties['Year'].max())]
    df_mpo      = df_mpo     [(df_mpo     ['Race/Ethnicity'] != 'All') & (df_mpo     ['Year'] == df_mpo     ['Year'].max())]
            
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
    df_counties['NAME'] = df_counties['NAME'].str.replace(', California'     , '', regex=True)

    df_places   = df_places  .rename(columns={'NAME':'Geography', 'Variable':'Housing Tenure'})
    df_counties = df_counties.rename(columns={'NAME':'Geography', 'Variable':'Housing Tenure'})
    df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography', 'Variable':'Housing Tenure'})
    df_mpo = df_mpo.drop_duplicates()

    df_places  ['Race/Ethnicity'] = df_places  ['Race/Ethnicity'].replace(race_ethcnitiy_map)
    df_counties['Race/Ethnicity'] = df_counties['Race/Ethnicity'].replace(race_ethcnitiy_map)# trying to role up to new race/ethnicity mapping, it's new so may not run properly, double check
    df_mpo     ['Race/Ethnicity'] = df_mpo     ['Race/Ethnicity'].replace(race_ethcnitiy_map)

    df_places   = df_places  .groupby(['County Name', 'Geography', 'Race/Ethnicity', 'Housing Tenure'], as_index=False)['Households'].sum()
    df_counties = df_counties.groupby([               'Geography', 'Race/Ethnicity', 'Housing Tenure'], as_index=False)['Households'].sum()
    df_mpo      = df_mpo     .groupby([               'Geography', 'Race/Ethnicity', 'Housing Tenure'], as_index=False)['Households'].sum()

    df_places  ['Percent'] = df_places  ['Households'] / df_places  .groupby(['County Name', 'Geography', 'Race/Ethnicity'])['Households'].transform('sum')
    df_counties['Percent'] = df_counties['Households'] / df_counties.groupby([               'Geography', 'Race/Ethnicity'])['Households'].transform('sum')
    df_mpo     ['Percent'] = df_mpo     ['Households'] / df_mpo     .groupby([               'Geography', 'Race/Ethnicity'])['Households'].transform('sum')

    df_places   = df_places  [['County Name', 'Geography', 'Race/Ethnicity', 'Housing Tenure', 'Households', 'Percent']].reset_index(drop=True)
    df_counties = df_counties[[               'Geography', 'Race/Ethnicity', 'Housing Tenure', 'Households', 'Percent']].reset_index(drop=True)
    df_mpo      = df_mpo     [[               'Geography', 'Race/Ethnicity', 'Housing Tenure', 'Households', 'Percent']].reset_index(drop=True)


    counties = df_counties['Geography'].unique()

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_places_sub, df_counties_sub = rhna.acs_sub(df_places, df_counties, county)
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod, df_pct = rhna.acs_pivot(INDICATOR, df_places_sub, county, jurisdiction, 'Housing Tenure', 'Households', 'Race/Ethnicity')

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            dt_eth_map = {
                'American Indian or Alaska Native':'American Indian or<br>Alaska Native'
                , 'Asian':'Asian'
                , 'Black or African American':'Black or<br>African American'
                , 'Hispanic or Latino':'Hispanic or<br>Latino'
                , 'Native Hawaiian or other Pacific Islander':'Native Hawaiian or<br>other Pacific Islander'
                , 'Other race or multiple races':'Other race or<br>multiple races'
                , 'White (NH)': 'White (NH)'
            }
            df_plot['Race/Ethnicity'] = df_plot['Race/Ethnicity'].map(dt_eth_map)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

