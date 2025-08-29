

print(); print()

# Workspace -------------------------------------------------------------------------------------------------------------------------------------------------------------


# Packages
import pandas as pd
import getpass
from pathlib import Path
from tqdm import tqdm
from arcgis.gis import GIS
from arcgis.geocoding import geocode
from arcgis.geocoding import batch_geocode
from IPython.display import display

# Functions
def extract_coords(df):
    df_coords = df['location'].apply(pd.Series)
    df = pd.concat([df, df_coords], axis=1)
    df = df.rename(columns={'x':'LONGITUDE', 'y':'LATITUDE'})
    return df

def extract_attributes(df):
    df_attributes = df['attributes'].apply(pd.Series)
    df = pd.concat([df, df_attributes], axis=1)
    return df


# File to geocode
path_ = Path(r'P:\Employment Inventory\Employment_2025\Processed_Clean\QC')
file_to_geocode = 'EDD_addresses_to_geocoded.csv'



# Main ----------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
  

    # Prep addresses for geocoding
    df_to_geocode = pd.read_csv(path_ / file_to_geocode)


    '''This block is intended to clean specific input dataframe to get addresses ready for geocoding'''

    df_to_geocode = df_to_geocode.drop(['LATITUDE', 'LONGITUDE', 'Address', 'City', 'County', 'ZIP'], axis=1).rename(columns={'Latitude':'LATITUDE', 'Longitude':'LONGITUDE'})
    df_to_geocode = df_to_geocode[df_to_geocode['Geocoded'] == 'Y']
    df_to_geocode = df_to_geocode['PHYSICAL_STATE'].fillna('CA')
    df_to_geocode = df_to_geocode[['UIACCT_REPORTINGUNIT', 'PHYSICAL_STREET', 'PHYSICAL_CITY', 'PHYSICAL_STATE', 'PHYSICAL_ZIP', 'LATITUDE', 'LONGITUDE']]

    df_to_geocode['address_to_geocode'] = df_to_geocode['PHYSICAL_STREET'] + ', ' + df_to_geocode['PHYSICAL_CITY'] + ', ' + df_to_geocode['PHYSICAL_STATE']

    ''''''

    print('Geocoded dataset:')
    display(df_to_geocode.head())
    df_to_geocode = df_to_geocode.head(14)
    address_to_geocode = list(df_to_geocode['address_to_geocode'].unique()); print(); print()
    print('Addresses to geocode: ')
    print(address_to_geocode); print(); print()


    # Connect to ArcGIS Online
    print('ArcGIS Online Login')
    agol_username = input('Username: ')
    agol_password = getpass.getpass("Password (hidden during input): "); print()
    print('Setting up AGOL connection...')
    gis = GIS("https://www.arcgis.com", agol_username, agol_password); print(); print()
    n_address = len(address_to_geocode)
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
                    folder_batches = path_ / 'batches'
                    folder_batches.mkdir(exist_ok=True)
                df_batch.to_csv(folder_batches / f'{file_to_geocode}__geocoded_w_agol__batch{index_batch}.csv', index=False)

            except Exception as e: print(e)

        df_geocoded = pd.concat(list_batches)
        df_geocoded = df_geocoded.reset_index(drop=True)
        print(); print()
        print('Final result: ')
        display(df_geocoded)
        df_geocoded.to_csv(path_ / f'{file_to_geocode}__geocoded_w_agol.csv', index=False)



# Code graveyard -----------------------------------------------------------------------------

# # Option 1: Connect to ArcGIS Online anonymously (for simple geocoding not requiring credits)
# gis = GIS()

