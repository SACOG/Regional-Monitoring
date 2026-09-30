"""
Name: bikedata2osm_gpd.py
Purpose: Conflate data from a line file of bikeways (source) onto OSM links (target). USING GEOPANDAS

    Returns SHP of OSM links that have been clipped to match bikeway extents,
    and containing bikeway data. Also computes LTS for each link.


Author: Darren Conly
Last Updated: Sept 2026
Updated by: Josh
Copyright:   (c) SACOG
Python Version: 3.x
"""
# import os
from pathlib import Path
import datetime as dt

import pandas as pd
import geopandas as gpd

import utils

def add_lts(in_df, f_bike_class, f_osm_hwy, fname_lts='lts'):
    # computes LTS for each road link based on type of bike facility and OSM highway type

    def compute_lts_row(row, config_df, f_bikeclass, f_hwy):
        bike_class = row[f_bikeclass]
        hwy_type = row[f_hwy]
        if hwy_type not in config_df.columns: hwy_type = 'other'

        config_bkclss = 'bike_class'
        
        if hwy_type and bike_class in config_df[config_bkclss].values:
            lts_val = config_df.loc[config_df[config_bkclss] == bike_class][hwy_type].values[0]
        elif bike_class in config_df[config_bkclss].values:
            # LTS values to use if highway tag null or was a filtered out type
            lts_val = config_df.loc[config_df[config_bkclss] == bike_class]['other'].values[0]
        else:
            lts_val = 4
        
        return lts_val # must be integer value for Conveyal

    lts_config_csv = Path(__file__).parent.joinpath("lts_config.csv")
    df_config = pd.read_csv(lts_config_csv)

    in_df[fname_lts] = in_df.apply(lambda row: compute_lts_row(row, df_config, f_bike_class, f_osm_hwy), axis=1)
    
def apply_lts_override(in_gdf, f_lts, f_jnid):
    # some streets defy the logic in the lts_config CSV (e.g., 2nd Ave in Sac tagged as LTS4, but really is more like LTS2)
    # this func reads a CSV of specific OSM links that require a link-specific override LTS value.

    print("Applying override LTS values for specific locations...")

    # load override CSV
    override_csv = Path(__file__).parent.joinpath("lts_override.csv")
    df_override = pd.read_csv(override_csv)
    jn_sufx = '_override'

    # replace LTS values with override LTS value, if osm_id is in the override table.
    f_id_temp = f"{f_jnid}_float"
    in_gdf[f_id_temp] = in_gdf[f_jnid].astype(float)
    dfj = in_gdf.merge(df_override, how='left', left_on=f_id_temp, right_on=f_jnid, suffixes=('',jn_sufx))
    dfj.loc[~dfj[f"{f_lts}{jn_sufx}"].isnull(), f_lts] = dfj[f"{f_lts}{jn_sufx}"]
    dfj = dfj[[*in_gdf.columns]]

    # flag for user which override links did not appear in the base layer (could mean the override table IDs are out of date)
    revjn = df_override.merge(in_gdf, how='left', left_on=f_jnid, right_on=f_id_temp, suffixes=(jn_sufx,''))
    missing = revjn.loc[revjn[f_lts].isnull()] # if osm ID from the override table not found in conflated network, warn user.

    if missing.shape[0] > 0:
        print(f"""The following {missing.shape[0]} override IDs do not exist in the output network. 
              You may need to update the list of IDs in {override_csv}\n""")
        print(missing)

        print("""HOWEVER, these unmatched links could also mean that your source layer did not overlap with any
              of the links specified to have override values.""")

    del dfj[f_id_temp]
    return dfj

def simple_conflation(target_line_file, source_line_file, output_file, target_fields, source_fields,
            search_dist_ft=50, local_crs=2226, lts_field=None, fld_bikeclass=None, 
            hwytyps_to_exclude=None):

    """Clips target_line_file to extents of source_line_file and conflates source_line_file's 
        attributes onto clipped target_line_file.

    Args:
        target_line_file (gis line file): line file you want source data conflated to
        source_line_file (gis line file): line file whose attributes you want to conflate to target_line_file
        output_file (_type_): name of output line file
        target_fields (_type_): fields you want to keep from target_line_file
        source_fields (_type_): fields you want to keep from source_line_file
        search_dist_ft (int, optional): Distance, in feet, of how far away to search for target lines
                                        to conflate source line data onto. Defaults to 50 feet.
        local_crs (int, optional): _description_. Spatial reference system to use. Ideally set to feet. Defaults to 2226.
        lts_field: field, if provided, indicating the bike level of traffic stress for source links. Will be computed if not provided.
        hwytyps_to_exclude: OSM highway types to exclude from conflation. If None, nothing will be excluded.
    """

    # make sure all geodataframes have geometry field
    f_geom = 'geometry'
    if not fld_bikeclass and not lts_field:
        raise Exception(f"You must specify a level of traffic stress (LTS) and/or bike class (1-4) field from your bikeway source layer.")

    if fld_bikeclass: source_fields.append(fld_bikeclass)
    for flist in [target_fields, source_fields]:
        if f_geom not in flist:
            flist.append(f_geom)

    f_angle_src = 'angle_src'
    f_angle_tar = 'angle_tar'
    f_par_flag = 'is_parallel'

    fld_hwytyp = 'highway'

    f_lts_standardized = 'lts' # will want to rename lts_field to this no matter what
    
    # prep source line data
    print("loading link files into geodataframes...")
    gdf_source = gpd.read_file(source_line_file, engine='pyogrio')[source_fields].to_crs(local_crs) # load source file

    # only include officially-recognized bike classes, if bike class field specified
    if fld_bikeclass:
        gdf_source = gdf_source.loc[gdf_source[fld_bikeclass].isin([1, 2, 3, 4])] 

    gdf_source = gdf_source.explode(index_parts=True) # ensure no multipart lines
    # gdf_source[f_angle_src] = gdf_source.geometry.apply(lambda g: utils.get_line_angle(g)) # get angle for each line
    gdf_source[f_angle_src] = [utils.get_line_angle(g) for g in gdf_source.geometry]

    # make version of source line file that is flat-capped polygon buffers
    gdf_source_buff = gdf_source
    gdf_source_buff[f_geom] = gdf_source_buff.geometry.buffer(search_dist_ft, cap_style=2)
    gdf_source_buff = gdf_source_buff.reset_index().drop(columns=['level_0', 'level_1'])

    # load target line file to gdf
    gdf_target = gpd.read_file(target_line_file, engine='pyogrio')[target_fields].to_crs(local_crs)

    # filter out unwanted target links
    if hwytyps_to_exclude:
        gdf_target = gdf_target.loc[~gdf_target[fld_hwytyp].isin(hwytyps_to_exclude)]

    # intersect target with source and pull source's attributes onto target segments
    print(f"clipping target links to source link extents and tagging source link data to target links...")
    gdf_target_ix = gpd.overlay(gdf_target, gdf_source_buff, how="intersection")

    # after intersecting, get angles of target feature pieces
    gdf_target_ix = gdf_target_ix.explode(index_parts=True)
    # gdf_target_ix[f_angle_tar] = gdf_target_ix.geometry.apply(lambda g: utils.get_line_angle(g))
    gdf_target_ix[f_angle_tar] = [utils.get_line_angle(g) for g in gdf_target_ix.geometry]


    # compare angles between source and target features; tag if target feature is roughly parallel to source feature
    gdf_target_ix['angle_diff'] = gdf_target_ix[f_angle_src] - gdf_target_ix[f_angle_tar]
    gdf_target_ix['is_parallel'] = gdf_target_ix.apply(lambda row: utils.is_similar_angle(row[f_angle_src], \
                                                row[f_angle_tar], max_deg_diff=20), axis=1)

    # then, filter out all pieces of target file that only intersected due to proximity, e.g. cross streets.
    # Keep only pieces that are parallel to source line or, if not parallel, then longer than the buffer width
    min_x_len = search_dist_ft * 2.3 # add 0.3 to account for streets that don't cross perpendicular

    gdf_out = gdf_target_ix.loc[(gdf_target_ix[f_par_flag] == True) | (gdf_target_ix.geometry.length > min_x_len)]
    
    if lts_field:
        gdf_out = gdf_out.rename(columns={lts_field: f_lts_standardized}) # standardize lts field name
    else:
        print("computing LTS for each final output links...")
        add_lts(in_df=gdf_out, f_bike_class=fld_bikeclass, f_osm_hwy=fld_hwytyp, fname_lts=f_lts_standardized)
    gdf_out[f_lts_standardized] = gdf_out[f_lts_standardized].astype('int')
    if fld_bikeclass: gdf_out[fld_bikeclass] = gdf_out[fld_bikeclass].astype('int')
    print("exporting to GIS file...")
    gdf_out = gdf_out.reset_index().drop(columns=['level_0', 'level_1']) # get rid of multilevel indexing

    gdf_out = apply_lts_override(gdf_out, f_lts=f_lts_standardized, f_jnid='osm_id')
    # utils.gdf_to_esri_fc(gdf_out, output_file)
    gdf_out.to_file(output_file, engine='pyogrio')

    print(f"success! output file is {output_file}")
    print("\nIMPORTANT: Manual visual inspection of output file strongly recommended to check for misconflations or wrong data.")

if __name__ == '__main__':
    
    # source lines whose data you want - existing bikeways
    # bikeway_fc = r"I:\Projects\Darren\PEP\ConveyalData\ConveyalNetworkDevelopment\ExistingBikeways\bikeways_sacog_2022\bikeways_sacog_2022.shp"
    # bike_class_field = 'BIKE_CLASS' # required. Field specifying bike facility class (1-4) of each bikeway link.
    # lts_field_name = None # optional bike level of traffic stress field; will computed via lts_config.csv if blank.
    # bikeway_otherfields = ['TRAIL_NAME', 'MILES'] # fields from source bikeway data set that you want in output conflation result. (geometry will be included automatically)
    # output_dir = r'I:\Projects\Darren\PEP\ConveyalData\ConveyalNetworkDevelopment\BikewayConflated2OSM_forLTSLayer\conflatedbikeway_existing'
    
    # source lines whose data you want - committed bikeways on existing OSM segments
    # probably need to keep separate from existing because of issue of conflicting LTS values between exising and committed
    bikeway_fc = r"I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\3__bikeways\latest_existing_bikeways\ExistingBikeway\ExistingBikeway.shp"
    bike_class_field = None # required. Field specifying bike facility class (1-4) of each bikeway link.
    lts_field_name = 'BIKE_CLASS' # optional bike level of traffic stress field; will computed via lts_config.csv if blank.
    bikeway_otherfields = ['FULLSTREET'] # fields from source bikeway data set that you want in output conflation result. (geometry will be included automatically)
    output_dir = r'I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\3__bikeways'

    # target lines to which you want to conflat source lines' data
    # osm_fc = input("Enter path to SHP of OSM links you wish to match bikeway data with: ").strip("\"") # r"I:\Projects\Darren\PEP\PEP_GIS\SHP\fromOSM\sacog_2023080920230818_1655_NewDevMerge.shp"
    # osm_fields = ['osm_id', 'name', 'highway', 'geometry']
    osm_fc = r"I:\Projects\Josh\Conveyal\conveyal_inputs\network_prep\2__filtered\pbf2shp\Six-County_Sacramento_Region_202609_filtered20260922_1031.shp"
    osm_fields = ['osm_id', 'name', 'highway'] # osm fields you want in conflation result (geometry will be included automatically)
    road_types_to_exclude = ['steps', 'pedestrian', 'bridleway', 'abandoned', 'footway', 'motorway_link', 'motorway', 'raceway']

    # output_dir = r'I:\Projects\Darren\PEP\ConveyalData\ConveyalNetworkDevelopment\BikewayConflated2OSM_forLTSLayer'

    #===============RUN SCRIPT===============================
    for f in [bike_class_field, lts_field_name]:
        if f: bikeway_otherfields.append(f)

    sufx = str(dt.datetime.now().strftime('%Y%m%d_%H%M'))
    output_name = Path(output_dir).joinpath(f'osm_w_sacogbw{sufx}.shp')

    simple_conflation(target_line_file=osm_fc, source_line_file=bikeway_fc,
                        output_file=output_name, target_fields=osm_fields,
                        source_fields=bikeway_otherfields, lts_field=lts_field_name,
                        fld_bikeclass=bike_class_field, hwytyps_to_exclude=road_types_to_exclude)

