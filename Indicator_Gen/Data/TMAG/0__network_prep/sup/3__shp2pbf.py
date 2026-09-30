"""
Name: shp2pbf.py
Purpose: convert shapefile or ESRI feature class to PBF file for uploading to conveyal


Author: Darren Conly
Last Updated: 
Updated by: 
Copyright:   (c) SACOG
Python Version: 3.x
"""
from pathlib import Path
import os
import subprocess

import arcpy
arcpy.env.overwriteOutput = True


def is_fc(in_path):
    fsuffix = Path(in_path).suffix
    is_directory = Path(in_path).is_dir()
    if fsuffix == '' and not is_directory:
        result = True
    else:
        result = False
    
    return result

def shp2pbf(in_fc_or_shp, pbf_dir, ogr_env_folder):
    fc_file = is_fc(in_fc_or_shp)
    fc_gdb = Path(in_fc_or_shp).parent
    fc_name = Path(in_fc_or_shp).stem

    # get path to shapefile to be converted; if it's a feature class, then convert to a shapefile
    if fc_file:
        print("converting feature class to SHP...")
        shp_name = f"{Path(in_fc_or_shp).stem}.shp"
        shp_dir = arcpy.env.scratchFolder
        shp_path = Path(shp_dir).joinpath(shp_name)

        arcpy.conversion.FeatureClassToFeatureClass(in_features=in_fc_or_shp, out_path=shp_dir, out_name=shp_name)

    else:
        shp_path = in_fc_or_shp

    pbf_dir = Path(pbf_dir)
    osm_path = f"{pbf_dir.joinpath(fc_name)}.osm"
    pbf_path = f"{pbf_dir.joinpath(fc_name)}.pbf"

    

    cmd_shp2osm = f"ogr2osm {shp_path} -o {osm_path} -f"
    cmd_osm2pbf = f"osmconvert64 {osm_path} -o={pbf_path}" # -f flag forces overwrite if file exists

    
    # Need to switch to correct environment with ogr tools
    ogr_env = os.environ.copy()
    ogr_env['PATH'] = os.pathsep.join([ogr_env_folder, ogr_env['PATH']])

    
    print("converting SHP to PBF...")
    try:
        subprocess.run(cmd_shp2osm, shell=True, env=ogr_env)
    except ImportError as e:
        msg = f"""{e} - To fix try:
            1. Creating new environment
            2. Run conda install -c conda-forge gdal
            3. Search how to install ogr2osm (probably pip)
            4. Update ogr_envfolder to reflect new env you created"""
        raise Exception(ogr_env_folder)
    
    subprocess.run(cmd_osm2pbf, shell=True, env=ogr_env)

    # Path(osm_path).unlink # delete OSM file, is large and no longer needed--8/22/2023 - for some reason unlink() isn't working. Using os.remove() instead
    # os.remove(osm_path)

    print(f"Success! Resulting PBF is {pbf_path}")



if __name__ == '__main__':

    fc_path_in = r"I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\3__filtered_w_bikeways\pbf2shp\Six-County_Sacramento_Region_202609_filtered20260911_1449\Six-County_Sacramento_Region_202609_filtered20260911_1449.shp"
    pbf_folder = r'I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\3__filtered_w_bikeways'

    # fc_path_in = input("Enter path to input feature class or shapefile: ").strip("\"")
    # pbf_folder = input("Enter path to PBF output folder: ").strip("\"")

    # folder for environment containing ogr tools like ogr2ogr, ogr2osm, etc.
    ogr_envfolder = r'C:\Users\jfontes\AppData\Local\ESRI\conda\envs\conveyal_gdal\Scripts'  # r'C:\Users\dconly\AppData\Local\ESRI\conda\envs\ogr-tools\Scripts'

    shp2pbf(fc_path_in, pbf_folder, ogr_envfolder)