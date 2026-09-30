"""
Name: utils.py
Purpose: various utility functions for bikedata2osm.py
    that are unlikely to change much, therefore are kept here


Author: Darren Conly
Last Updated: 
Updated by: 
Copyright:   (c) SACOG
Python Version: 3.x
"""

from pathlib import Path


def make_shp_compatible(in_df):
    # update field data types to make compatible with exporting to shapefile

    translator = {
        'int64': 'int32',
        'float64': 'float32',
        'bool': 'int32'
    }

    for fname, dt in in_df.dtypes.to_dict().items():
        dtname_lc = dt.name.lower()
        if dtname_lc in translator.keys():
            in_df[fname] = in_df[fname].astype(translator[dtname_lc])

def gdf_to_esri_fc(gdf, out_fc_path):
    # 3/17/2023 - stupid workaround: presently cannot use geopandas .to_file(),
    # so as workaround export to ESRI spatially-enabled dataframe then export
    # from that to ESRI feature class

    import arcpy
    import pandas as pd
    from arcgis.features import GeoAccessor, GeoSeriesAccessor
    arcpy.env.overwriteOutput = True

    try:
        arcpy.Delete_management(arcpy.env.scratchGDB) # ensures a new, fresh scratch GDB is created to avoid any weird file-not-found errors
        print("Deleted arcpy scratch GDB to ensure reliability.")
    except:
        pass

    def fixnulls(df, fname):
        ftype = df[fname].dtype.name

        nulldict = {'object':''}
        
        if nulldict.get(ftype) is not None:
            df[fname] = df[fname].fillna(nulldict[ftype])
        
        return df[fname]
    
    def fix_fname(df, fname):
        hasupper = any(c.isupper() for c in fname)
        if hasupper and fname != 'SHAPE':
            fname2 = fname.lower()
            df[fname2] = df[fname]
            df.drop(columns=[fname], inplace=True)

        return df

    for f in gdf.columns:
        gdf = fix_fname(gdf, f)

    make_shp_compatible(gdf) # ensure all data types are compatible to export to shapefile

    sedf = pd.DataFrame.spatial.from_geodataframe(gdf)  
    for f in sedf.columns:
        sedf[f] = fixnulls(sedf, f)

    # 3/7/2024 - more ESRI dumbness: if exported directly to shp, there are remaining field
    # data type incompatibilities and the is_parallel gets all zero values.
    # workaround is to export to temp feature class, then convert temp FC to SHP.
    # and reminder, this is all because in esri env, you cannot use gpd.to_file()
    out_path_obj = Path(out_fc_path)
    out_path_name = out_path_obj.stem
    temp_fc = str(Path(arcpy.env.scratchGDB).joinpath(out_path_name))
    sedf.spatial.to_featureclass(temp_fc)
    arcpy.conversion.FeatureClassToShapefile(Input_Features=temp_fc, Output_Folder=str(out_path_obj.parent))


def get_line_angle(line_geom):
    import math
    coordlist = line_geom.coords
    x_start = coordlist[0][0]
    y_start = coordlist[0][1]
    x_end   = coordlist[-1][0]
    y_end   = coordlist[-1][1]
    
    xdiff = x_end - x_start
    ydiff = y_end - y_start
    
    angle = math.degrees(math.atan2(ydiff,xdiff))
    
    return angle

def is_similar_angle(angle_1, angle_2, max_deg_diff, two_way=True):
    # tags whether a line is parallel to another line whose attributes have been tagged to it.
    # if two_way True, then will consider two lines parallel even if they point in opposite directions.
    # if two_way False, then only consider parallel if lines pointing in same direction
    
    angle_diff = abs(angle_1 - angle_2)
    
    range1 = [-max_deg_diff, max_deg_diff]
    range2 = [180-max_deg_diff, 180+max_deg_diff]

    is_dir1_parallel = angle_diff > range1[0] and angle_diff < range1[1]
    is_dir2_parallel = angle_diff > range2[0] and angle_diff < range2[1]
    
    if two_way:
        result = is_dir1_parallel or is_dir2_parallel
    else:
        result = is_dir1_parallel
        
    return int(result) # return true/false as 1/0




if __name__ == '__main__':
    pass