'''

Data Download
Note: As of 2020, the Census API has been somewhat unreliable. We encourage
everyone to save all their downloads so you don't run into delays while
working on your project. Don't rely on the API to download everyday.


'''



# Workspace --------------------------------------------------------------------------------------------------------------------------------------



print(); print(); print()


import census
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Proj
import matplotlib.pyplot as plt
from IPython.display import display

pd.options.display.float_format = '{:.2f}'.format # avoid scientific notation

home = str(Path.home())
input_path = home+'/git/displacement-typologies/data/inputs/'
output_path = home+'/git/displacement-typologies/data/outputs/'


path_git = Path(__file__).parent.parent.parent.parent
path_code    = path_git / 'Data' / 'Census'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'



# Read API key from ignored txt file
file_api = path_config / 'api_key.txt'
with open(file_api, 'r') as file:
    api_key = file.read()
    c = census.Census(api_key)






# Main ----------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':




    # Choose City and Census Tracts of Interest --------------------------------------------------------------------------

    # To get city data, run the following code in the terminal # TODO: Wondering if there is a better way
    # `python data.py <city name>`
    # Example: python data.py Atlanta

    city_name = 'Sacramento'
    # city_name = 'Atlanta'
    #If reproducing for another city, add elif for
    #that city & desired counties after last line

    if city_name == 'Sacramento':
        state = '06'
        counties = ['017', '061', '067', '101', '113', '115']
    else:
        print ('There is not information for the selected city')

    sql_query='state:{} county:*'.format(state)

    

    # Download ACS 2018 5-Year Estimates --------------------------------------------------------------------------

    df_vars_23=['B03002_001E',
                'B03002_003E',
                'B19001_001E',
                'B19013_001E',
                'B25077_001E',
                'B25077_001M',
                'B25064_001E',
                'B25064_001M',
                'B15003_001E',
                'B15003_022E',
                'B15003_023E',
                'B15003_024E',
                'B15003_025E',
                'B25034_001E',
                'B25034_010E',
                'B25034_011E',
                'B25003_002E',
                'B25003_003E',
                'B25105_001E',
                'B06011_001E']

    # Income categories - see notes
    var_str = 'B19001'
    var_list = []
    for i in range (1, 18):
        var_list.append(var_str+'_'+str(i).zfill(3)+'E')
    df_vars_23 = df_vars_23 + var_list

    # Migration - see notes
    var_str = 'B07010'
    var_list = []
    for i in list(range(25,34))+list(range(36, 45))+list(range(47, 56))+list(range(58, 67)):
        var_list.append(var_str+'_'+str(i).zfill(3)+'E')
    df_vars_23 = df_vars_23 + var_list


    # Run API query
    print('Fetching ACS 5-year estimates for 2023...');print(); print()
    var_dict_acs5 = c.acs5.get(df_vars_23, geo = {'for': 'tract:*', 'in': sql_query}, year=2023)


    # Converts variables into dataframe and filters only counties of interest
    df_vars_23 = pd.DataFrame.from_dict(var_dict_acs5)
    df_vars_23['counties']=df_vars_23['state']+df_vars_23['county']+df_vars_23['tract']
    df_vars_23 = df_vars_23[df_vars_23['county'].isin(counties)]

    # Renames variables
    df_vars_23 = df_vars_23.rename(columns = {'B03002_001E':'pop_18',
                                                'B03002_003E':'white_18',
                                                'B19001_001E':'hh_18',
                                                'B19013_001E':'hinc_18',
                                                'B25077_001E':'mhval_18',
                                                'B25077_001M':'mhval_18_se',
                                                'B25064_001E':'mrent_18',
                                                'B25064_001M':'mrent_18_se',
                                                'B25003_002E':'ohu_18',
                                                'B25003_003E':'rhu_18',
                                                'B25105_001E':'mmhcosts_18',
                                                'B15003_001E':'total_25_18',
                                                'B15003_022E':'total_25_col_bd_18',
                                                'B15003_023E':'total_25_col_md_18',
                                                'B15003_024E':'total_25_col_pd_18',
                                                'B15003_025E':'total_25_col_phd_18',
                                                'B25034_001E':'tot_units_built_18',
                                                'B25034_010E':'units_40_49_built_18',
                                                'B25034_011E':'units_39_early_built_18',
                                                'B07010_025E':'mov_wc_w_income_18',
                                                'B07010_026E':'mov_wc_9000_18',
                                                'B07010_027E':'mov_wc_15000_18',
                                                'B07010_028E':'mov_wc_25000_18',
                                                'B07010_029E':'mov_wc_35000_18',
                                                'B07010_030E':'mov_wc_50000_18',
                                                'B07010_031E':'mov_wc_65000_18',
                                                'B07010_032E':'mov_wc_75000_18',
                                                'B07010_033E':'mov_wc_76000_more_18',
                                                'B07010_036E':'mov_oc_w_income_18',
                                                'B07010_037E':'mov_oc_9000_18',
                                                'B07010_038E':'mov_oc_15000_18',
                                                'B07010_039E':'mov_oc_25000_18',
                                                'B07010_040E':'mov_oc_35000_18',
                                                'B07010_041E':'mov_oc_50000_18',
                                                'B07010_042E':'mov_oc_65000_18',
                                                'B07010_043E':'mov_oc_75000_18',
                                                'B07010_044E':'mov_oc_76000_more_18',
                                                'B07010_047E':'mov_os_w_income_18',
                                                'B07010_048E':'mov_os_9000_18',
                                                'B07010_049E':'mov_os_15000_18',
                                                'B07010_050E':'mov_os_25000_18',
                                                'B07010_051E':'mov_os_35000_18',
                                                'B07010_052E':'mov_os_50000_18',
                                                'B07010_053E':'mov_os_65000_18',
                                                'B07010_054E':'mov_os_75000_18',
                                                'B07010_055E':'mov_os_76000_more_18',
                                                'B07010_058E':'mov_fa_w_income_18',
                                                'B07010_059E':'mov_fa_9000_18',
                                                'B07010_060E':'mov_fa_15000_18',
                                                'B07010_061E':'mov_fa_25000_18',
                                                'B07010_062E':'mov_fa_35000_18',
                                                'B07010_063E':'mov_fa_50000_18',
                                                'B07010_064E':'mov_fa_65000_18',
                                                'B07010_065E':'mov_fa_75000_18',
                                                'B07010_066E':'mov_fa_76000_more_18',
                                                'B06011_001E':'iinc_18',
                                                'B19001_002E':'I_10000_18',
                                                'B19001_003E':'I_15000_18',
                                                'B19001_004E':'I_20000_18',
                                                'B19001_005E':'I_25000_18',
                                                'B19001_006E':'I_30000_18',
                                                'B19001_007E':'I_35000_18',
                                                'B19001_008E':'I_40000_18',
                                                'B19001_009E':'I_45000_18',
                                                'B19001_010E':'I_50000_18',
                                                'B19001_011E':'I_60000_18',
                                                'B19001_012E':'I_75000_18',
                                                'B19001_013E':'I_100000_18',
                                                'B19001_014E':'I_125000_18',
                                                'B19001_015E':'I_150000_18',
                                                'B19001_016E':'I_200000_18',
                                                'B19001_017E':'I_201000_18'})


    print('Result:')
    display(df_vars_23); print(); print()



    # Download ACS 2018 5-Year Estimates --------------------------------------------------------------------------
    # Note: If additional cities are added, make sure to change create_lag_vars.r
    # accordingly.

    # List variables of interest
    df_vars_18=['B25077_001E',
                'B25077_001M',
                'B25064_001E',
                'B25064_001M',
                'B07010_025E',
                'B07010_026E',
                'B07010_027E',
                'B07010_028E',
                'B07010_029E',
                'B07010_030E',
                'B07010_031E',
                'B07010_032E',
                'B07010_033E',
                'B07010_036E',
                'B07010_037E',
                'B07010_038E',
                'B07010_039E',
                'B07010_040E',
                'B07010_041E',
                'B07010_042E',
                'B07010_043E',
                'B07010_044E',
                'B07010_047E',
                'B07010_048E',
                'B07010_049E',
                'B07010_050E',
                'B07010_051E',
                'B07010_052E',
                'B07010_053E',
                'B07010_054E',
                'B07010_055E',
                'B07010_058E',
                'B07010_059E',
                'B07010_060E',
                'B07010_061E',
                'B07010_062E',
                'B07010_063E',
                'B07010_064E',
                'B07010_065E',
                'B07010_066E',
                'B06011_001E']


    # Run API query
    print('Fetching ACS 5-year estimates for 2018...');print(); print()
    var_dict_acs5 = c.acs5.get(df_vars_18, geo = {'for': 'tract:*', 'in': sql_query}, year=2018)


    # Converts variables into dataframe and filters only FIPS of interest
    df_vars_18 = pd.DataFrame.from_dict(var_dict_acs5)
    df_vars_18['FIPS']=df_vars_18['state']+df_vars_18['county']+df_vars_18['tract']
    df_vars_18 = df_vars_18[df_vars_18['county'].isin(counties)]

    # Renames variables
    df_vars_18 = df_vars_18.rename(columns = {'B25077_001E':'mhval_12',
                                                'B25077_001M':'mhval_12_se',
                                                'B25064_001E':'mrent_12',
                                                'B25064_001M':'mrent_12_se',
                                                'B07010_025E':'mov_wc_w_income_12',
                                                'B07010_026E':'mov_wc_9000_12',
                                                'B07010_027E':'mov_wc_15000_12',
                                                'B07010_028E':'mov_wc_25000_12',
                                                'B07010_029E':'mov_wc_35000_12',
                                                'B07010_030E':'mov_wc_50000_12',
                                                'B07010_031E':'mov_wc_65000_12',
                                                'B07010_032E':'mov_wc_75000_12',
                                                'B07010_033E':'mov_wc_76000_more_12',
                                                'B07010_036E':'mov_oc_w_income_12',
                                                'B07010_037E':'mov_oc_9000_12',
                                                'B07010_038E':'mov_oc_15000_12',
                                                'B07010_039E':'mov_oc_25000_12',
                                                'B07010_040E':'mov_oc_35000_12',
                                                'B07010_041E':'mov_oc_50000_12',
                                                'B07010_042E':'mov_oc_65000_12',
                                                'B07010_043E':'mov_oc_75000_12',
                                                'B07010_044E':'mov_oc_76000_more_12',
                                                'B07010_047E':'mov_os_w_income_12',
                                                'B07010_048E':'mov_os_9000_12',
                                                'B07010_049E':'mov_os_15000_12',
                                                'B07010_050E':'mov_os_25000_12',
                                                'B07010_051E':'mov_os_35000_12',
                                                'B07010_052E':'mov_os_50000_12',
                                                'B07010_053E':'mov_os_65000_12',
                                                'B07010_054E':'mov_os_75000_12',
                                                'B07010_055E':'mov_os_76000_more_12',
                                                'B07010_058E':'mov_fa_w_income_12',
                                                'B07010_059E':'mov_fa_9000_12',
                                                'B07010_060E':'mov_fa_15000_12',
                                                'B07010_061E':'mov_fa_25000_12',
                                                'B07010_062E':'mov_fa_35000_12',
                                                'B07010_063E':'mov_fa_50000_12',
                                                'B07010_064E':'mov_fa_65000_12',
                                                'B07010_065E':'mov_fa_75000_12',
                                                'B07010_066E':'mov_fa_76000_more_12',
                                                'B06011_001E':'iinc_12'})


    print('Result:')
    display(df_vars_18); print(); print()


    # Decennial Census 2000 Variables
    var_sf1=['P004001',
                'P004005',
                'H004001',
                'H004002',
                'H004003']

    var_sf3=['P037001',
                'P037015',
                'P037016',
                'P037017',
                'P037018',
                'P037032',
                'P037033',
                'P037034',
                'P037035',
                'H085001',
                'H063001',
                'P052001',
                'P053001']

    var_str = 'P0'
    var_list = []
    for i in range (2, 18):
        var_list.append(var_str+str(52000+i))

    var_sf3 = var_sf3 + var_list




    # Run API query
    # NOTE: on certain days, Census API may argue about too many queries and this section
    # may get hung up.


    print('Fetching decennial data for 2020...');print(); print()

    # SF1
    var_dict_sf1 = c.sf1.get(var_sf1, geo = {'for': 'tract:*', 'in': sql_query}, year=2000)

    # SF3
    var_dict_sf3 = c.sf3.get(var_sf3, geo = {'for': 'tract:*', 'in': sql_query}, year=2000)



    # Converts variables into dataframe and filters only FIPS of interest
    df_vars_sf1 = pd.DataFrame.from_dict(var_dict_sf1)
    df_vars_sf3 = pd.DataFrame.from_dict(var_dict_sf3)
    df_vars_sf1['FIPS']=df_vars_sf1['state']+df_vars_sf1['county']+df_vars_sf1['tract']
    df_vars_sf3['FIPS']=df_vars_sf3['state']+df_vars_sf3['county']+df_vars_sf3['tract']
    df_vars_sf1 = df_vars_sf1[df_vars_sf1['county'].isin(counties)]
    df_vars_sf3 = df_vars_sf3[df_vars_sf3['county'].isin(counties)]


    # Renames variables
    df_vars_sf1 = df_vars_sf1.rename(columns = {'P004001':'pop_00',
                                                'P004005':'white_00',
                                                'H004001':'hu_00',
                                                'H004002':'ohu_00',
                                                'H004003':'rhu_00'})

    df_vars_sf3 = df_vars_sf3.rename(columns = {'P037001':'total_25_00',
                                                'P037015':'male_25_col_bd_00',
                                                'P037016':'male_25_col_md_00',
                                                'P037017':'male_25_col_psd_00',
                                                'P037018':'male_25_col_phd_00',
                                                'P037032':'female_25_col_bd_00',
                                                'P037033':'female_25_col_md_00',
                                                'P037034':'female_25_col_psd_00',
                                                'P037035':'female_25_col_phd_00',
                                                'H085001':'mhval_00',
                                                'H063001':'mrent_00',
                                                'P052001':'hh_00',
                                                'P053001':'hinc_00',
                                                'P052002':'I_10000_00',
                                                'P052003':'I_15000_00',
                                                'P052004':'I_20000_00',
                                                'P052005':'I_25000_00',
                                                'P052006':'I_30000_00',
                                                'P052007':'I_35000_00',
                                                'P052008':'I_40000_00',
                                                'P052009':'I_45000_00',
                                                'P052010':'I_50000_00',
                                                'P052011':'I_60000_00',
                                                'P052012':'I_75000_00',
                                                'P052013':'I_100000_00',
                                                'P052014':'I_125000_00',
                                                'P052015':'I_150000_00',
                                                'P052016':'I_200000_00',
                                                'P052017':'I_201000_00'})

    df_vars_00 = df_vars_sf1.merge(df_vars_sf3.drop(columns=['county', 'state', 'tract']), on = 'FIPS')


    print('Result:')
    display(df_vars_00); print(); print()



    