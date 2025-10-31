


'''

Import data that is prepared to be geocoded
Connect to SACOG Portal account
Import internal SACOG locator
Use the locator to geocode addresses (one at a time)
Calculate summary statistics of data and geocoded results
Export to filegdb

'''



print(); print()




# Workspace -------------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
import geopandas as gpd
import getpass
from pathlib import Path
from tqdm import tqdm
from arcgis.gis import GIS
from arcgis.geocoding import Geocoder
from arcgis.features import GeoAccessor
from IPython.display import display



def geocode_w_sacog_locator(file_to_geocode, col_address, locator_ID):

    '''
    Connects to the SACOG GIS Portal, using input username and password credentials
    Imports the desired locator for geocoding, using the Source ID of the locator
    Imports csv file of data with address field to be geocoded
    Geocodes the addresses using the imported locator
    Exports csv file of results to same place as imported data
    Exports feature class to desired file geodatabase

    User inputs: 
    file_to_geocode     = Path - path to csv file that has address field that needs geocoding
    col_address         = String - name of the address column that needs to be geocoded
    locator_ID          = String - Source ID of the locator available through Portal

    return:
    a pandas dataframe with geocoded results

    Note:
    col_address needs to be one address field in the following format:  1415 L ST, SACRAMENTO, CA 95814

    '''

    # Prep addresses for geocoding
    df_to_geocode = pd.read_csv(file_to_geocode, dtype=str)

    df_to_geocode[col_address] = df_to_geocode[col_address].str.upper()
    df_to_geocode[col_address] = df_to_geocode[col_address].str.replace('\s+', ' ', regex=True).str.strip()

    print('Geocoded dataset:')
    display(df_to_geocode.head(10))
    address_to_geocode = list(df_to_geocode[col_address].tolist()); print(); print()
    n_address = len(address_to_geocode)
    print('Number of addresses to geocode: ', n_address)
    print('Sample of addresses: ')
    print(address_to_geocode[0:10]); print(); print()


    # Connect to SACOG Portal
    print('SACOG Portal Login:')
    portal_url = "https://portal.sacog.org/portal/home/"
    agol_username = input('Username: ') # nt-domain\username
    agol_password = getpass.getpass("Password (hidden during input): "); print()
    print('Setting up Portal connection...')
    gis = GIS(portal_url, agol_username, agol_password); print(); print()

    # Set up locator using the Source ID
    locator_item = gis.content.get(locator_ID)
    locator = Geocoder.fromitem(locator_item)


    # Geocoding one address at a time
    print('Locator is set up, geocoding one address at a time :(   ...')
    df_geocoded = df_to_geocode.copy()
    df_geocoded['Latitude'     ] = None
    df_geocoded['Longitude'    ] = None
    df_geocoded['Score'        ] = None
    df_geocoded['Match_Address'] = None

    for index, row in tqdm(df_geocoded.iterrows()):
        address = row['address_to_geocode']
        try:
            # Geocode the address
            geocode_result = locator.geocode(address)

            if geocode_result:
                # Extract relevant information from the first candidate
                df_geocoded.loc[index, 'Latitude'     ] = geocode_result[0]['location']['y']
                df_geocoded.loc[index, 'Longitude'    ] = geocode_result[0]['location']['x']
                df_geocoded.loc[index, 'Score'        ] = geocode_result[0]['score']
                df_geocoded.loc[index, 'Match_Address'] = geocode_result[0]['address']
            else:
                print(f"No match found for: {address}")
        except Exception as e:
            print(f"Error geocoding {address}: {e}")


    print(); print()
    print('Final result: ')
    display(df_geocoded)

    return df_geocoded



def send_to_filegdb(df, file_fc):
    '''
    Sends data frame with geometry field to file geodatabase
    '''
    geometry = gpd.points_from_xy(df['Longitude'], df['Latitude'])
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    gdf = gdf.to_crs('EPSG:2226')
    sdf = GeoAccessor.from_geodataframe(gdf, column_name='geometry')
    sdf.spatial.to_featureclass(location=file_fc)




# Main ----------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    ## Inputs:
    # Path and file name of csv that needs to be geocoded
    # Path of file geodatabase and desired filename of output feature class
    # Source ID available on SACOG GIS Portal
    # Name of column that has addresses

    file_to_geocode = Path(r'P:\Employment Inventory\Employment_2025\Processed_Clean\QC')    / 'EDD_address_to_geocode__indrani.csv'
    file_to_send_to_gdb = Path(r"P:/Employment Inventory/Employment_2025/ArcPro/Costar.gdb") / f'{file_to_geocode.stem}__geocoded_SACOG_Addr_Locatr_2024'
    # locator_ID = 'c778cdd083ea4badb1afd05ad4b2ca74' # SACOG_Addr_Locatr_2022 (can be found on Portal)
    locator_ID = '84885daa01ac4abfbbdc9e413da0d891' # SACOG_Addr_Locatr_2024_WGS (can be found on Portal)
    col_address = 'address_to_geocode'

    # Geocoding
    df_geocoded = geocode_w_sacog_locator(file_to_geocode, col_address, locator_ID)



    # Exporting csv
    print('Exporting results to csv in the following folder: ', file_to_geocode.parent)
    df_geocoded.to_csv(file_to_geocode.parent / f'{file_to_geocode.stem}__geocoded_SACOG_Addr_Locatr_2024.csv', index=False)

    # Exporting to filegdb
    print('Converting to point layer and exporting to the following gdb: ', file_to_send_to_gdb)
    send_to_filegdb(df_geocoded, file_to_send_to_gdb)


  