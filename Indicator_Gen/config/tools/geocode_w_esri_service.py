

print(); print()


'''

Import data that is prepared to be geocoded
Connect to ArcGIS Online account
Use ESRI geocoding services to geocode addresses in batches (uses credits)
Export to filegdb

'''


# Workspace -------------------------------------------------------------------------------------------------------------------------------------------------------------



import pandas as pd
import geopandas as gpd
import getpass
from pathlib import Path
from tqdm import tqdm
from arcgis.gis import GIS
from arcgis.features import GeoAccessor
from arcgis.geocoding import batch_geocode
from IPython.display import display


def extract_coords(df):
    df_coords = df['location'].apply(pd.Series)
    df = pd.concat([df, df_coords], axis=1)
    df = df.rename(columns={'x':'LONGITUDE', 'y':'LATITUDE'})
    return df

def extract_attributes(df):
    df_attributes = df['attributes'].apply(pd.Series)
    df = pd.concat([df, df_attributes], axis=1)
    return df



def geocode_w_esri_service(file_to_geocode, col_address):

    '''
    Connects to the ArcGIS Online account, using input username and password credentials
    Imports csv file of data with address field to be geocoded
    Geocodes the addresses using the ESRI geocoding services
    Exports csv file of results to same place as imported data
    Exports feature class to desired file geodatabase

    User inputs: 
    file_to_geocode     = Path - path to csv file that has address field that needs geocoding
    col_address         = String - name of the address column that needs to be geocoded

    return:
    a pandas dataframe with geocoded results

    Note:
    col_address needs to be one address field in the following format:  1415 L ST, SACRAMENTO, CA 95814

    '''

    df_to_geocode = pd.read_csv(file_to_geocode)

    print('Geocoded dataset:')
    display(df_to_geocode.head())
    address_to_geocode = list(df_to_geocode[col_address].unique()); print(); print()
    n_address = len(address_to_geocode)
    print('Number of addresses to geocode: ', n_address)
    print('Sample of addresses: ')
    print(address_to_geocode[0:15]); print(); print()


    # Connect to ArcGIS Online
    print('ArcGIS Online Login')
    agol_username = input('Username: ')
    agol_password = getpass.getpass("Password (hidden during input): "); print()
    print('Setting up AGOL connection...')
    gis = GIS("https://www.arcgis.com", agol_username, agol_password); print(); print()
    credits_per_address = 40/1000 # 40 credits per 1k addresses
    print(f'Available credits: {gis.admin.credits.credits}')
    print(f'Number of credits needed to geocode {n_address} addresses: {n_address*credits_per_address}'); print()
    proceed = input('If you want to proceed, then enter "Yes": '); print(); print()


    # Geocoding by batches
    if proceed == 'Yes':
        print('Geocoding in batches...')
        batch_size = 100
        batches = [address_to_geocode[x:x+batch_size] for x in range(0, n_address, batch_size)]

        list_batches = []
        for batch in tqdm(batches):
            try:
                # Geocode and store results in list
                batch_results = batch_geocode(batch)
                df_batch = pd.DataFrame(batch_results)
                df_batch = extract_coords(df_batch)
                df_batch = extract_attributes(df_batch)
                list_batches.append(df_batch)

                # Export results as failsafe
                index_batch = batches.index(batch)
                if index_batch == 0:
                    folder_batches = file_to_geocode.parent / 'batches'
                    folder_batches.mkdir(exist_ok=True)
                df_batch.to_csv(folder_batches / f'{file_to_geocode}__geocoded_esri__batch{index_batch}.csv', index=False)
                
            except Exception as e: print(e)

        df_geocoded = pd.concat(list_batches)
        df_geocoded = df_geocoded.reset_index(drop=True)
        print(); print()
        print('Final result: ')
        display(df_geocoded)

        return df_geocoded
    



def send_to_filegdb(df, file_fc, lon, lat):
    '''
    Sends data frame with geometry field to file geodatabase, starting with WGS CRS
    '''
    geometry = gpd.points_from_xy(df[lon], df[lat])
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    gdf = gdf.to_crs('EPSG:2226')
    sdf = GeoAccessor.from_geodataframe(gdf, column_name='geometry')
    sdf.spatial.to_featureclass(location=file_fc)






# Main ----------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    ## Inputs:
    # Path and file name of csv that needs to be geocoded
    # Path of file geodatabase and desired filename of output feature class
    # Name of column that has addresses

    geocoding_service = 'ESRI'
    file_to_geocode = Path(r'P:\Employment Inventory\Employment_2025\Processed_Clean\QC')    / 'EDD_address_to_geocode.csv'
    file_to_send_to_gdb = Path(r"P:/Employment Inventory/Employment_2025/ArcPro/Costar.gdb") / f'{file_to_geocode.stem}__geocoded_{geocoding_service}'
    col_address = 'address_to_geocode'

    # Geocoding
    df_geocoded = geocode_w_esri_service(file_to_geocode, col_address)


    # Exporting csv
    print('Exporting results to csv in the following folder: ', file_to_geocode.parent)
    df_geocoded.to_csv(file_to_geocode.parent / f'{file_to_geocode.stem}__geocoded_{geocoding_service}.csv', index=False)

    # Exporting to filegdb
    print('Converting to point layer and exporting to the following gdb: ', file_to_send_to_gdb)
    send_to_filegdb(df_geocoded, file_to_send_to_gdb, 'Longitude', 'Latitude')


  
