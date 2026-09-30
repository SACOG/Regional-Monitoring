
'''
This script converts a file geodatabase feature class to a shapefile
i.e. Import data using geopandas, transform geometry to desired CRS, subset to desired columns, export to shapefile

For Conveyal destinations, need shapefiles of the following point layers:
1) Jobs                  - using employment inventory developed with EDD
2) Schools               - using schools inventory developed with CDE
3) Neighborhood Services - using point of interest layer developed with Overture

After running this code and data is successfully exported, shapefiles are manually uploaded to Conveyal as Spatial Datasets
'''

from warnings import warn
from shapely import wkt
import arcpy
from arcpy import Describe
import geopandas as gpd
import pandas as pd
from pandas import read_csv
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from pathlib import Path
import time
from datetime import date
import pyogrio


CRS = 4326
PATH_CONFIG=Path(__file__).parent/'config'



def esri_to_df(esri_obj_path, include_geom, field_list=None, index_field=None, 
               crs_val=None, dissolve=False):
    """
    Converts ESRI file (File GDB table, SHP, or feature class) to either pandas dataframe
    or geopandas geodataframe (if it is spatial data)
    esri_obj_path = path to ESRI file
    include_geom = True/False on whether you want resulting table to have spatial data (only possible if
        input file is spatial)
    field_list = list of fields you want to load. No need to specify geometry field name as will be added automatically
        if you select include_geom. Optional. By default all fields load.
    index_field = if you want to choose a pre-existing field for the dataframe index. Optional.
    crs_val = crs, in geopandas CRS string format, that you want to apply to the resulting geodataframe. Optional.
    dissolve = True/False indicating if you want the resulting GDF to be dissolved to single feature.
    """

    fields = field_list # should not be necessary, but was having issues where class properties were getting changed with this formula
    if not field_list:
        fields = [f.name for f in arcpy.ListFields(esri_obj_path)]

    if include_geom:
        import geopandas as gpd
        # by convention, geopandas uses 'geometry' instead of 'SHAPE@' for geom field
        f_esrishp = 'SHAPE@'
        f_gpdshape = 'geometry'
        fields = fields + [f_esrishp]

    data_rows = []
    with arcpy.da.SearchCursor(esri_obj_path, fields) as cur:
        for row in cur:
            rowlist = [i for i in row]
            if include_geom:
                try:
                    geom_wkt = wkt.loads(rowlist[fields.index(f_esrishp)].WKT)
                except:
                    print(f"\tWARNING: not loading link {rowlist} because it has no geometry")
                    continue
                rowlist[fields.index(f_esrishp)] = geom_wkt
            out_row = rowlist
            data_rows.append(out_row)  

    if include_geom:
        fields_gpd = [f for f in fields]
        fields_gpd[fields_gpd.index(f_esrishp)] = f_gpdshape
        
        out_df = gpd.GeoDataFrame(data_rows, columns=fields_gpd, geometry=f_gpdshape)

        # only set if the input file has no CRS--this is not same thing as .to_crs(), which merely projects to a CRS
        if crs_val:
            if out_df.crs is None:
                out_df = out_df.set_crs(crs_val)

        # dissolve to single zone so that, during spatial join, points don't erroneously tag to 2 overlapping zones.
        if dissolve and out_df.shape[0] > 1: 
            out_df = out_df.dissolve() 
    else:
        out_df = pd.DataFrame(data_rows, index=index_field, columns=field_list)

    return out_df


def add_poi_wts(in_fc):

    target_sref = 'EPSG:4326' # spatial ref used by conveyal
    wt_csv = PATH_CONFIG/'poi_wts.csv'
    df_wts = read_csv(wt_csv)
    
    fc_sref = Describe(in_fc).spatialReference.name
    df = esri_to_df(in_fc, include_geom=True, crs_val=fc_sref)
    df.to_crs(target_sref, inplace=True)
    df = df[['category', 'geometry']]

    df = df.merge(df_wts, on='category', how='left').rename(columns={'dest_cnt':'count'})
    df = df[df['cat_ppa']=='service']

    return df



def convert_fc_to_shp(dest, file_to_convert, file_shp, add_date=True):

    '''
    Function to convert a feature class in a file geodatabase to a shapefile

    Parameters:
    file_to_convert - string = file path to a feature class in a file geodatabase
    file_shp        - string = file path of file geodatabase
    '''

    print(f'Importing feature class from file geodatabase {file_to_convert}...')

    if dest in ['jobs', 'schools']:
        gdf_data = gpd.read_file(str(Path(file_to_convert).parent), layer=Path(file_to_convert).stem, engine='pyogrio')
        if dest=='jobs':
            gdf_data = gdf_data[['empmonth1', 'geometry']]
        if dest=='schools':
            gdf_data['count']=1
            gdf_data = gdf_data[['count', 'geometry']]
    if dest=='services':
        gdf_data = add_poi_wts(file_to_convert)
        gdf_data = gdf_data[['count', 'geometry']]

    if gdf_data.crs != CRS:
        gdf_data = gdf_data.to_crs(CRS)

    if add_date:
        shp_name = f"{Path(file_to_convert).stem}_{date.today().strftime('%Y%m')}"
    else:
        shp_name = Path(file_to_convert).stem
    file_shp = Path(file_shp) / shp_name

    try:
        print(f'Exporting feature class {file_to_convert} to the file geodatabase {str(file_shp)}...')
        start_time = time.time()
        gdf_data.to_file(str(file_shp), driver="ESRI Shapefile", engine="pyogrio")
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")
    except Exception as e:
        print(e)




if __name__ == '__main__':

    # Jobs
    file_to_convert_jobs = r'I:\Projects\Josh\Regional Monitoring\Employment Inventory\ArcPro\EmploymentInventory_EDA.gdb\EDD_2024q3'
    file_shp_jobs = r'I:\Projects\Josh\Conveyal\conveyal_inputs\shp\jobs'

    # Schools
    file_to_convert_schools = r'I:\Projects\Josh\Handoffs\Warren\schools\GIS\Schools_2026.gdb\SACOG_Schools_2526'
    file_shp_schools = r'I:\Projects\Josh\Conveyal\conveyal_inputs\shp\schools'
    
    # Neighborhood Services (POI)
    file_to_convert_services = r'I:\Projects\Darren\PPA3_GIS\PPA3_GIS.gdb\POI_overture_2025'
    # file_to_convert_services = r'I:\Projects\Josh\POI\ArcPro\POI.gdb\POI_202607'
    file_shp_services = r'I:\Projects\Josh\Conveyal\conveyal_inputs\shp\services'


    dt_dest = {
        'jobs': [file_to_convert_jobs, file_shp_jobs]
        , 'schools': [file_to_convert_schools, file_shp_schools]
        , 'services': [file_to_convert_services, file_shp_services]
    }


    for dest, vals in dt_dest.items():
        print(f'\n\n\nProcessing {dest} layer...\n\n')
        file_to_convert = vals[0]
        file_shp        = vals[1]
        convert_fc_to_shp(dest, file_to_convert, file_shp, add_date=False)
        print('\n'*2)