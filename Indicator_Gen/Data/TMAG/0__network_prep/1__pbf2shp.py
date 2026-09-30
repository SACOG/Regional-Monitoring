"""
Name: pbf2shp_multi_call.py
Purpose: Convert PBF of OSM data into line SHP, filtering way types appropriate for accessibility analysis.
    The resulting SHP will be manipulated/edited as needed in GIS software, then can be reconverted to PBF
    for final upload to Conveyal.

    "Multi call" enables more complex "and" logic in osmium filters. E.g., to get a final SHP with
    all highway != path, but then want to add in highway=path where bicycle=designated

    References:
    https://osmcode.org/osmium-tool/manual.html


Author: Darren Conly
Last Updated: Sept 2026
Updated by: Josh
Copyright:   (c) SACOG
Python Version: 3.x
"""
import datetime as dt
sufx = str(dt.datetime.now().strftime('%Y%m%d_%H%M'))

from pathlib import Path
import os
import subprocess
import yaml

with open(Path(__file__).parent.joinpath('config.yml'), 'r') as f:
    cfg = yaml.safe_load(f)

import arcpy
arcpy.env.overwriteOutput = True
try:
    arcpy.Delete_management(arcpy.env.scratchFolder) # ensures a new, fresh scratch GDB is created to avoid any weird file-not-found errors
    print('Deleted arcpy scratch GDB to ensure reliability.')
except:
    pass


def add_default_lts(in_shp):
    print("setting baseline LTS, assuming no on-street bike-specific infrastructure...")
    
    # placeholder function: after downloading/exporting to SHP, use this to hard-set a
    # default lts value that will be updated via modification in conveyal interface. 
    # will set default LTS values based on lts_config.csv

    # {road_type: lts}
    # max LTS value is 4 (highest traffic stress)
    default_lts = {'residential': 1, 'living_street': 1,  'cycleway': 1, 'path': 1} # assuming only have paths where bicycle=designated
    max_lts_val = 4

    f_lts = 'lts'
    f_hwy = 'highway'
    in_shp = str(in_shp) # arcpy does not like path objects. So convert to string.
    arcpy.management.AddField(in_table=in_shp, field_name=f_lts, field_type="SHORT")

    curfields = [f_hwy, f_lts]
    with arcpy.da.UpdateCursor(in_shp, curfields) as cur:
        for row in cur:
            hwyval = row[curfields.index(f_hwy)]
            if hwyval in default_lts.keys():
                ltsval = default_lts[hwyval]
            else:
                ltsval = max_lts_val
            row[curfields.index(f_lts)] = ltsval
            cur.updateRow(row)



def pbf2shp(in_pbf, shp_output_dir, osmium_filter_str, pbf_out_dir=None, delete_raw_pbf=False, make_shp=True, output_suffix=None):

    fp_inpbf = Path(in_pbf)
    name_inpbf = Path(fp_inpbf.stem).stem # need to get stem twice because pbfs download as <name>.osm.pbf
    fp_filteredpbf = fp_inpbf.parent.joinpath(f"{name_inpbf}_bw.osm.pbf")
    if pbf_out_dir:
        fp_filteredpbf = Path(pbf_out_dir).joinpath(fp_filteredpbf.name)

    # NOTE - osmium filter expressions are treated as OR expressions. E.g., "w/bicycle=designated w/surface!=dirt"
    # means get links where bicycle=designated OR surface != dirt

    default_filter = "w/public_transport=platform w/railway=platform w/park_ride r/type=restriction"
    final_filter = f"{osmium_filter_str} {default_filter}"

    cmd_filterpbf = f"""osmium tags-filter {fp_inpbf} {final_filter} -o {fp_filteredpbf} --overwrite"""

    ogr_env = os.environ.copy()
    ogr_env_folders = cfg['ogr_paths']
    ogr_env_folders.append(ogr_env['PATH'])
    ogr_env['PATH'] = os.pathsep.join(ogr_env_folders)

    output_dict = {}
    subprocess.run(cmd_filterpbf, shell=True, env=ogr_env, check=True)
    output_dict['pbf_out'] = str(fp_filteredpbf)
    
    if shp_output_dir:
        print(f"Exporting to SHP...")
        if output_suffix:
            output_shp = (
                f"{Path(fp_filteredpbf.stem).stem}"
                f"_{output_suffix}_{sufx}.shp"
            )
        else:
            output_shp = f"{Path(fp_filteredpbf.stem).stem}_{sufx}.shp"
        out_shp_path = Path(shp_output_dir).joinpath(output_shp)
        cmd_pbf2shp = f"ogr2ogr {out_shp_path} {fp_filteredpbf} lines -oo CONFIG_FILE={cfg['ogr_config']}"
        subprocess.run(cmd_pbf2shp, shell=True, env=ogr_env, check=True)


        add_default_lts(out_shp_path)

        # drop OSM tags field, which could confuse LTS computation
        arcpy.DeleteField_management(in_table=str(out_shp_path), drop_field='other_tags')
        output_dict['shp_out'] = str(out_shp_path)

        print(f"Success: resulting SHP is {out_shp_path}")

    if delete_raw_pbf:
        fp_inpbf.unlink()

    return output_dict




if __name__ == '__main__':

    pbf = r"I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\2__filtered\Six-County_Sacramento_Region_202609_filtered.osm.pbf"
    shp_dir = r'I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\2__filtered\pbf2shp'


    # pbf = input("Enter path to input PBF file: ").strip("\"")
    # shp_dir = input("Enter path to input SHP output folder: ").strip("\"")

    # =================BEGIN SCRIPT========================

    # recommended filtering logic:
    # generate SHP that reflects filter to retrieve all highways!=planned,proposed,construction,busway,path. This will return lots of dirt paths you don't want,
    # and exclude all paths
    print("creating SHP of just hwys without paths...")
    filt_hwy = 'w/highway!=planned,proposed,construction,busway,path'
    results_hwys = pbf2shp(in_pbf=pbf, shp_output_dir=arcpy.env.scratchFolder, osmium_filter_str=filt_hwy, make_shp=True, output_suffix='hwys')
    shp_hwys = results_hwys['shp_out']
    
    # generate PBF of only paths
    print("creating temp PBF of just paths...")
    filt_paths = 'w/highway=path'
    result_filtpaths = pbf2shp(in_pbf=pbf, shp_output_dir=None, pbf_out_dir=arcpy.env.scratchFolder, osmium_filter_str=filt_paths, make_shp=False)
    pbf_paths = result_filtpaths['pbf_out']

    # starting with PBF of only paths, generate SHP only of paths where bicycle=designated
    print("creating temp SHP of just *bike* paths...")
    filt_bikepath = 'w/bicycle=designated,yes'
    
    results_bikepaths = pbf2shp(in_pbf=pbf_paths, shp_output_dir=arcpy.env.scratchFolder, osmium_filter_str=filt_bikepath, make_shp=True, output_suffix='bikepaths')
    
    # merge all-hwys-no-paths SHP with only-bicycle-paths SHP
    print("merging SHPs of hwys+bike paths...")
    shp_bikepaths = results_bikepaths['shp_out']
    output_shp_name = f"{Path(Path(pbf).stem).stem}{sufx}.shp"
    out_shp_path = Path(shp_dir).joinpath(output_shp_name)
    arcpy.Merge_management(inputs=[shp_hwys, shp_bikepaths], output=str(out_shp_path))
    print(f"Success! Base OSM Net for Conveyal in {out_shp_path}")
   