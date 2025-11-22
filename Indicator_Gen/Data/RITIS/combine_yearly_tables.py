export=False

from pathlib import Path
from zipfile import ZipFile
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile
import os
import clean_names
import pandas as pd
import numpy as np
import time
import sys

# ====================================================================
# Configuration and Path Setup
# ====================================================================
PATH_GIT = Path.home() / 'Documents' / 'Github Repos' / 'Regional-Monitoring' / 'Indicator_Gen'
PATH_CODE    = PATH_GIT / 'Data' / 'RITIS'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_SQL = PATH_GIT / 'Data' / 'RITIS' / 'sql_scripts'

sys.path.append(str(PATH_CONFIG0))

pd.set_option('display.max_columns', None)

# Path to yearly csv files
PATH_IDRIVE = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/yearly csv")

# Output Paths
PATH_FINAL = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/final csv")
PATH_SUMMARY = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/summary csv")

# Vehicle type codes for filename parsing
tp_dict = {
    'Truck': 'T',
    'Pax': 'P',
    'Combined': 'TAP'
}

# Free-flow period parameters (8 PM to 6 AM)
FF_PERIOD_START = 20  
FF_PERIOD_END = 6     

# Choose what vehicle class to process
vehicle_class = 'Combined'  # Options: 'Truck', 'Pax', 'Combined'

# Weekdays
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# Minimum Epochs for Hourly Speed Calculation (Approx. 40% coverage of ~92 epochs)
MIN_EPOCHS = 35

# SharePoint
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' 
PATH_CONGESTION = PATH_SP / 'Data' / 'Safe Equitable Resilient Infrastructure' / 'Congestion'
PATH_PHED  = PATH_CONGESTION / 'RITIS' / 'PHED'
PATH_LOTTR = PATH_CONGESTION / 'RITIS' / 'LOTTR'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")

## Format csv names
clean_names.clean_files(PATH_IDRIVE)

# ====================================================================
# Functions
# ====================================================================
def calc_freeflow_speed(group):
    """
    Calculates free-flow speed by TMC based on F_System:
    Freeways (f_system 1,2): 85th percentile speed
    Arterials (other): 60th percentile speed
    """
    f_system = group['f_system'].iloc[0]
    # Check for NaN and Freeways (1.0 or 2.0)
    if pd.notna(f_system) and f_system in [1.0, 2.0]:
        return group['speed'].quantile(0.85)
    else:
        return group['speed'].quantile(0.60)


def process_month(df_traffic_month, df_tmc, year_month):
    """
    Process a single month's worth of data and return metrics.
    
    Parameters:
    - df_traffic_month: DataFrame with traffic data for one month
    - df_tmc: DataFrame with TMC metadata
    - year_month: String in format 'YYYY_MM'
    
    Returns:
    - final: DataFrame with TMC-level metrics
    - system_metrics: Dictionary with system-wide metrics
    """
    
    print(f"  Processing {year_month}...")
    print(f"  Traffic records: {len(df_traffic_month):,}")
    
    # --- Keep only necessary columns from traffic data ---
    # Columns needed: tmc_code, measurement_tstamp, speed, travel_time_seconds, nhs
    traffic_cols = ['tmc_code', 'measurement_tstamp', 'speed', 'travel_time_seconds']
    df_traffic_month = df_traffic_month[traffic_cols]
    
    # --- Keep only necessary columns from TMC metadata ---
    # Columns needed: tmc, f_system, nhs, miles
    tmc_cols = ['tmc', 'f_system', 'nhs', 'miles']
    df_tmc_keep = df_tmc[tmc_cols].copy()
    
    # --- Create one base DataFrame ---
    # Merge TMC info onto traffic data. Use 'inner' to keep only TMCs present in both.
    df_base = df_traffic_month.merge(
        df_tmc_keep, 
        left_on='tmc_code', 
        right_on='tmc', 
        how='inner'
    )
    df_base['hour'] = df_base['measurement_tstamp'].dt.hour
    

    # --- Calculating Free Flow Speeds ---
    ff_mask = (df_base['hour'] >= FF_PERIOD_START) | (df_base['hour'] < FF_PERIOD_END)
    df_ff = df_base.loc[ff_mask]
    
    df_ff = df_ff.astype({'f_system': 'float'})
    df_ff = df_ff[df_ff['nhs'] > 0]
    
    if len(df_ff) > 0:
        ff_speeds = df_ff.groupby('tmc_code', group_keys=False).apply(calc_freeflow_speed, include_groups=False).reset_index()
        ff_speeds.columns = ['tmc_code', 'ff_speed_art60thp']
        epochs_night = df_ff.groupby('tmc_code').size().reset_index(name='epochs_night')
    else:
        print(f"  Warning: Insufficient data on NHS roads for free-flow calculation in {year_month}")
        return None, None
        
    if ff_speeds.empty:
        print(f"  Warning: No free-flow speeds calculated for {year_month}")
        return None, None

    # --- Calculate Hourly Speeds ---
    df_hourly = df_base[['tmc_code', 'measurement_tstamp', 'speed', 'travel_time_seconds', 'f_system', 'nhs', 'hour', 'miles']].copy()
    df_hourly['day_name'] = df_hourly['measurement_tstamp'].dt.day_name()
    df_hourly = df_hourly[df_hourly['day_name'].isin(WEEKDAYS)]

    df_hourly = df_hourly.merge(ff_speeds, on='tmc_code', how='inner')
    df_hourly_clean = df_hourly[df_hourly['speed'] > 0]
    
    # Calculate harmonic average speed by TMC and hour
    hourly_stats = df_hourly_clean.groupby(['tmc_code', 'hour']).agg(
        total_epochs_hr=('measurement_tstamp', 'count'),
        havg_spd_weekdy=('speed', lambda x: len(x) / (1.0 / x).sum()),
        avg_tt_sec_weekdy=('travel_time_seconds', 'mean'),
        ff_speed_art60thp=('ff_speed_art60thp', 'first')
    ).reset_index()
    
    
    # Apply epoch filter and calculate congestion rank
    hourly_stats = hourly_stats[hourly_stats['total_epochs_hr'] >= MIN_EPOCHS]
    
    if len(hourly_stats) > 0:
        hourly_stats['cong_ratio_hr_weekdy'] = (
            hourly_stats['havg_spd_weekdy'] / hourly_stats['ff_speed_art60thp']
        )
        hourly_stats['hour_cong_rank'] = (
            hourly_stats.groupby('tmc_code')['cong_ratio_hr_weekdy']
            .rank(method='first', ascending=True)
        )
    else:
        print(f"  Warning: No hourly statistics after filtering for {year_month}")
        return None, None

    # --- Calculate Worst 4 Hours Speed and Slowest Hour ---
    # Worst 4 Hours
    worst_hours = hourly_stats[hourly_stats['hour_cong_rank'] < 5][['tmc_code', 'hour']]
    
    df_worst = df_base[['tmc_code', 'measurement_tstamp', 'speed', 'hour', 'miles']].copy()
    df_worst['day_name'] = df_worst['measurement_tstamp'].dt.day_name()
    df_worst = df_worst[df_worst['day_name'].isin(WEEKDAYS)]
    
    df_worst = df_worst.merge(worst_hours, on=['tmc_code', 'hour'], how='inner')
    df_worst = df_worst.merge(ff_speeds, on='tmc_code', how='inner')
    
    worst_stats = df_worst.groupby('tmc_code').agg(
        epochs_worst4hrs=('measurement_tstamp', 'count'),
        havg_spd_worst4hrs=('speed', lambda x: len(x) / (1.0 / x).sum()),
        ff_speed_art60thp=('ff_speed_art60thp', 'first')
    ).reset_index()
    
    # Slowest Hour
    slowest = hourly_stats[hourly_stats['hour_cong_rank'] == 1].copy()
    slowest = slowest[['tmc_code', 'hour', 'havg_spd_weekdy', 'total_epochs_hr']]
    slowest.columns = ['tmc_code', 'slowest_hr', 'slowest_hr_speed', 'epochs_slowest_hr']
    slowest = slowest.drop_duplicates(subset=['tmc_code'], keep='first')
    
    # --- Create Final Report ---
    # Rename tmc_code to tmc for merging
    ff_speeds = ff_speeds.rename(columns={'tmc_code': 'tmc'})
    worst_stats = worst_stats.rename(columns={'tmc_code': 'tmc'})
    slowest = slowest.rename(columns={'tmc_code': 'tmc'})
    epochs_night = epochs_night.rename(columns={'tmc_code': 'tmc'})
    
    # Start with just the TMC metadata we need for the final report
    final = df_tmc[df_tmc['nhs'] > 0].copy()
    final = final.merge(ff_speeds, on='tmc', how='left')
    final = final.merge(worst_stats[['tmc', 'havg_spd_worst4hrs', 'epochs_worst4hrs']], 
                       on='tmc', how='left')
    final = final.merge(slowest, on='tmc', how='left')
    final = final.merge(epochs_night, on='tmc', how='left')
    
    # Fill missing values with -1.0 for metrics
    metric_cols = ['ff_speed_art60thp', 'havg_spd_worst4hrs', 'slowest_hr', 
                   'slowest_hr_speed', 'epochs_worst4hrs', 'epochs_slowest_hr', 'epochs_night']
    for col in metric_cols:
        if col in final.columns:
            final[col] = final[col].fillna(-1.0)
    
    # Calculate congestion ratios
    final['congratio_worst4hrs'] = np.where(
        (final['havg_spd_worst4hrs'] > -1) & (final['ff_speed_art60thp'] > -1),
        np.minimum(final['havg_spd_worst4hrs'] / final['ff_speed_art60thp'], 1.0),
        -1.0
    )
    final['congratio_worsthr'] = np.where(
        (final['slowest_hr_speed'] > -1) & (final['ff_speed_art60thp'] > -1),
        final['slowest_hr_speed'] / final['ff_speed_art60thp'],
        -1.0
    )
    final['year_month'] = year_month
    
    # --- Calculate System wide metrics ---
    valid_mask = (final['havg_spd_worst4hrs'] > -1) & (final['ff_speed_art60thp'] > -1)
    tot_nhs_dirmiles = final[valid_mask]['miles'].sum()
    
    # Congestion defined as worst 4 hours speed < 60% of free-flow speed
    congested_mask = (final['congratio_worst4hrs'] < 0.6) & valid_mask
    congested_miles = final[congested_mask]['miles'].sum()
    
    pct_dirmi_congested = (congested_miles / tot_nhs_dirmiles * 100) if tot_nhs_dirmiles > 0 else 0
    
    # Store results for final summary
    system_metrics = {
        'month': year_month,
        'total_nhs_dirmiles': tot_nhs_dirmiles,
        'congested_miles': congested_miles,
        'pct_miles_congested': pct_dirmi_congested,
        'tmcs_insufficient_data': len(final[~valid_mask])
    }
    
    print(f"  Total NHS directional miles: {tot_nhs_dirmiles:,.2f}")
    print(f"  Percent of miles congested: {pct_dirmi_congested:.2f}%")
    
    return final, system_metrics


# ====================================================================
# Main Processing Loop
# ====================================================================

all_system_metrics = []
all_final_list = []

print(f"Searching for zip files in: {PATH_IDRIVE}")
zip_files = list(PATH_IDRIVE.glob('*.zip'))

if not zip_files:
    print("No zip files found. Check PATH_IDRIVE and file structure.")
    sys.exit()
else:
    print(f"Found {len(zip_files)} zip files to process.")

for zip_path in zip_files:
    
    zip_name = zip_path.name
    
    # Check if this is the right vehicle type
    no_extension = zip_name.split(".")[0]
    if tp_dict[vehicle_class] == 'TAP':
        if not no_extension.endswith('TAP'):
            print(f"Skipping {zip_name}: Filename does not end with expected vehicle type code")
            continue
    elif tp_dict[vehicle_class] in ['T', 'P']:
        if not no_extension.endswith(tp_dict[vehicle_class]):
            print(f"Skipping {zip_name}: Filename does not end with expected vehicle type code")
            continue

    print(f"\n*** Processing {zip_path.name} ***")
    
    # --- Infer year from zip_name (e.g., '2024TAP.zip' -> '2024')
    # Remove the vehicle type suffix to get the year
    file_base = zip_name.split(".")[0]
    if file_base.endswith('TAP'):
        year = file_base[:-3]
    elif file_base.endswith('T') or file_base.endswith('P'):
        year = file_base[:-1]
    else:
        year = file_base
    
    # Expect the yearly CSV to be named like '2024.csv'
    speed_file = year + '.csv'
    tmc_file = 'TMC_Identification.csv'
    
    # --- 1. Load TMC metadata (This is small and safe) ---
    try:
        with ZipFile(zip_path) as z:
            with z.open(tmc_file) as f:
                df_tmc = pd.read_csv(f)
        print(f"TMC segments loaded: {len(df_tmc):,}")
    except (FileNotFoundError, KeyError) as e:
        print(f"Skipping {zip_path.name}: Required file not found inside zip ({tmc_file}): {e}")
        continue
    except Exception as e:
        print(f"Skipping {zip_path.name}: Error loading TMC data: {e}")
        continue

    # --- 2. Partition Traffic Data to Disk (The final, memory-safe ETL step) ---
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  Using temporary directory: {temp_dir}")
        temp_dir_path = Path(temp_dir)
        
        # Dictionary to hold the active ParquetWriter object for each monthly file
        parquet_writers = {} 
        
        print("  Loading traffic data in chunks and partitioning to monthly files using PyArrow...")
        CHUNK_SIZE = 5_000_000

        try:
            with ZipFile(zip_path) as z:
                with z.open(speed_file) as f:
                    with pd.read_csv(f, chunksize=CHUNK_SIZE) as reader:
                        for i, chunk in enumerate(reader):
                            print(f"    Processing chunk {i+1}...")
                            
                            # Convert to datetime and explicitly remove timezone for the Period conversion
                            chunk['measurement_tstamp'] = pd.to_datetime(chunk['measurement_tstamp'], utc=True)
                            chunk['year_month_period'] = chunk['measurement_tstamp'].dt.tz_localize(None).dt.to_period('M')
                            
                            # Group by month
                            for year_month_period, data in chunk.groupby('year_month_period'):
                                year_month_str = year_month_period.strftime('%Y_%m')
                                temp_file_path = temp_dir_path / f"{year_month_str}.parquet"
                                
                                # Convert the pandas DataFrame slice into a PyArrow Table
                                table = pa.Table.from_pandas(data.drop(columns=['year_month_period']), preserve_index=False)
                                
                                # Check if a writer for this month already exists
                                if year_month_str not in parquet_writers:
                                    # Create a new writer and store it
                                    writer = pq.ParquetWriter(str(temp_file_path), table.schema)
                                    parquet_writers[year_month_str] = writer
                                else:
                                    # Use the existing writer
                                    writer = parquet_writers[year_month_str]
                                
                                # Write the chunk to the file
                                writer.write_table(table)
        
        except (FileNotFoundError, KeyError) as e:
            print(f"Skipping {zip_path.name}: Required file not found inside zip ({speed_file}): {e}")
            # Ensure writers are closed before continuing/exiting
            for writer in parquet_writers.values():
                writer.close()
            continue
        except ImportError:
            print("\n*** ERROR: 'pyarrow' is required for this script. ***")
            print("Please install it in your environment: pip install pyarrow")
            sys.exit()
        except Exception as e:
            print(f"Skipping {zip_path.name}: Error loading/partitioning traffic data: {e}")
            # Ensure writers are closed before continuing/exiting
            for writer in parquet_writers.values():
                writer.close()
            continue

        # --- IMPORTANT: Close all writers after all chunks are processed ---
        for writer in parquet_writers.values():
            writer.close()
        print("  Finished writing all partitioned files.")

        # --- 3. Process data one month at a time from partitioned files ---
        monthly_files = sorted(temp_dir_path.glob("*.parquet"))

        for mf in monthly_files:
            year_month = mf.stem  # e.g. "2024_01"
            print(f"  Processing monthly parquet file: {mf.name}")

            # Load the parquet file
            df_traffic_month = pq.read_table(mf).to_pandas()

            # Call your monthly processing function
            final, system_metrics = process_month(df_traffic_month, df_tmc, year_month)

            if final is None or system_metrics is None:
                print(f"  Skipping {mf.name}: insufficient data")
                continue

            # Append monthly results
            all_final_list.append(final)
            all_system_metrics.append(system_metrics)

        # ... (rest of your monthly processing logic is correct and follows here)

# ====================================================================
# Final Summary Output
# ====================================================================

if all_system_metrics:
    print("\n\n*** Summary of All Processed Months ***")
    df_summary = pd.DataFrame(all_system_metrics)
    # Reorder columns for a cleaner look
    df_summary = df_summary[['month', 'total_nhs_dirmiles', 'congested_miles', 'pct_miles_congested', 'tmcs_insufficient_data']]
    print(df_summary.to_string(index=False, float_format="%.2f"))
    print("\nConcatenating all monthly reports...")
    all_final = pd.concat(all_final_list, ignore_index=True)
else:
    print("\nNo data processed successfully.")
    sys.exit()

# ====================================================================
# Export
# ====================================================================    
# name output file based on vehicle class and date range
min_time = min(df_summary['month'])
max_time = max(df_summary['month'])
base_filename = f"Final_Congestion_{vehicle_class}_{min_time}_to_{max_time}.csv"

output_path = PATH_FINAL / f"{base_filename}"
if output_path.exists():
    print(f"\n*** Skipping {base_filename} ***")
    print(f"  Output file already exists at: {output_path}")
else:
    print(f"  ...Exporting to {output_path}")
    all_final.to_csv(output_path, index=False)
    print("  Export complete.")

# Define the output file name for the monthly summary
summary_output_filename = f"Summary{base_filename[5:]}"
summary_output_path = PATH_SUMMARY / summary_output_filename

# Check if the output file already exists
if summary_output_path.exists():
    print(f"\n*** Skipping {summary_output_filename} ***")
    print(f"  Output file already exists at: {summary_output_path}")
else:
    print(f"  ...Exporting to {summary_output_filename}")
    df_summary.to_csv(summary_output_path, index=False)
    print("  Export complete.")