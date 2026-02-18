

def print2(): print(); print()




EXPORT=False





## Preparing Workspace ---------------------------------------------------------------------------------------------------------------


import numpy as np
import pandas as pd
from pathlib import Path
from xlwt.Workbook import *
from IPython.display import display

PATH_GIT = Path(__file__).parent.parent.parent
PATH_CONFIG0 = PATH_GIT / 'config'


# Network paths
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data') / 'Zillow'
PATH_MAIN = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' / 'Data'
PATH_OUT = PATH_MAIN / 'Vibrant and Inclusive Places' / 'Development' / 'Housing Cost'
PATH_WEIGHTS = PATH_MAIN / 'Reference' / 'Weights'



import sys
sys.path.append(str(PATH_CONFIG0))
import functions as func
import plot as pt



def process_nonmpo(df):

    metros = ['Sacramento-Roseville-Folsom, CA', 'Yuba City, CA']
    print()

    # Load CSV file
    # Subset and rename cols

    if geography == 'Neighborhoods':
        regiontype = 'neighborhood'
    if geography == 'ZIP Codes':
        regiontype = 'zip'
    if geography == 'Cities':
        regiontype = 'city'
    if geography == 'Counties':
        regiontype = 'county'
    df = df[df['RegionType'] == regiontype]

    cols_dates = [col for col in df.columns if '20' in col]
    if 'CountyName' in df.columns: cols_geos = ['StateName', 'Metro', 'CountyName', 'RegionName']
    else: cols_geos = ['StateName', 'Metro', 'RegionName']

    df = df[cols_geos + cols_dates]
    df = pd.melt(df, id_vars=cols_geos, var_name='date_', value_name='Price')
    df = df[df['StateName'].isin(['CA'])]
    df = df[df['Metro'].isin(metros)]

    if 'CountyName' in df.columns:
        df = df[['Metro', 'CountyName', 'RegionName', 'date_', 'Price']]
        df.columns = ['Metro', 'CountyName', geography, 'date_', 'Price']
        df = df.sort_values(by=['Metro', 'CountyName', geography, 'date_'], ascending=[True, True, True, False]).reset_index(drop=True)
    else:
        df = df[['Metro', 'RegionName', 'date_', 'Price']]
        df.columns = ['Metro', geography, 'date_', 'Price']
        df = df.sort_values(by=['Metro', geography, 'date_'], ascending=[True, True, False]).reset_index(drop=True)

    df['date_'] = pd.to_datetime(df['date_'])
    df['Year'] = df['date_'].dt.year

    if geography != 'Cities':
        if 'CountyName' in df.columns:
            df_yr = df.groupby(['Metro', 'CountyName', geography, 'Year'], as_index=False)['Price'].mean()
        else:
            df_yr = df.groupby(['Metro', geography, 'Year'], as_index=False)['Price'].mean()
    else:
        file_weights = PATH_WEIGHTS / 'Total_Households Places ACS5.xlsx'
        df_weights = pd.read_excel(file_weights)
        df_weights = df_weights[['NAME', 'Year', 'Households']].rename(columns={'NAME':'Cities'})
        df_temp  = df_weights[df_weights['Year'] == 2023]
        df_temp2 = df_weights[df_weights['Year'] == 2023]
        df_temp ['Year'] = 2024
        df_temp2['Year'] = 2025
        df_temp3 = df_weights[df_weights['Year'] == 2009]
        df_temp4 = df_weights[df_weights['Year'] == 2009]
        df_temp5 = df_weights[df_weights['Year'] == 2009]
        df_temp6 = df_weights[df_weights['Year'] == 2009]
        df_temp7 = df_weights[df_weights['Year'] == 2009]
        df_temp8 = df_weights[df_weights['Year'] == 2009]
        df_temp9 = df_weights[df_weights['Year'] == 2009]
        df_temp10 = df_weights[df_weights['Year'] == 2009]
        df_temp11 = df_weights[df_weights['Year'] == 2009]
        df_temp3['Year'] = 2008
        df_temp4['Year'] = 2007
        df_temp5['Year'] = 2006
        df_temp6['Year'] = 2005
        df_temp7['Year'] = 2004
        df_temp8['Year'] = 2003
        df_temp9['Year'] = 2002
        df_temp10['Year'] = 2001
        df_temp11['Year'] = 2000
        df_weights = pd.concat([df_weights, df_temp, df_temp2, df_temp3, df_temp4, df_temp5, df_temp6, df_temp7, df_temp8, df_temp9, df_temp10, df_temp11])
        df = df.merge(df_weights, on=['Cities', 'Year'], how='left')
        incorporated = ['Auburn', 'Citrus Heights', 'Colfax', 'Davis', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Lincoln', 'Live Oak', 'Loomis town', 'Marysville', 'Placerville'
                        , 'Rancho Cordova', 'Rocklin', 'Roseville', 'Sacramento', 'South Lake Tahoe', 'West Sacramento', 'Wheatland', 'Winters', 'Woodland', 'Yuba City']
        df.loc[~df['Cities'].isin(incorporated), 'Cities'] = 'Unincorporated'

        df_no_na = df.dropna().drop_duplicates().reset_index(drop=True)
        wm = lambda x: np.average(x, weights = df_no_na.loc[x.index, "Households"])
        if 'CountyName' in df.columns:
            df_yr = df_no_na.groupby(['Metro', 'CountyName', geography, 'Year' ], as_index=False).agg(Price=('Price', wm))
            df    = df_no_na.groupby(['Metro', 'CountyName', geography, 'date_'], as_index=False).agg(Price=('Price', wm))
        else:
            df_yr = df_no_na.groupby(['Metro', geography, 'Year' ], as_index=False).agg(Price=('Price', wm))
            df    = df_no_na.groupby(['Metro', geography, 'date_'], as_index=False).agg(Price=('Price', wm))

    df = df.drop_duplicates()
    if 'CountyName' in df.columns:
        df    = df   .sort_values(['Metro', 'CountyName', geography, 'date_'], ascending=[True, True, True, False]).reset_index(drop=True)
        df_yr = df_yr.sort_values(['Metro', 'CountyName', geography, 'Year' ], ascending=[True, True, True, False]).reset_index(drop=True)
    else:
        df    = df   .sort_values(['Metro', geography, 'date_'], ascending=[True, True, False]).reset_index(drop=True)
        df_yr = df_yr.sort_values(['Metro', geography, 'Year' ], ascending=[True, True, False]).reset_index(drop=True)

    df['date_'] = df['date_'].astype('str')

    display(df_yr.head(6))

    return df, df_yr


    
def process_mpo(df):

    print()
    sacog_state = ["Sacramento, CA", "Yuba City, CA"]

    ca_peers = ["Los Angeles, CA", "San Francisco, CA", "Riverside, CA", 
                "San Diego, CA", "Oxnard, CA", "Santa Rosa, CA", 
                "Vallejo, CA", "El Centro, CA", "Napa, CA", "San Jose, CA"]

    other_peers = ["Austin, TX", "Charlotte, NC", "Cincinnati, OH",
                    "Cleveland, OH", "Columbus, OH", "Detroit, MI",
                    "Indianapolis, IN", "Kansas City, MO", "Miami, FL", # Kansas City, KS or MO?
                    "Orlando, FL", "Phoenix, AZ", "Pittsburg, PA",
                    "Portland, OR", "Salt Lake City, UT", "San Antonio, TX",
                    "St. Louis, MO", "Tampa, FL"]

    sacog = ["Yuba City", "Sacramento"]
    mtc   = ["San Francisco", "Santa Rosa", "Vallejo", "Napa", 'San Jose']
    scag  = ["Los Angeles", "Riverside", "Oxnard", "El Centro"]
    
    # Load CSV file
    # Subset and rename cols
    # Removing trailing text from Region
    # Mutate function to get MSA col
    # Calculate median prices for each MSA
    # Combine all median dfs, and clean cols

    df = df[df['RegionType'] == 'msa']
    df = pd.melt(df, id_vars=['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName'], var_name='date_', value_name='Price')

    df = df[['RegionName', 'StateName', 'date_', 'Price']]
    df.columns = ['Region', 'State', 'date_', 'Price']
    df = df[df['Region'].isin(sacog_state + ca_peers + other_peers)]

    df['Region'] = df['Region'].str.replace(r',.*', '', regex=True)

    df['MSA'] = np.where(df['Region'].isin(sacog), 'SACOG'
                , np.where(df['Region'].isin(mtc), 'MTC'
                , np.where(df['Region'].isin(scag), 'SCAG'
                , np.where(df['Region'] == 'San Diego', 'SANDAG', df['Region']))))
    

    df['date_'] = pd.to_datetime(df['date_'])
    df['Year'] = df['date_'].dt.year

    file_weights = PATH_WEIGHTS / 'Total_Households MSA ACS1.xlsx'
    df_weights = pd.read_excel(file_weights)
    df_weights = df_weights[['MSA', 'Year', 'Households']]
    df_temp  = df_weights[df_weights['Year'] == 2023]
    df_temp2 = df_weights[df_weights['Year'] == 2023]
    df_temp ['Year'] = 2024
    df_temp2['Year'] = 2025
    df_temp3 = df_weights[df_weights['Year'] == 2005]
    df_temp4 = df_weights[df_weights['Year'] == 2005]
    df_temp5 = df_weights[df_weights['Year'] == 2005]
    df_temp6 = df_weights[df_weights['Year'] == 2005]
    df_temp7 = df_weights[df_weights['Year'] == 2005]
    df_temp3['Year'] = 2004
    df_temp4['Year'] = 2003
    df_temp5['Year'] = 2002
    df_temp6['Year'] = 2001
    df_temp7['Year'] = 2000
    df_temp8 = df_weights[df_weights['Year'] == 2021]
    df_temp8['Year'] = 2020
    df_weights = pd.concat([df_weights, df_temp, df_temp2, df_temp3, df_temp4, df_temp5, df_temp6, df_temp7, df_temp8])
    df_weights['Region'] = df_weights['MSA'].map(pt.peer_msa_labels)
    df_weights = df_weights.dropna(subset=['Region'])
    list_regions = sacog_state + ca_peers + other_peers
    df_weights = df_weights[df_weights['Region'].isin(list_regions)]
    df_weights['Region'] = df_weights['Region'].str.replace(r',.*', '', regex=True)
    df_weights = df_weights[['Region', 'Year', 'Households']]
    df = df.merge(df_weights, on=['Region', 'Year'], how='left')
    df = df.dropna(subset=['Households']).drop_duplicates().reset_index(drop=True)

    df_no_na = df.dropna().drop_duplicates().reset_index(drop=True)
    wm = lambda x: np.average(x, weights = df_no_na.loc[x.index, "Households"])
    sacog_mn = df_no_na[df_no_na['MSA'] == 'SACOG'].groupby(['MSA', 'date_'], as_index=False).agg(Price=('Price', wm))
    sacog_mn['State'] = 'CA'
    sacog_mn['Region'] = 'SACOG Weighted Average'
    sacog_mn.columns = ['MSA', 'date_', 'Price', 'State', 'Region']

    mtc_mn = df_no_na[df_no_na['MSA'] == 'MTC'].groupby(['MSA', 'date_'], as_index=False).agg(Price=('Price', wm))
    mtc_mn['State'] = 'CA'
    mtc_mn['Region'] = 'MTC Weighted Average'
    mtc_mn.columns = ['MSA', 'date_', 'Price', 'State', 'Region']

    scag_mn = df_no_na[df_no_na['MSA'] == 'SCAG'].groupby(['MSA', 'date_'], as_index=False).agg(Price=('Price', wm))
    scag_mn['State'] = 'CA'
    scag_mn['Region'] = 'SCAG Weighted Average'
    scag_mn.columns = ['MSA', 'date_', 'Price', 'State', 'Region']

    df = pd.concat([df, sacog_mn, mtc_mn, scag_mn])
    df = df[['State', 'Region', 'date_', 'Price']]
    df['date_'] = df['date_'].astype('str')
    df = df.drop_duplicates()
    df = df.sort_values(by=['State', 'Region', 'date_'], ascending=[True, True, False]).reset_index(drop=True)

    df_yr = df.copy()

    df_yr['date_'] = pd.to_datetime(df_yr['date_'])
    df_yr['Year'] = df_yr['date_'].dt.year
    df_yr = df_yr.drop('date_', axis=1)
    df_yr = df_yr.groupby(['State', 'Region', 'Year'], as_index=False)['Price'].mean()
    df_yr = df_yr.sort_values(by=['State', 'Region', 'Year'], ascending=[True, True, False])

    display(df_yr.head(6))

    return df, df_yr






## Main ---------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    sample_type = 'Zillow'
    indicators = ['Cost_1', 'Cost_2']

    print()

    dt_geo = {
            'Cost_1':
                {
                    'MSA'          : {'file_in':'Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'       , 'file_out': 'Cost_1 MSA Sales Price Zillow.xlsx'          },
                    'Counties'     : {'file_in':'County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'      , 'file_out': 'Cost_1 Counties Sales Price Zillow.xlsx'     },
                    'Cities'       : {'file_in':'City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'        , 'file_out': 'Cost_1 Cities Sales Price Zillow.xlsx'       },
                    'Neighborhoods': {'file_in':'Neighborhood_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv', 'file_out': 'Cost_1 Neighborhoods Sales Price Zillow.xlsx'},
                    'ZIP Codes'    : {'file_in':'Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'         , 'file_out': 'Cost_1 ZIP Codes Sales Price Zillow.xlsx'    }
                },
            'Cost_2':
                {
                    'MSA'      : {'file_in':'Metro_zori_uc_sfrcondomfr_sm_month.csv' , 'file_out': 'Cost_2 MSA Rent Price Zillow.xlsx'      },
                    'Counties' : {'file_in':'County_zori_uc_sfrcondomfr_sm_month.csv', 'file_out': 'Cost_2 Counties Rent Price Zillow.xlsx' },
                    'Cities'   : {'file_in':'City_zori_uc_sfrcondomfr_sm_month.csv'  , 'file_out': 'Cost_2 Cities Rent Price Zillow.xlsx'   },
                    'ZIP Codes': {'file_in':'Zip_zori_uc_sfrcondomfr_sm_month.csv'   , 'file_out': 'Cost_2 ZIP Codes Rent Price Zillow.xlsx'}
                }
        }

    for indicator in indicators:

        print2()
        print(indicator)

        for geography, files in dt_geo[indicator].items():

            print2()
            print(geography)
            print()

            file_in = PATH_ORIG / files['file_in']
            df = pd.read_csv(file_in)

            if geography == 'MSA':
                df, df_yr = process_mpo(df)
            else:
                df, df_yr = process_nonmpo(df)


            if EXPORT:

                year_start = df_yr['Year'].min()
                year_end   = df_yr['Year'].max()

                df_about = func.write_about(sample_type    = sample_type
                                            , indicator    = indicator
                                            , year_start   = year_start
                                            , year_end     = year_end
                                            , geography    = geography)
                print("About page documentation table:")
                display(df_about)

                if indicator == 'Cost_1':
                    PATH_SP = PATH_OUT / 'Cost_1 Sales Price'
                if indicator == 'Cost_2':
                    PATH_SP = PATH_OUT / 'Cost_2 Rent Prices'
                path_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")

                paths = [PATH_SP, path_server]
                workbook_name = files['file_out']

                for path_ in paths:
                    file_out = path_ / workbook_name
                    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
                        df_about.to_excel(writer, index=False, sheet_name='About'  , header=False)
                        df      .to_excel(writer, index=False, sheet_name='Monthly'              )
                        df_yr   .to_excel(writer, index=False, sheet_name='Annual'               )
                    print("Exported: ", path_)


