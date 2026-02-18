from pathlib import Path
import geopandas as gpd
import pandas as pd
import sys

import pandas as pd

# ==========================================================================
# Functions
# ==========================================================================

# ========================================================================
# Format the Summary data cleanly
# ========================================================================
def format_summary(df, group_col, o_col='ohu_23', r_col='rhu_23'):
    # Aggregate
    summary = df.groupby(group_col)[[o_col, r_col]].sum() # needs to be scaled by proportion of population from each census tract falling within each jurisdiction
    
    # Add totals row
    totals = pd.DataFrame(summary.sum()).T
    totals.index = ['Totals']
    summary = pd.concat([summary, totals])
    
    # Reset index
    summary = summary.reset_index()
    
    # Rename columns
    summary = summary.rename(columns={
        group_col: 'Displacement Group',
        o_col: 'Owner Occupied',
        r_col: 'Renter Occupied'
    })
    
    # Add commas for readability
    summary['Owner Occupied'] = summary['Owner Occupied'].apply(lambda x: f"{x:,}")
    summary['Renter Occupied'] = summary['Renter Occupied'].apply(lambda x: f"{x:,}")
    
    return summary

# ========================================================================
# Regional summary
# ========================================================================
def summarize_typology_region(df):
    return format_summary(df, 'typ_simplified_name')

# ========================================================================
# Jurisdiction-level summary
# ========================================================================
def summarize_typology_jurisdiction(df):
    summaries = {}
    for juris, group in df.groupby('JURIS'):
        summaries[juris] = format_summary(group, 'typ_simplified_name')
    return summaries

# ==========================================================================
# Variables
# ==========================================================================
DATA_Dir="I:\Projects\Josh\RHNA\Data\POPEMP_25\emp25_data"
input_path = DATA_Dir+'/inputs/'
output_path = DATA_Dir+'/outputs/'

GDB = Path(r'I:\Projects\Josh\RHNA\ArcPro\RHNA.gdb')
FC_JURISDICTIONS = 'GISOWNER_City_County'
FC_TRACTS = 'GISOWNER_T2020_Census_Tracts_SACOG_Region'
FC_BLOCKS = 'GISOWNER_T2020_Census_Blocks_SACOG_Region' # Left join this guy onto the census tracts file, only needing three fields from the Blocks layer [BLOCK ID, CENSUS TRACT GEOID, Population]


# ==========================================================================
#Reading in data
# ==========================================================================
print('Importing GIS layers:')
print('Jurisdictions...'); gdf_jurisdictions = gpd.read_file(GDB, layer=FC_JURISDICTIONS)
print('Census Tracts...'); gdf_tracts        = gpd.read_file(GDB, layer=FC_TRACTS       )
print('Blocks...'       ); gdf_blocks        = gpd.read_file(GDB, layer=FC_BLOCKS       ) # may take a few minutes to import

print("Importing typology data")
df_typol = pd.read_csv(output_path+'/typologies/Sacramento_typology_output.csv',dtype={'FIPS':str,'rhu_23':int,'ohu_23':int})
df_typol=df_typol.rename(columns={'FIPS':'GEOCODE'})

gdf_overlay = gpd.overlay(gdf_jurisdictions, gdf_tracts, how='intersection', keep_geom_type=False)

typ_overlay_merge = pd.merge(df_typol,
                             gdf_overlay,
                             on='GEOCODE'
                             )

clean_typ_overlay = typ_overlay_merge[['GEOCODE','typ_cat','ohu_23','rhu_23','hh_23','JURIS','county','typ_simplified_name','typ_name']]

# Region-level summary
regional_summary = summarize_typology_region(clean_typ_overlay)

# Jurisdiction-level summaries
jur_summaries = summarize_typology_jurisdiction(clean_typ_overlay)
df_jur_summaries = pd.concat(jur_summaries.values(), keys=jur_summaries.keys())
df_jur_summaries = df_jur_summaries.reset_index()
df_jur_summaries = df_jur_summaries.rename(columns={
    'level_0': 'Jurisdiction',
    'index': 'Typology'
})

sys.exit()
df_jur_summaries = df_jur_summaries.drop(columns=['level_1'])
df_jur_summaries.to_csv(output_path+"/typologies/jurisdiction_typology_summary.csv", index=False)






## TODO:
# (1) Import BLOCK level (or parcel level) population data
# (2) Overlay the black level data with census tracts layer before you overlay the census tracts with the counties/jurisdictions layer (this will create the crosswalk from BLOCK ID to CENSUS TRACT GEOID ID  to JURISDICTION ID) (left join block level data to what you have at the end)
# (3) Using block level population estimates, for each census tract roll up the number of people that fall within each jurisdiction (group by statement)
## Ex:
## Census Tract ID 06067009618 falls within both Elk Grove and Sacramento County Unincorporated
## group by jurisdiction and census tract, sum block level population estimates
## then we can calculate percent of population within this census tract that falls within Elk Grove vs Sacramento County Unincorporated (this will be our scalar for rolling up census tract population to jurisdictions)
# (4) Scale back the final numbers that you have by scalars when rolling up



