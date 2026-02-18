

'''
This script preps the Quarterly Hourly Speeds Profile data provided by Replica for the travel accessibility analysis conducted in Conveyal.
Data at the county level can be manually downloaded here:  https://studio.replicahq.com/data/downloads
Conveyal requires simple shapefiles (speed needs to be in MPH, only necessary columns, remove all very short road segments (less than 1 foot long), etc...)

'''


EXPORT=False


# Workspace -------------------------------------------------------------------------------------------------------------------------------------------

from pathlib import Path
import os
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from scipy.stats import hmean
from IPython.display import display


PATH_REP = Path(r'I:\Projects\Josh\Geospatial Data\Replica\qtr-hourly-speeds_2024')
PATH_CON = Path(r'I:\Projects\Josh\Geospatial Data\Conveyal')


def clean_replica_for_conveyal(gdf):

    crs_ft = 'EPSG:2226'
    gdf = gdf.to_crs(crs_ft)

    for index, row in gdf.iterrows():
        if row.geometry.geom_type == 'LineString':
            line_length_ft = row.geometry.length
            gdf.loc[index, 'length_ft'] = line_length_ft
        else: pass

    gdf = gdf[gdf['length_ft'] > 1]
    gdf = gdf.drop('length_ft', axis=1)
    gdf = gdf.reset_index(drop=True)

    crs_orig = 'EPSG:4326'
    gdf = gdf.to_crs(crs_orig)

    return gdf




# Main ------------------------------------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':

    list_folders = [folder for folder in PATH_REP.iterdir() if folder.is_dir()]
    list_gdf = []

    for folder in tqdm(list_folders):

        shapefile = [shapefile for shapefile in folder.iterdir() if '.shp' in str(shapefile)][0]
        gdf = gpd.read_file(shapefile)
        cols_to_average = ['wkdy_0700', 'wkdy_0715', 'wkdy_0730', 'wkdy_0745', 'wkdy_0800', 'wkdy_0815', 'wkdy_0830', 'wkdy_0845', 'wkdy_0900']
        gdf['7_9am_havg'] = hmean(gdf[cols_to_average], axis=1)
        gdf = gdf[['7_9am_havg', 'geometry']]

        gdf = clean_replica_for_conveyal(gdf)
        list_gdf.append(gdf)

        if EXPORT:
            PATH_CON_new = PATH_CON / f'{shapefile.stem}__clean'
            os.makedirs(PATH_CON_new, exist_ok=True)
            shapefile_out = PATH_CON_new / f'{shapefile.stem}__clean.shp'
            gdf.to_file(shapefile_out)


    gdf = pd.concat(list_gdf)
    display(gdf.head(3))

    if EXPORT:
        PATH_CON_new = PATH_CON / 'Replica_11__clean'
        os.makedirs(PATH_CON_new, exist_ok=True)
        shapefile_out = PATH_CON_new / 'Replica_11__clean.shp'
        gdf.to_file(shapefile_out)



