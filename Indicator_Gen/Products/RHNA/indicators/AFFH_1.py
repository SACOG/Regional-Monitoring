

import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
from IPython.display import display


import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
PATH_GEO = Path(r'I:\Projects\Josh\Geospatial Data')
FILE_TRACTS = PATH_GEO / 'GISOWNER' / 'T2020_Census_Tracts_SACOG_Region' / 'T2020_Census_Tracts_SACOG_Region.shp'
FILE_JURISDICTIONS = PATH_GEO / 'GISOWNER' / 'CityCounty' / 'CityCounty.shp'


if __name__ == '__main__':


    years    = ['2023']
    counties = ['06101','06115','06113','06061','06017','06067']

    dtypes = {
        'loan_to_value_ratio'           : str
        , 'interest_rate'               : str
        , 'rate_spread'                 : str
        , 'total_loan_costs'            : str
        , 'total_points_and_fees'       : str
        , 'origination_charges'         : str
        , 'discount_points'             : str
        , 'lender_credits'              : str
        , 'loan_term'                   : str
        , 'prepayment_penalty_term'     : str
        , 'intro_rate_period'           : str
        , 'property_value'              : str
        , 'total_units'                 : str
        , 'multifamily_affordable_units': str
        , 'census_tract'                : str
    }

    action_map = {
        1:'Loan originated'
        , 2:'Application approved but not accepted'
        , 3:'Application denied'
        , 4:'Application withdrawn by applicant'
        , 5:'File closed for incompleteness'
        , 6:'Purchased loan'
        , 7:'Preapproval request denied'
        , 8:'Preapproval request approved but not accepted'
    }


    df = rhna.hmda_import(years, counties, dtypes)

    df = df[['county_code', 'census_tract', 'derived_ethnicity', 'derived_race', 'action_taken']]
    df['Mortgage Application Status'] = df['action_taken'].replace(action_map)

    df = df[~df['derived_ethnicity'].isin(['Joint', 'Free Form Text Only'])]
    df = df[~df['derived_race'     ].isin(['Joint', 'Free Form Text Only'])]

    df['Race/Ethnicity'] = df['derived_race'].copy()
    df.loc[df['derived_ethnicity'] == 'Hispanic or Latino', 'Race/Ethnicity'] = 'Hispanic or Latino'
    df.loc[df['derived_ethnicity'] == 'Not Hispanic or Latino', 'Race/Ethnicity'] = df[df['derived_ethnicity'] == 'Not Hispanic or Latino']['Race/Ethnicity'] + ' (NH)'
    df.loc[(df['derived_ethnicity'] == 'Ethnicity Not Available') & (df['derived_race'] != 'Race Not Available'), 'Race/Ethnicity'] = df[(df['derived_ethnicity'] == 'Ethnicity Not Available') & (df['derived_race'] != 'Race Not Available')]['Race/Ethnicity'] + ' (NH)'
    df.loc[df['Race/Ethnicity'] == 'Race Not Available', 'Race/Ethnicity'] = 'Unknown'
    df.loc[df['Race/Ethnicity'] == 'Race Not Available (NH)', 'Race/Ethnicity'] = 'Unknown'

    df = df.groupby(['county_code', 'census_tract', 'Race/Ethnicity', 'Mortgage Application Status'], as_index=False).count()


    # Read in census tracts shp
    # Read in citycounty shp
    # Intersect
    # create crosswalk of tracts to jurisdictions
    # merge jurisdictions onto mortgage lending data using census tracts

    gdf_ct = gpd.read_file(FILE_TRACTS)
    gdf_cdp = gpd.read_file(FILE_JURISDICTIONS)
    
    gdf_ct = gdf_ct.to_crs("EPSG:2226")
    gdf_cdp = gdf_cdp.to_crs("EPSG:2226")

    gdf_int = gpd.overlay(gdf_ct, gdf_cdp, how='intersection')
    gdf_int['COUNTY_1'] = gdf_int['COUNTY_1'].astype(str).str[:-2].apply('{:0>3}'.format)
    gdf_int['TRACT'   ] = gdf_int['TRACT'   ].astype(str).str[:-2].apply('{:0>6}'.format)
    gdf_int['census_tract'] = '06' + gdf_int['COUNTY_1'] + gdf_int['TRACT']
    gdf_int = gdf_int[['census_tract', 'COUNTY_2', 'JURIS']].reset_index(drop=True)

    gdf_int['census_tract'] = gdf_int['census_tract'].str[1:].astype('int64')
    df['census_tract'] = df['census_tract'].str[1:].astype('int64')

    df = df.merge(gdf_int, on='census_tract', how='left')
    df = df[['COUNTY_2', 'JURIS', 'Race/Ethnicity', 'Mortgage Application Status']]

    df = df.groupby(['COUNTY_2', 'JURIS', 'Race/Ethnicity', 'Mortgage Application Status'], as_index=False).size()
    df['Percent'] = df['size'] / df.groupby(['COUNTY_2', 'JURIS', 'Race/Ethnicity'], as_index=False)['size'].transform('sum')
    df.loc[df['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

    display(df.head())


    counties = list(df['COUNTY_2'].unique())

    for county in counties:

        rhna.print2()
        print(county)

        path_county = PATH_OUT / county
        df_sub = df[df['COUNTY_2'] == county]
        jurisdictions = list(df_sub['JURIS'].unique())

        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)
            df_sub_juris = df_sub[df_sub['JURIS'] == jurisdiction]

            df_plot = df_sub_juris.copy()

            df_prod = df_sub_juris[['Race/Ethnicity', 'Mortgage Application Status', 'size'   ]].pivot_table(index='Race/Ethnicity', columns='Mortgage Application Status', values='size'   ).reset_index()
            df_pct  = df_sub_juris[['Race/Ethnicity', 'Mortgage Application Status', 'Percent']].pivot_table(index='Race/Ethnicity', columns='Mortgage Application Status', values='Percent').reset_index()

            df_plot['Percent of Population'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


