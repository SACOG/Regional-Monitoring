"""
Name: merge_new_lines.py
Purpose: merge/"stitch" in a shp of new lines (e.g., for new developments) into an
    OSM line shapefile. Note that the new lines file must have an 'lts' field.

    Idea: ideally, could have this integrated as function into pbf2shp.py, ie., as an optional
    method/step: after converting to SHP with 'lts' field, weave in SHP of center lines


Author: Darren Conly
Last Updated:
Updated by:
Copyright:   (c) SACOG
Python Version: 3.x
"""
import datetime as dt
from pathlib import Path
from time import perf_counter

import arcpy
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326) # ensure everything's in WGS84

try:
    arcpy.Delete_management(arcpy.env.scratchGDB) # ensures a new, fresh scratch GDB is created to avoid any weird file-not-found errors
    print("Deleted arcpy scratch GDB to ensure reliability.")
except:
    pass

def check_lts_field(osm_shp, newlines_fc, fname_lts='lts'):
    osm_fields = [f.name for f in arcpy.ListFields(osm_shp)]
    newline_fields = [f.name for f in arcpy.ListFields(newlines_fc)]

    lts_in_newlines = fname_lts in newline_fields

    if not lts_in_newlines:
        msg = f"ERROR: level-of-traffic-stress field {fname_lts} not among fields in {newlines_fc}"
        raise Exception(msg)

def add_new_lines(osm_shp, fc_newlines, split_newlines=True, snap_newlines=True):
    # weave in fc_newlines into osm_shp. Set split_newlines = False if the input newlines file is already split
    # at intersections--though recommend setting to True

    check_lts_field(osm_shp, fc_newlines)
    fl_osm_links = 'fl_links'
    arcpy.MakeFeatureLayer_management(osm_shp, fl_osm_links)

    fc_pts_temp = str(Path(arcpy.env.scratchGDB).joinpath("PTS_TEMP"))

    # step 1: split new lines at intersections
    name_newlines_fc = Path(fc_newlines).stem
    fc_newlines_split = str(Path(arcpy.env.scratchGDB).joinpath(name_newlines_fc))
    if split_newlines:
        print("splitting new lines at intersections...")
        st = perf_counter()

        arcpy.analysis.PairwiseIntersect(in_features=fc_newlines, out_feature_class=fc_pts_temp, output_type='POINT')
        arcpy.management.SplitLineAtPoint(in_features=fc_newlines, point_features=fc_pts_temp, 
                                  out_feature_class=fc_newlines_split, search_radius="10 Feet")
        
        elapsed = round((perf_counter() - st) / 60, 1)
        print(f"splitting of new lines completed in {elapsed} mins.")
        
    else:
        arcpy.management.CopyFeatures(in_features=fc_newlines, out_feature_class=fc_newlines_split)

    # step 2: "snap" splitted new lines to nearby osm links
    if snap_newlines:
        st = perf_counter()

        print("snapping new line endpoints to nearby OSM links...")
        snap_env = [fl_osm_links, "EDGE", "25 Feet"]
        arcpy.edit.Snap(in_features=fc_newlines_split, snap_environment=[snap_env])

        elapsed = round((perf_counter() - st) / 60, 1)
        print(f"snapping of new lines to OSM completed in {elapsed} mins.")

    # step 3: split OSM lines where they intersect with new lines
    print("pairwise intersecting OSM lines at intersections with new lines...")
    fc_osm_split = str(Path(arcpy.env.scratchGDB).joinpath("TEMP_osm_links_split"))

    arcpy.Delete_management(fc_pts_temp)
    arcpy.analysis.PairwiseIntersect(in_features=[fl_osm_links, fc_newlines_split], 
                                     out_feature_class=fc_pts_temp, output_type='POINT')
    
    print("doing final splitting...")
    arcpy.management.SplitLineAtPoint(in_features=fl_osm_links, point_features=fc_pts_temp, 
                                  out_feature_class=fc_osm_split, search_radius='10 Feet')
    
    # step 4: merge snapped and split new lines with split osm lines
    print("merging new lines with OSM lines...")
    fp_osm = Path(osm_shp)
    merged_output_fc = str(fp_osm.parent.joinpath(f"{fp_osm.stem}_NewLinesMerge.shp"))
    osm_fields = [f.name for f in arcpy.ListFields(osm_shp)]
    newline_fields = [f.name for f in arcpy.ListFields(fc_newlines)]    
    fields_to_exclude = [f for f in newline_fields if f not in osm_fields]
    arcpy.management.Merge([fc_osm_split, fc_newlines_split], output=merged_output_fc)

    for f in fields_to_exclude:
        arcpy.DeleteField_management(in_table=merged_output_fc, drop_field=f)

    print(f"Success! Output in {merged_output_fc}")
    print("WARNING: to prohibit cars on bike path links, they must have highway=cycleway.")

                                

if __name__ == '__main__':
    # for dev testing, comment out if not using
    # osm_lineshp_in = r"I:\Projects\Darren\PEP\PEP_GIS\SHP\fromOSM\sacog_20230809_filtered20230818_1118.shp"
    # lines_to_merge = r'I:\Projects\Darren\PEP\PEP_GIS\PEP_GIS.gdb\NewDevLines_split_wCommtdProjects' # NewDevLines_split 
    # split_new_lines = False # if True, will split lines_to_merge at intersections--WARNING: time-consuming
    # snap_new_lines = True # if True, will snap lines_to_merge end points to OSM links--WARNING: time-consuming

    # normal inputs
    osm_lineshp_in = input("Enter path to line SHP derived from OSM (with LTS field already calculated): ").strip("\"") # r'I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\3__filtered_w_bikeways\pbf2shp\Six-County_Sacramento_Region_202609_filtered20260911_1449\Six-County_Sacramento_Region_202609_filtered20260911_1449.shp', r"I:\Projects\Darren\PEP\PEP_GIS\SHP\fromOSM\sacog_20230809_filtered20230816_1337.shp"
    lines_to_merge = input("Enter path to SHP of non-OSM lines you want to merge in (with LTS calculated): ").strip("\"") # NewDevLines_split
    split_new_lines = bool(input("Do you want to split non-OSM lines before merging (leave blank if no): ")) # if True, will split lines_to_merge at intersections--WARNING: time-consuming
    snap_new_lines = True # if True, will snap lines_to_merge end points to OSM links--WARNING: time-consuming

    add_new_lines(osm_shp=osm_lineshp_in, fc_newlines=lines_to_merge, split_newlines=split_new_lines, snap_newlines=snap_new_lines)
    
