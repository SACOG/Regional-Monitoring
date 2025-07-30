
'''
This script converts a vector GIS file (shapefile, geodatabase, geojson, etc...) to a file geodatabase feature class
i.e. Import data using geopandas, transform geometry to desired CRS, convert object to spatial dataframe, export to gdb
'''

print(); print()


## Setup ================================================================================================


## Packages ---

import pandas as pd
import geopandas as gpd
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from pathlib import Path


## User defined functions ---

# Function to convert geospatial file to file geodatabase feature class
def fc_convert(file_to_convert, file_gdb, crs):

    '''
    Parameters:
    file_to_convert = file path to vector GIS file that the user wants to convert to a file geodatabase feature class
    file_gdb        = file path of file geodatabase
    crs             = desired CRS of output feature class
    '''

    print(f'Importing GIS file {file_to_convert}...'); print();print()
    
    gdf_data = gpd.read_file(file_to_convert)
    gdf_data = gdf_data.to_crs(crs)

    sdf_data = GeoAccessor.from_geodataframe(gdf_data, column_name='geometry')

    fc_name = file_to_convert.stem
    file_fc = file_gdb / fc_name

    print(f'Exporting feature class {file_to_convert} to the file geodatabase {file_gdb}...'); print(); print()
    sdf_data.spatial.to_featureclass(location=file_fc)
    print(f'Successfully exported to the following location: {file_gdb}'); print(); print()



## Main ================================================================================================


if __name__ == '__main__':

    # file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_counties_sacog\tl_2020_sacog_county.shp')
    # file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_valleyvision_bg\tl_2020_valleyvision_bg.shp')
    file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_valleyvision_county\tl_2020_valleyvision_county.shp')
    # file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_cdp_06\tl_2020_cdp_06.shp')
    # file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_tracts_sacog\tl_2020_sacog_tracts.shp')
    # file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_bg_sacog\tl_2020_sacog_bg.shp')
    # file_to_convert = Path(r'I:\Projects\Josh\Geospatial Data\TIGER\shp\2020_blocks_sacog\tl_2020_sacog_blocks.shp')

    file_gdb = Path(r'I:\Projects\Josh\Regional Monitoring\ArcPro_sup\Accessibility\Accessibility.gdb')



    crs = 'EPSG:2284'

    fc_convert(file_to_convert, file_gdb, crs)