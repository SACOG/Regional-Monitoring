

import arcpy, os

# Define the input CSV file path and the output geodatabase path
csv_file = r"I:/Projects/Josh/Regional Monitoring/ArcPro_v2/Data/2020_urban_blocks_CA_v2.csv"
out_gdb = r"I:/Projects/Josh/Regional Monitoring/ArcPro_v2/MnR.gdb"

# Check if the geodatabase exists, create if it doesn't
if not arcpy.Exists(out_gdb):
    gdb_path, gdb_name = os.path.split(out_gdb)
    arcpy.CreateFileGDB_management(gdb_path, gdb_name)

# Construct the output table name
out_table_name = os.path.splitext(os.path.basename(csv_file))[0]
out_table = os.path.join(out_gdb, out_table_name)

# Execute the TableToGeodatabase tool
arcpy.TableToGeodatabase_conversion(csv_file, out_gdb)

print(f"CSV file '{csv_file}' imported to '{out_table}' in geodatabase '{out_gdb}'")

