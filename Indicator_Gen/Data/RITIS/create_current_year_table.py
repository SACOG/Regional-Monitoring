export=False

from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import sys

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
# Load and Combine Monthly Data
# ====================================================================

print("\nLoading and combining monthly data...")

all_dfs = []
tmc_file_path = None

for zip_path in monthly_zips:
    print(f"  Processing {zip_path.name}...")
    
    try:
        with ZipFile(zip_path) as z:
            # Get the CSV filename (format: YYYY_MM{suffix}.csv)
            csv_files = [f for f in z.namelist() if f.endswith('.csv') and 'TMC' not in f]
            
            if not csv_files:
                print(f"    Warning: No data CSV found in {zip_path.name}")
                continue
            
            csv_name = csv_files[0]
            
            # Load the monthly data
            with z.open(csv_name) as f:
                df = pd.read_csv(f, usecols=['tmc_code', 'measurement_tstamp', 'speed'])
                all_dfs.append(df)
                print(f"    Loaded {len(df):,} rows from {csv_name}")
            
            # Get TMC file from the most recent zip (last in sorted list)
            if tmc_file_path is None:
                tmc_files = [f for f in z.namelist() if 'TMC_Identification' in f]
                if tmc_files:
                    tmc_file_path = (zip_path, tmc_files[0])
    
    except Exception as e:
        print(f"    Error processing {zip_path.name}: {e}")
        continue

if not all_dfs:
    print("No data was successfully loaded.")
    sys.exit()

# Combine all monthly dataframes
print(f"\nCombining {len(all_dfs)} months of data...")
df_yearly = pd.concat(all_dfs, ignore_index=True)
print(f"Total rows in combined yearly data: {len(df_yearly):,}")

# ====================================================================
# Load TMC Metadata
# ====================================================================

print("Loading TMC metadata...")
if tmc_file_path:
    zip_path, tmc_name = tmc_file_path
    with ZipFile(zip_path) as z:
        with z.open(tmc_name) as f:
            df_tmc = pd.read_csv(f)
    print(f"TMC segments loaded: {len(df_tmc):,}")
else:
    print("Warning: Could not locate TMC_Identification.csv")
    df_tmc = pd.DataFrame()

# ====================================================================
# Create Output Zip File
# ====================================================================

print(f"\nCreating yearly zip file...")

zip_filename = f"{year}{vehicle_suffix}.zip"
zip_output_path = PATH_YEARLY / zip_filename

if zip_output_path.exists():
    print(f"Warning: {zip_filename} already exists. Skipping.")
    sys.exit()

# Prepare Contents.txt
contents_text = f"Speed, historical average speed, reference speed, travel time (reported in seconds), and data density for NPMRDS from INRIX ({vehicle_description}) data expanded"

try:
    with ZipFile(zip_output_path, 'w') as zf:
        # Write yearly CSV
        yearly_csv_name = f"{year}.csv"
        zf.writestr(yearly_csv_name, df_yearly.to_csv(index=False))
        print(f"  Added {yearly_csv_name} ({len(df_yearly):,} rows)")
        
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