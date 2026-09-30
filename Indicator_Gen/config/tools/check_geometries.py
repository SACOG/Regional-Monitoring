

import sys
from pathlib import Path

from IPython.display import display

sys.path.append(str(Path(__file__).parent))
import sde
from arcgis.features import GeoAccessor
from shapely.validation import explain_validity


def validate_geometries(gdf):
    gdf['invalid_geometry_check'] = gdf['geometry'].apply(explain_validity)
    gdf['geometry'] = gdf['geometry'].make_valid()
    gdf['valid_geometry_status'] = gdf['geometry'].apply(explain_validity)
    return gdf


def send_gdf_to_filegdb(gdf, file_fc):
    '''
    Sends data frame with geometry field to file geodatabase
    '''
    print('Converting to point layer and EXPORTing to the following gdb: ', file_fc)
    # if arcpy.Exists(file_fc):
    #     arcpy.Delete_management(file_fc)
    if gdf.crs != 2226:
        gdf = gdf.to_crs('EPSG:2226')
    sdf = GeoAccessor.from_geodataframe(gdf, column_name='geometry')
    sdf.spatial.to_featureclass(location=file_fc)



FC_FIXED_INVALIDS = r'I:\Projects\Josh\Regional Monitoring\Employment Inventory\ArcPro\EmploymentInventory_EDA.gdb\Master_Parcel_Region_fixed_invalids'
FC_VALIDATED = r'I:\Projects\Josh\Regional Monitoring\Employment Inventory\ArcPro\EmploymentInventory_EDA.gdb\Master_Parcel_Region_validated'



if __name__=='__main__':

    # gdf_og = gpd.read_file(GDB, layer=FC_IN, engine="pyogrio")
    gdf_og = sde.sqlqry_to_gdf(sde.sql_parcel)
    display(gdf_og)

    gdf_valid = validate_geometries(gdf_og)
    gdf_fixed_invalids = gdf_valid[gdf_valid['invalid_geometry_check']!='Valid Geometry']

    # send_gdf_to_filegdb(gdf_fixed_invalids, FC_FIXED_INVALIDS)
    # send_gdf_to_filegdb(gdf_valid, FC_VALIDATED)




