export=False
"""
Docstring for Indicator_Gen.Data.RITIS.combine_monthly_tables
Author: Terrell Enoru
Date: December 2025
This script combines all the monthly tables for the current year into a single yearly table for a specified vehicle class 
so it can be processed with the other yearly zips by the combine_yearly_tables.py script.
"""
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import tempfile
import sys
import shutil
# ====================================================================
# Configuration
# ====================================================================
PATH_MONTHLY = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/monthly csv")
PATH_YEARLY = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/yearly csv")

# Vehicle type codes
tp_dict = {
    'Truck': 'T',
    'Pax': 'P',
    'Combined': 'TAP'
}

# Vehicle type descriptions for Contents.txt
vehicle_descriptions = {
    'Truck': 'Trucks',
    'Pax': 'Passenger vehicles',
    'Combined': 'Trucks and passenger vehicles'
}

# Choose vehicle class to process
vehicle_class = 'Combined'  # Options: 'Truck', 'Pax', 'Combined'

# Chunk size for reading large CSVs
CHUNK_SIZE = 5_000_000

# ====================================================================
# Main Logic
# ====================================================================

vehicle_suffix = tp_dict[vehicle_class]
vehicle_description = vehicle_descriptions[vehicle_class]

print(f"Looking for {vehicle_class} monthly zip files in: {PATH_MONTHLY}\n")

# Find all monthly zip files for this vehicle type
monthly_zips = sorted(list(PATH_MONTHLY.glob(f'*{vehicle_suffix}.zip')))

if not monthly_zips:
    print(f"No monthly zip files found for vehicle class '{vehicle_class}'")
    sys.exit()

print(f"Found {len(monthly_zips)} monthly zip files:")
for z in monthly_zips:
    print(f"  - {z.name}")

# Extract year from first zip file name
year = monthly_zips[0].name[:4]
print(f"\nDetermined year: {year}")

# ====================================================================
# Load TMC Metadata (from most recent zip)
# ====================================================================

print("\nLoading TMC metadata from most recent month...")
tmc_zip_path = monthly_zips[-1]  # Last (most recent)
try:
    with ZipFile(tmc_zip_path) as z:
        tmc_files = [f for f in z.namelist() if 'TMC_Identification' in f]
        if tmc_files:
            with z.open(tmc_files[0]) as f:
                df_tmc = pd.read_csv(f)
            print(f"TMC segments loaded: {len(df_tmc):,}")
        else:
            print("Warning: Could not locate TMC_Identification.csv")
            df_tmc = pd.DataFrame()
except Exception as e:
    print(f"Error loading TMC: {e}")
    df_tmc = pd.DataFrame()

# ====================================================================
# Combine Monthly Data (Chunked) and Write to Temp CSV
# ====================================================================

print(f"\nCombining monthly data in chunks...")

with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_csv:
    temp_csv_path = temp_csv.name
    header_written = False
    total_rows = 0
    
    for zip_path in monthly_zips:
        print(f"  Processing {zip_path.name}...")
        
        try:
            with ZipFile(zip_path) as z:
                # Get the CSV filename
                csv_files = [f for f in z.namelist() if f.endswith('.csv') and 'TMC' not in f]
                
                if not csv_files:
                    print(f"    Warning: No data CSV found in {zip_path.name}")
                    continue
                
                csv_name = csv_files[0]
                
                # Read in chunks and write to temp file
                with z.open(csv_name) as f:
                    for i, chunk in enumerate(pd.read_csv(f, usecols=['tmc_code', 'measurement_tstamp', 'speed'], 
                                                            chunksize=CHUNK_SIZE)):
                        if not header_written:
                            chunk.to_csv(temp_csv_path, mode='w', index=False, header=True)
                            header_written = True
                        else:
                            chunk.to_csv(temp_csv_path, mode='a', index=False, header=False)
                        
                        total_rows += len(chunk)
                        if i % 5 == 0:
                            print(f"    Chunk {i+1}: {total_rows:,} rows total so far...")
                
                print(f"    Finished {zip_path.name}: {total_rows:,} rows accumulated")
        
        except Exception as e:
            print(f"    Error processing {zip_path.name}: {type(e).__name__}: {e}")
            continue
    
    print(f"\nTotal combined rows: {total_rows:,}")

# ====================================================================
# Create Output Zip File
# ====================================================================

print(f"\nCreating yearly zip file...")

zip_filename = f"{year}{vehicle_suffix}.zip"
zip_output_path = PATH_YEARLY / zip_filename

if zip_output_path.exists():
    print(f"Warning: {zip_filename} already exists. Skipping.")
    import os
    os.unlink(temp_csv_path)
    sys.exit()

# Prepare Contents.txt
contents_text = f"Speed, historical average speed, reference speed, travel time (reported in seconds), and data density for NPMRDS from INRIX ({vehicle_description}) data expanded"

try:
    print("  Writing CSV to zip (this may take a moment for large files)...")
    with ZipFile(zip_output_path, 'w') as zf:
        # Write yearly CSV in chunks to avoid loading entire file into memory
        yearly_csv_name = f"{year}.csv"
        with open(temp_csv_path, 'rb') as f_in:
            with zf.open(yearly_csv_name, 'w',force_zip64=True) as f_out:
                shutil.copyfileobj(f_in, f_out, length=8192*1024)
                #while True:
                    #chunk = f_in.read(8192 * 1024)  # 8MB chunks
                    #if not chunk:
                        #break
                    #f_out.write(chunk)
        print(f"  Added {yearly_csv_name} ({total_rows:,} rows)")
        
        # Write TMC identification
        if not df_tmc.empty:
            zf.writestr('TMC_Identification.csv', df_tmc.to_csv(index=False))
            print(f"  Added TMC_Identification.csv ({len(df_tmc):,} segments)")
        
        # Write Contents.txt
        zf.writestr('Contents.txt', contents_text)
        print(f"  Added Contents.txt")
    
    print(f"\nSuccessfully created: {zip_output_path}")
    print(f"This file is ready to be processed by combine_yearly_tables.py")

except Exception as e:
    print(f"Error creating zip file: {e}")
    sys.exit()

finally:
    # Clean up temp file
    import os
    if Path(temp_csv_path).exists():
        os.unlink(temp_csv_path)