

import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
import numpy as np
from IPython.display import display

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


PATH_GEO = Path(r'I:\Projects\Josh\Geospatial Data')
FILE_TRACTS = PATH_GEO / 'GISOWNER' / 'T2020_Census_Tracts_SACOG_Region' / 'T2020_Census_Tracts_SACOG_Region.shp'
FILE_JURISDICTIONS = PATH_GEO / 'GISOWNER' / 'CityCounty' / 'CityCounty.shp'

PATH_RHNA_GEO = Path(r'I:\Projects\Josh\RHNA\Geospatial Data')
FILE_IN = PATH_RHNA_GEO / 'draft-2024-opportunity-maps-shapefile' / 'final_opp_2024_public.gpkg'

GDB = Path(r'I:\Projects\Josh\RHNA\ArcPro\RHNA.gdb')
FC_BLOCKS = 'GISOWNER_Census_Blocks_SACOG_Region' # Left join this guy onto the census tracts file, 


## TODO: Scale back AFFH_2 data
def scale_tracts_by_blocks(gdf_ct, gdf_blocks, gdf_cdp):

    # STEP 1 — PREP BLOCK POPULATION
    print("Preparing block population...")
    gdf_blocks = gdf_blocks.rename(columns={'GEOID': 'BLOCK_GEOID', 'POP100': 'POP'})
    gdf_blocks = gdf_blocks[['BLOCK_GEOID', 'POP', 'geometry']].copy()
    gdf_blocks['POP'] = gdf_blocks['POP'].fillna(0)
    if gdf_blocks.crs.is_geographic: gdf_blocks = gdf_blocks.to_crs(gdf_ct.crs)

    # STEP 2 — BLOCK → TRACT JOIN
    print("Assigning blocks to tracts...")
    gdf_blocks_tract = gpd.sjoin(gdf_blocks, gdf_ct[['GEOCODE','geometry']], how='left', predicate='within')

    # STEP 3 — BLOCK → JURISDICTION OVERLAY
    print("Overlaying blocks with jurisdictions...")
    gdf_block_juris = gpd.overlay(gdf_blocks_tract, gdf_cdp[['JURIS','geometry']], how='intersection')
    gdf_block_juris['piece_area'] = gdf_block_juris.geometry.area
    block_area = gdf_blocks[['BLOCK_GEOID','geometry']].copy()
    block_area['block_area'] = block_area.geometry.area
    gdf_block_juris = gdf_block_juris.merge(block_area[['BLOCK_GEOID','block_area']], on='BLOCK_GEOID')
    gdf_block_juris['pop_piece'] = round(gdf_block_juris['POP'] * (gdf_block_juris['piece_area'] / gdf_block_juris['block_area']))

    # STEP 4 — TRACT × JURIS POP SCALAR
    print("Computing tract-jurisdiction scalars...")
    tract_juris_pop = (gdf_block_juris.groupby(['GEOCODE', 'JURIS'])['pop_piece'].sum().reset_index())
    tract_tot_pop = (gdf_block_juris.groupby('GEOCODE')['pop_piece'].sum().reset_index().rename(columns={'pop_piece':'tract_pop'}))
    tract_juris_pop = tract_juris_pop.merge(tract_tot_pop, on='GEOCODE')
    tract_juris_pop['pop_scalar'] = tract_juris_pop['pop_piece'] / tract_juris_pop['tract_pop']
    tract_juris_pop['pop_scalar'] = tract_juris_pop['pop_scalar'].fillna(1)
    tract_juris_pop['fips'] = tract_juris_pop['GEOCODE'].str[1:].astype('int64')

    return tract_juris_pop




if __name__ == '__main__':


    if __name__ == '__main__':

        gdf_tcac = gpd.read_file(FILE_IN)
        gdf_tcac = gdf_tcac[gdf_tcac['county_name'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yuba', 'Yolo'])].reset_index(drop=True)
        df_tcac = gdf_tcac[['county_name', 'fips', 'oppcat']]
        display(df_tcac.head())

        df_acs = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR} Tracts ACS5.xlsx')
        df_acs['state' ] = df_acs['State FIPS' ].astype(str).apply('{:0>2}'.format)
        df_acs['county'] = df_acs['County FIPS'].astype(str).apply('{:0>3}'.format)
        df_acs['tract' ] = df_acs['Tract ID'   ].astype(str).apply('{:0>6}'.format)
        df_acs['fips'  ] = df_acs['state'] + df_acs['county'] + df_acs['tract']
        df_acs = df_acs[df_acs['Race_Ethnicity'] != 'All'].rename(columns={'Race_Ethnicity':'Race/Ethnicity'})

        df_acs = df_acs[['fips', 'Race/Ethnicity', 'Population']]
        display(df_acs.head())


        df_tcac = df_tcac.merge(df_acs, on='fips', how='left')

        ## Read in blocks data
        ## Read in opportunity map tract data
        ## Read in ACS population tract data
        ## Read in crosswalk from tracts to jurisdictions

        gdf_blocks = gpd.read_file(GDB, layer=FC_BLOCKS)
        gdf_ct  = gpd.read_file(FILE_TRACTS).to_crs("EPSG:2226")
        gdf_cdp = gpd.read_file(FILE_JURISDICTIONS).to_crs("EPSG:2226")
        gdf_ct_scaled = scale_tracts_by_blocks(gdf_ct, gdf_blocks, gdf_cdp)

        gdf_int = gpd.overlay(gdf_ct, gdf_cdp, how='intersection')
        gdf_int = gdf_int[
            ((gdf_int['COUNTY_2'] ==  'El Dorado') & (gdf_int['COUNTY_1'] ==  17.0)) |
            ((gdf_int['COUNTY_2'] ==     'Placer') & (gdf_int['COUNTY_1'] ==  61.0)) |
            ((gdf_int['COUNTY_2'] == 'Sacramento') & (gdf_int['COUNTY_1'] ==  67.0)) |
            ((gdf_int['COUNTY_2'] ==     'Sutter') & (gdf_int['COUNTY_1'] == 101.0)) |
            ((gdf_int['COUNTY_2'] ==       'Yolo') & (gdf_int['COUNTY_1'] == 113.0)) |
            ((gdf_int['COUNTY_2'] ==       'Yuba') & (gdf_int['COUNTY_1'] == 115.0))
            ]

        gdf_int['COUNTY_1'] = gdf_int['COUNTY_1'].astype(str).str[:-2].apply('{:0>3}'.format)
        gdf_int['TRACT'   ] = gdf_int['TRACT'   ].astype(str).str[:-2].apply('{:0>6}'.format)
        gdf_int['fips'] = '06' + gdf_int['COUNTY_1'] + gdf_int['TRACT']
        gdf_int = gdf_int[['fips', 'JURIS']]
        gdf_int = gdf_int.reset_index(drop=True)

        gdf_int['fips'] = gdf_int['fips'].str[1:].astype('int64')
        df_tcac['fips'] = df_tcac['fips'].str[1:].astype('int64')

        df_tcac = df_tcac.merge(gdf_int, on='fips', how='left')
        df_tcac = df_tcac.merge(gdf_ct_scaled[['fips', 'JURIS', 'pop_scalar']], on=['fips', 'JURIS'], how='left')
        df_tcac['Population'] = df_tcac['Population'] * df_tcac['pop_scalar']

        df_tcac.loc[df_tcac['JURIS' ].str.contains('County'), 'JURIS' ] = 'Unincorporated'
        df_tcac.loc[df_tcac['oppcat'].isna(), 'oppcat'] = 'Unknown'
        df_tcac.loc[df_tcac['oppcat'].str.contains('High'  ), 'oppcat'] = 'High/Highest Resource'

        df_tcac = df_tcac.groupby(['county_name', 'JURIS', 'Race/Ethnicity', 'oppcat'], as_index=False).agg(Population=('Population', 'sum'))

        df_tcac = df_tcac.pivot_table(index=['county_name', 'JURIS', 'Race/Ethnicity'], columns='oppcat', values='Population').reset_index()
        df_tcac = df_tcac.melt(id_vars=['county_name', 'JURIS', 'Race/Ethnicity'], var_name='oppcat', value_name='Population')

        df_tcac['Percent'] = df_tcac['Population'] / df_tcac.groupby(['county_name', 'JURIS', 'oppcat'])['Population'].transform('sum')
        df_tcac['sort'] = pd.Categorical(df_tcac['oppcat'], [
            'Low Resource'
            , 'Moderate Resource'
            , 'High/Highest Resource'
            , 'Unknown'
        ])
        df_tcac = df_tcac.sort_values(['county_name', 'JURIS', 'Race/Ethnicity', 'sort'], ascending=[True, True, False, True]).drop('sort', axis=1).reset_index(drop=True)
        df_tcac = df_tcac.fillna(0)

        counties = list(df_tcac['county_name'].unique())

        for county in counties:

            print('\n'*2)
            print(county)

            df_sub = df_tcac[df_tcac['county_name'] == county]
            jurisdictions = list(df_sub['JURIS'].unique())

            for jurisdiction in tqdm(jurisdictions, position=0):

                tqdm.write(jurisdiction)

                df_sub_juris = df_sub[df_sub['JURIS'] == jurisdiction]

                df_plot = df_sub_juris.copy().rename(columns={'oppcat':'Opportunity Category'})
                df_prod = df_sub_juris[['Race/Ethnicity', 'oppcat', 'Population']].pivot_table(index='Race/Ethnicity', columns='oppcat', values='Population').reset_index()
                df_pct  = df_sub_juris[['Race/Ethnicity', 'oppcat', 'Percent'   ]].pivot_table(index='Race/Ethnicity', columns='oppcat', values='Percent'   ).reset_index()
                
                df_prod = df_prod.replace(0, np.nan)
                df_pct  = df_pct .replace(0, np.nan)

                df_prod = df_prod[['Race/Ethnicity', 'Low Resource', 'Moderate Resource', 'High/Highest Resource', 'Unknown']]
                df_pct  = df_pct [['Race/Ethnicity', 'Low Resource', 'Moderate Resource', 'High/Highest Resource', 'Unknown']]

                df_plot['Percent of Population'] = round(df_plot['Percent']*100, 1)
                df_sort = pd.DataFrame({'Opportunity Category': ['Low Resource', 'Moderate Resource', 'High/Highest Resource', 'Unknown'], 'Sort': [1, 2, 3, 4]})
                df_plot = df_plot.merge(df_sort, on='Opportunity Category', how='left')
                df_plot = df_plot.sort_values(['Sort', 'Percent of Population'], ascending=[True, False])

                fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
                rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
                rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


