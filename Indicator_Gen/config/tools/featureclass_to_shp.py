
'''
This script converts a vector GIS file (shapefile, geojson, etc...) to a file geodatabase feature class
i.e. Import data using geopandas, transform geometry to desired CRS, convert object to spatial dataframe, export to gdb
'''


import geopandas as gpd
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from pathlib import Path
import time
from datetime import date
import pyogrio


def convert_fc_to_shp(file_to_convert, file_shp, crs, add_date=True):

    '''
    Function to convert a feature class in a file geodatabase to a shapefile

    Parameters:
    file_to_convert - string = file path to a feature class in a file geodatabase
    file_shp        - string = file path of file geodatabase
    crs             - string = desired CRS of output feature class
    '''

    print(f'\n\nImporting feature class from file geodatabase {file_to_convert}...\n\n')
    gdf_data = gpd.read_file(str(Path(file_to_convert).parent), layer=Path(file_to_convert).stem, engine='pyogrio')

    if gdf_data.crs != crs:
        gdf_data = gdf_data.to_crs(crs)

    if add_date:
        shp_name = f"{Path(file_to_convert).stem}_{date.today().strftime('%Y%m')}"
    else:
        shp_name = Path(file_to_convert).stem
    file_shp = Path(file_shp) / shp_name

    print(f'Exporting feature class {file_to_convert} to the file geodatabase {str(file_shp)}...\n\n')
    start_time = time.time()
    gdf_data.to_file(str(file_shp), driver="ESRI Shapefile", engine="pyogrio")
    print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---\n")



if __name__ == '__main__':


    file_to_convert = r'I:\Projects\Josh\Regional Monitoring\Employment Inventory\ArcPro\EmploymentInventory_EDA.gdb\EDD_2025q3'
    file_shp = r'I:\Projects\Josh\Conveyal\inputs\shp\jobs'

    crs = 'EPSG:2226'

    convert_fc_to_shp(file_to_convert, file_shp, crs, add_date=False)