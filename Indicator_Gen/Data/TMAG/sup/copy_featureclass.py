
'''
This script copies/pastes a feature class from one file geodatabse to another
'''


import time
from datetime import date
from pathlib import Path

import geopandas as gpd
from arcgis.features import GeoAccessor, GeoSeriesAccessor


def copy_fc_to_filegdb(file_to_copy, gdb_to_copy_file_to, crs, add_date=True):

    '''
    Function to convert a feature class in a file geodatabase to a shapefile

    Parameters:
    file_to_convert - string = file path to a feature class in a file geodatabase
    file_shp        - string = file path of file geodatabase
    crs             - string = desired CRS of output feature class
    '''

    print(f'\n\nImporting feature class from file geodatabase {file_to_copy}...\n')    
    gdf_data = gpd.read_file(str(Path(file_to_copy).parent), layer=Path(file_to_copy).stem, engine='pyogrio')
    gdf_data = gdf_data.to_crs(crs)


    print(f'Exporting feature class {file_to_copy} to the file geodatabase {gdb_to_copy_file_to}...\n')
    start_time = time.time()
    if add_date:
        fc_out = f'{gdb_to_copy_file_to}_{date.today().strftime('%Y%m')}'
    else:
        fc_out = gdb_to_copy_file_to
    sdf_data = GeoAccessor.from_geodataframe(gdf_data, column_name='geometry')
    sdf_data.spatial.to_featureclass(location=fc_out)
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---\n")



if __name__ == '__main__':

    # add_date=True
    # file_to_copy  = r'P:\CMP\2026\CMP_network\CMP_network.gdb\ExistingBikeway'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\Conveyal\ArcPro\Conveyal_Layers.gdb\ExistingBikeway'

    # add_date=False
    # file_to_copy  = r'I:\Projects\Josh\POI\ArcPro\POI.gdb\POI_202607'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\Conveyal\ArcPro\Conveyal_Layers.gdb\POI_202607'

    # add_date=True
    # file_to_copy  = r'I:\Data\Assessor_2026\SacCounty_Addresses\SacCountyAddresses.gdb\Address'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\Regional Monitoring\Employment Inventory\ArcPro\EmploymentInventory_EDA.gdb\Address'

    # add_date=False
    # file_to_copy  = r'I:\Projects\Josh\PPA\Layer_update\Congestion\Congestion Layer Corrections 2025\Congestion Layer Corrections 2025.gdb\NPMRDS_2025data_20260723_1158'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\PPA\Layer_update\Congestion\Congestion Layer Corrections 2025\Congestion Layer Corrections 2025.gdb\NPMRDS_2025data_202607'

    # add_date=False
    # file_to_copy  = r'C:\Users\jfontes\Documents\Projects\Local\PPA\Layer_update\PPA3_local_TEST.gdb\NPMRDS_2025_data_20260826_1322_TEST'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\PPA\Layer_update\Congestion\Congestion Layer Corrections 2025\Congestion Layer Corrections 2025.gdb\NPMRDS_2025_data_202608_QCTESTRUN'

    # add_date=False
    # file_to_copy  = r'I:\Projects\Darren\PPA3_GIS\PPA3_GIS.gdb\NPMRDS_2023ppadata_final'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\PPA\Layer_update\Congestion\Congestion Layer Corrections 2025\Congestion Layer Corrections 2025.gdb\NPMRDS_2023ppadata_final_QCCOPY'

    # add_date=False
    # file_to_copy  = r'I:\Projects\Darren\PPA3_GIS\PPA3.0_archive.gdb\INRIX_SHP_2020_2021_SACOG'
    # gdb_to_copy_file_to = r'I:\Projects\Josh\PPA\Layer_update\Congestion\Congestion Layer Corrections 2025\Congestion Layer Corrections 2025.gdb\INRIX_SHP_2020_2021_SACOG_QCCOPY'
    
    add_date=False
    file_to_copy  = r'C:\Users\jfontes\Documents\Projects\Local\PPA\Layer_update\PPA3_local_TEST.gdb\NPMRDS_2025_data_20260827_1429_QCTESTRUN_V3'
    gdb_to_copy_file_to = r'I:\Projects\Josh\PPA\Layer_update\Congestion\Congestion Layer Corrections 2025\Congestion Layer Corrections 2025.gdb\NPMRDS_2025_data_20260827_1429_QCTESTRUN_V3'


    crs = 'EPSG:2226'

    copy_fc_to_filegdb(file_to_copy, gdb_to_copy_file_to, crs, add_date=add_date)