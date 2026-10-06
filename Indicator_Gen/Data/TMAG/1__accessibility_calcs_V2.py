


'''
This script calculates a weighted travel accessibility score by geometry (weighted by number of workers or population)
Import vector feature class from file gdb (points, lines, or polygons), import raster tif file (for weights and for accessibility scores)
Aligns imported layers with same CRS, small buffer, etc...
Rolls up raster data to each geometry in vector layer to estimate an accessibility score by geography (accessibility by driving, transit, biking, and walking)
Exports results to a file gdb feature class
'''



# Workspace ------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import sys
from time import perf_counter as perf # what is this
import time
import pandas as pd
from datetime import datetime as dt
import arcpy
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from tqdm import tqdm
from arcgis.features import GeoAccessor
from IPython.display import display
from osgeo import gdal
sys.path.append(str(Path(__file__).parent / 'config'))
import parameters as params
import utils as ut
import yaml
yaml_file = Path(__file__).parent / 'config' / 'config_regavgs.yaml'
with open(yaml_file, 'r') as y:
    pathconfigs = yaml.load(y, Loader=yaml.FullLoader)
    acc_cfg = pathconfigs['access_data']
gdal.SetConfigOption("GDAL_MEM_ENABLE_OPEN", "YES")

    
def set_fc(tif_main, fc_main, search_dist):
    # load tif data
    with rasterio.open(tif_main) as tifdata:
        tif_epsg = tifdata.crs.to_epsg()
        crs_linunits = tifdata.crs.linear_units # placeholder in case you ever want to know what units the CRS uses.
        crs_to_use = f"EPSG:{tif_epsg}"

        # create buffered line object around project line (need to load in native CRS then convert to match TIF CRS
        fc_epsg = f"EPSG:{arcpy.Describe(fc_main).spatialReference.factoryCode}"
        gdf_fc = ut.esri_to_df(esri_obj_path=fc_main, include_geom=True, field_list=None, index_field=None, crs_val=fc_epsg, dissolve=False)
        gdf_fc = gdf_fc.to_crs(crs_to_use)

        if search_dist > 0:
            gdf_fc['geometry'] = gdf_fc['geometry'].buffer(search_dist) # distance in meters if EPSG 3857 (web mercator)

        return gdf_fc
    

def get_raster_pts_near_line(tif_main, gdf_fc, idx, valname):

    gdf_fc_slice = gdf_fc[idx:idx+1]
    mask_geom = gdf_fc_slice.geometry[ii]

    with rasterio.open(tif_main) as tifdata:
        tif_epsg = tifdata.crs.to_epsg()
        # crs_linunits = tifdata.crs.linear_units # placeholder in case you ever want to know what units the CRS uses.
        crs_to_use = f"EPSG:{tif_epsg}"

        # use buffer to mask TIF values.
        vals_masked, valmasked_transform = mask(tifdata, shapes=[mask_geom], all_touched=True, crop=True, pad=True, pad_width=0.5)
        vals_array = vals_masked[0]

    # make vector point gdf from the pixels that are near the line. Will need to further trim to go from
    # rectangle of points to just points that are right along the line.
    # helpful site = https://gis.stackexchange.com/questions/388047/get-coordinates-of-all-pixels-in-a-raster-with-rasterio
    row_range = np.arange(vals_array.shape[0])
    col_range = np.arange(vals_array.shape[1])

    # NOTE 4/4/2025 this is a perfromance bottleneck. Over 660,000 iterations
    # bounding boxes won't really help for commtypes because they cover whole region,
    # but *could* improve speed for individual projects?
    # import pdb; pdb.set_trace()
    coord_arr = []
    for r in row_range:
        for c in col_range:
            x, y = rasterio.transform.xy(valmasked_transform, r, c)
            val = vals_array[r][c]
            coord_arr.append({'cellid': f"{r}_{c}", 'x': x, 'y': y, valname: val})

    df_fc_slice = pd.DataFrame(coord_arr)
    gdf_fc_slice = gpd.GeoDataFrame(df_fc_slice, geometry=gpd.points_from_xy(df_fc_slice.x, df_fc_slice.y), crs=crs_to_use)

    return gdf_fc_slice


def get_acc_data(gdf_fc, tif_main, destination, idx):
    '''Calculate average accessibility to selected destination types for all
    polygons that either intersect the project line or are within a community type polygon.
    Average accessibility is weighted by each polygon's population.'''
    
    # load tif of population used for weighting
    wt = Path(tif_main).stem
    gdf_wt = get_raster_pts_near_line(tif_main, gdf_fc, idx, valname=wt)

    out_dict = {}
    acclayer_dict = acc_cfg['acc_lyrs']
    acclayers_dir = Path(acc_cfg['tifdir'])
    accdata_dest = acclayer_dict[destination]
    for mode in accdata_dest.keys():
        i_dict_key = f"{mode}_{destination}"
        acc_tif = accdata_dest[mode] # name of accessibility results tif file
        if acc_tif:
            acc_tif_path = acclayers_dir.joinpath(acc_tif)
            gdf_acc = get_raster_pts_near_line(acc_tif_path, gdf_fc, idx, valname=i_dict_key)
            gdfjn = gdf_acc.merge(gdf_wt, on='cellid')

            if gdfjn[wt].sum() == 0: # if no people, get unweighted avg access
                wtd_avg = gdfjn[i_dict_key].mean()
            else:
                wtd_avg = (gdfjn[i_dict_key]*gdfjn[wt]).sum() / gdfjn[wt].sum()

            out_dict[i_dict_key] = float(wtd_avg) # need to convert to python native type, not numpy dtype
        else:
            continue # if no tif of acc data for mode-dest combo, then skip computation of accessibility

        df_out = pd.DataFrame(out_dict, index=[idx])
            
    return df_out


def export_access(fc_name, wgt, destination):

    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")

    # # Feature class to file gdb
    # fc_name_out = f'{fc_name}__access_{wgt}_{destination}'
    # file_fc_out = Path(FILE_GDB) / fc_name_out
    # print(f'Exporting feature class {fc_name_out} to the file geodatabase {FILE_GDB}...\n')
    # sdf_data = GeoAccessor.from_geodataframe(gdf_fc, column_name='geometry')
    # sdf_data.spatial.to_featureclass(location=file_fc_out)
    # print(f'\nSuccessfully EXPORTed to the following location: {FILE_GDB}\n\n')

    path_out = Path(r'I:\Projects\Josh\Conveyal\accessibility_results')

    # csv
    df_fc = gdf_fc.drop('geometry', axis=1)
    wb_name = f'{fc_name}__access_{wgt}_{destination}_{timestamp}.csv'
    file_out = path_out / wb_name
    print(f'Exporting {wb_name} to csv here {path_out}...\n\n')
    df_fc.to_csv(file_out, index=False)

    # excel
    df_notes = pd.DataFrame([acc_cfg['acc_lyrs'][destination]]).T.reset_index().dropna()
    df_notes.columns=['Mode', 'tif file']
    df_notes[['Percentile', 'Travel Time Assumptions (Min)']] = df_notes['tif file'].str.extract(r'(P\d+)_(C\d+)')
    df_notes['Travel Time Assumptions (Min)'] = df_notes['Travel Time Assumptions (Min)'].str.replace('C', '').astype(int)
    df_notes = df_notes.drop('tif file', axis=1)
    df_fc = gdf_fc.drop('geometry', axis=1)
    wb_name = f'{fc_name}__access_{wgt}_{destination}_{timestamp}.xlsx'
    file_out = path_out / wb_name
    print(f'Exporting {wb_name} to excel here {path_out}...\n\n')
    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_notes.to_excel(writer, index=False, sheet_name='Assumptions')
        df_fc   .to_excel(writer, index=False, sheet_name=destination  )




# Main -------------------------------------------------------------------------------------------------------------------------------------


EXPORT=True


FILE_GDB = r'I:\Projects\Josh\Conveyal\ArcPro\Conveyal_Layers.gdb'




if __name__ == '__main__':

    start_time = time.time()

    arcpy.env.workspace = r'I:\Projects\Josh\Conveyal\ArcPro\Conveyal_Layers.gdb'

    fc_name = 'GISOWNER_PlanningArea' # GISOWNER_PlanningArea, GISOWNER_CityCounty, Community_Type_2024_dissolve
    fc_main = FILE_GDB + '\\' + fc_name
    str_project_type = 'AreaAvg'
    destination = 'nonwork'
    wgt = 'pop' # pop, asian, black, hispanic, white, workers

    tif_main = Path(acc_cfg['tifdir']).joinpath(acc_cfg['wts'][wgt]) # r"I:\Projects\Darren\PPA3_GIS\AccessibilityAnalyses\tif\workers2020.tif"


    if str_project_type == params.ptype_area_agg: # do i need this

        search_dist = 0 if str_project_type == params.ptype_area_agg else params.acc_search_dist # do i need this
        

        print('\n\nSetting feature class...\n\n')
        gdf_fc = set_fc(tif_main, fc_main, search_dist=100) # search dist is 100, why


        list_df_acc = []
        total_iterations = gdf_fc.shape[0]
        ii = 0

        print(f'Calculating accessibility metrics by geometry ({total_iterations} total geometries)...\n\n')
        
        with tqdm(total=total_iterations, desc='Processing', position=0) as pbar:
            while ii < total_iterations:
                try:
                    df_acc = get_acc_data(gdf_fc, tif_main, destination, ii)
                    list_df_acc.append(df_acc)
                except Exception as e:
                    tqdm.write(f' Error occured on index {ii} -> {e}')
                ii+=1
                pbar.update(1)

        df_out = pd.concat(list_df_acc)

        gdf_fc = gdf_fc.join(df_out, how='left')

        cols = list(gdf_fc.columns)
        cols.remove('geometry')
        gdf_fc = gdf_fc[cols + ['geometry']]

        print('\n'*2)
        display(gdf_fc)
        print('\n'*2)

        if EXPORT:
            export_access(fc_name, wgt, destination)


        ## Calculate time amounted while requesting data
        print('\nFinished!!')
        print(f'Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---\n')




