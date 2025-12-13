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

# Minimum Epochs for Hourly Speed Calculation (Yearly Threshold)
MIN_EPOCHS = 100 

# SharePoint
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' 
PATH_CONGESTION = PATH_SP / 'Data' / 'Safe Equitable Resilient Infrastructure' / 'Congestion'
PATH_PHED  = PATH_CONGESTION / 'RITIS' / 'PHED'
PATH_LOTTR = PATH_CONGESTION / 'RITIS' / 'LOTTR'
#PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")

## Format csv names
# clean_names.clean_files(PATH_IDRIVE) # Assuming this is a local utility


# ====================================================================
# Functions (Refined)
# ====================================================================

# Removed 'calc_freeflow_speed' as its logic is now vectorized in 'process_year_optimized'

def process_year_optimized(df_traffic_year, df_tmc, year_str):
    """
    Processes the FULL year of traffic data using vectorized operations 
    and memory-efficient type casting.
    """
    print(f"  Processing full year: {year_str}...")
    
    # --- 1. MEMORY OPTIMIZATION: Type Casting & Time Extraction ---
    # Convert tmc_code to category to save massive RAM
    df_traffic_year['tmc_code'] = df_traffic_year['tmc_code'].astype('category')
    
    # Extract hour and day of week (0=Mon, 4=Fri)
    df_traffic_year['hour'] = df_traffic_year['measurement_tstamp'].dt.hour.astype(np.uint8)
    df_traffic_year['day_of_week'] = df_traffic_year['measurement_tstamp'].dt.dayofweek.astype(np.uint8) 
    df_traffic_year.drop(columns=['measurement_tstamp'], inplace=True)

    # --- 2. Filter & Merge Metadata ---
    tmc_cols = ['tmc', 'f_system', 'nhs', 'miles']
    # Ensure f_system is float for comparison
    df_tmc_keep = df_tmc.loc[df_tmc['nhs'] > 0, tmc_cols].copy()
    df_tmc_keep['tmc'] = df_tmc_keep['tmc'].astype('category') 

    # Inner merge to keep only relevant data
    df_base = df_traffic_year.merge(df_tmc_keep, left_on='tmc_code', right_on='tmc', how='inner')
    
    # --- 3. Free Flow Speed (Vectorized) ---
    print("    Calculating Free-Flow Speeds...")
    # Filter: 8PM (20) to 6AM (6)
    mask_ff = (df_base['hour'] >= FF_PERIOD_START) | (df_base['hour'] < FF_PERIOD_END)
    df_ff = df_base[mask_ff].copy() # Explicit copy to avoid SettingWithCopyWarning
    
    # Calculate percentiles efficiently by f_system group
    fw_mask = df_ff['f_system'].isin([1.0, 2.0])
    
    # Freeways (1,2) -> 85th percentile
    ff_fw = df_ff[fw_mask].groupby('tmc_code', observed=True)['speed'].quantile(0.85)
    
    # Arterials (other) -> 60th percentile
    ff_art = df_ff[~fw_mask].groupby('tmc_code', observed=True)['speed'].quantile(0.60)
    
    # Combine results
    ff_speeds = pd.concat([ff_fw, ff_art]).rename('ff_speed_art60thp').reset_index()
    
    # Epochs count
    epochs_night = df_ff.groupby('tmc_code', observed=True).size().reset_index(name='epochs_night')

    if ff_speeds.empty:
        print("    Warning: No free-flow speeds calculated.")
        return None, None

    # --- 4. Hourly Congestion Metrics (Vectorized & Memory-Efficient) ---
    print("    Calculating Hourly Metrics...")
    # Filter: Weekdays (0=Mon, 4=Fri)
    mask_weekday = df_base['day_of_week'].le(4)
    df_weekday = df_base[mask_weekday].copy()

    # Harmonic Mean calculation: N / Sum(1/v). We calculate sum(1/v) inside agg.
    # IMPROVEMENT: Calculate sum(1/v) directly inside agg to avoid creating a large 'inv_speed' column.
    hourly_agg = df_weekday.groupby(['tmc_code', 'hour'], observed=True)['speed'].agg(
        total_epochs_hr='count',
        sum_inv_speed=lambda x: np.sum(1.0 / x)
    ).reset_index()
    
    # Filter MIN_EPOCHS
    hourly_agg = hourly_agg[hourly_agg['total_epochs_hr'] >= MIN_EPOCHS]
    
    # Compute Harmonic Mean
    hourly_agg['havg_spd_weekdy'] = hourly_agg['total_epochs_hr'] / hourly_agg['sum_inv_speed']
    
    # Merge FF speeds back
    hourly_agg = hourly_agg.merge(ff_speeds, on='tmc_code', how='inner')
    
    # Congestion Ratio & Rank
    hourly_agg['cong_ratio'] = hourly_agg['havg_spd_weekdy'] / hourly_agg['ff_speed_art60thp']
    hourly_agg['rank'] = hourly_agg.groupby('tmc_code')['cong_ratio'].rank(method='first', ascending=True)

    # --- 5. Worst 4 Hours & Slowest Hour ---
    
    # Slowest Hour (Rank 1)
    slowest = hourly_agg[hourly_agg['rank'] == 1].copy()
    slowest = slowest[['tmc_code', 'hour', 'havg_spd_weekdy', 'total_epochs_hr']]
    slowest.columns = ['tmc', 'slowest_hr', 'slowest_hr_speed', 'epochs_slowest_hr']
    slowest = slowest.drop_duplicates(subset=['tmc'])

    # Worst 4 Hours (Rank < 5) - Get keys
    worst_4_keys = hourly_agg[hourly_agg['rank'] < 5][['tmc_code', 'hour']]
    
    # Merge keys back to raw weekday data, calculate sum(1/v) on raw data
    df_worst_raw = df_weekday.merge(worst_4_keys, on=['tmc_code', 'hour'], how='inner')
    
    # Aggregation on raw data for worst 4 hours
    worst_stats = df_worst_raw.groupby('tmc_code', observed=True)['speed'].agg(
        epochs_worst4hrs='count',
        sum_inv_speed_w4=lambda x: np.sum(1.0 / x)
    ).reset_index()
    
    worst_stats['havg_spd_worst4hrs'] = worst_stats['epochs_worst4hrs'] / worst_stats['sum_inv_speed_w4']
    worst_stats = worst_stats.rename(columns={'tmc_code': 'tmc'})

    # --- 6. Final Assembly and System Metrics ---
    final = df_tmc_keep.merge(ff_speeds.rename(columns={'tmc_code':'tmc'}), on='tmc', how='left')
    final = final.merge(worst_stats[['tmc', 'havg_spd_worst4hrs', 'epochs_worst4hrs']], on='tmc', how='left')
    final = final.merge(slowest, on='tmc', how='left')
    final = final.merge(epochs_night.rename(columns={'tmc_code':'tmc'}), on='tmc', how='left')
    
    # Fill NA values (-1.0) and calculate final congestion ratios
    cols_to_fill = ['ff_speed_art60thp', 'havg_spd_worst4hrs', 'slowest_hr_speed', 'epochs_worst4hrs', 'epochs_slowest_hr', 'epochs_night']
    for c in cols_to_fill:
        final[c] = final[c].fillna(-1.0)
        
    # Congestion Ratio: Congested Speed / FF Speed
    final['congratio_worst4hrs'] = np.where(
        (final['havg_spd_worst4hrs'] > -1) & (final['ff_speed_art60thp'] > 0),
        np.clip(final['havg_spd_worst4hrs'] / final['ff_speed_art60thp'], None, 1.0),
        -1.0
    )
    final['year'] = year_str
    
    # --- System Metrics (CORRECTED) ---
    valid = (final['havg_spd_worst4hrs'] > -1) & (final['ff_speed_art60thp'] > -1)
    congested = (final['congratio_worst4hrs'] < 0.6) & valid
    
    num_total_tmcs_nhs = len(final)
    tmcs_insufficient_data = num_total_tmcs_nhs - valid.sum()
    obs_used_for_congestion = int(final.loc[final['epochs_worst4hrs'] > 0, 'epochs_worst4hrs'].sum())
    
    sys_metrics = {
        'year': year_str,
        'total_nhs_dirmiles': final.loc[valid, 'miles'].sum(),
        'congested_miles': final.loc[congested, 'miles'].sum(),
        'num_valid_tmcs': valid.sum(),
        'tmcs_insufficient_data': tmcs_insufficient_data, # Corrected
        'obs_used_for_congestion': obs_used_for_congestion # Corrected
    }
    sys_metrics['pct_miles_congested'] = (sys_metrics['congested_miles'] / sys_metrics['total_nhs_dirmiles'] * 100) if sys_metrics['total_nhs_dirmiles'] > 0 else 0
    
    return final, sys_metrics


# ====================================================================
# Main Processing Loop (No Changes Needed Here)
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
    
    # ... (File name checks and year inference) ...
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
    
    file_base = zip_name.split(".")[0]
    if file_base.endswith('TAP'):
        year = file_base[:-3]
    elif file_base.endswith('T') or file_base.endswith('P'):
        year = file_base[:-1]
    else:
        year = file_base
    
    speed_file = year + '.csv'
    tmc_file = 'TMC_Identification.csv'
    
    # --- 1. Load TMC metadata ---
    try:
        with ZipFile(zip_path) as z:
            with z.open(tmc_file) as f:
                df_tmc = pd.read_csv(f)
        print(f"TMC segments loaded: {len(df_tmc):,}")
    except Exception as e:
        print(f"Skipping {zip_path.name}: Error loading TMC data: {e}")
        continue
    # --- 2. Load traffic data in chunks ---
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  Using temporary directory: {temp_dir}")
        temp_dir_path = Path(temp_dir)
        parquet_writers = {} 
        
        print("  Loading traffic data in chunks and partitioning...")
        CHUNK_SIZE = 5_000_000

        try:
            with ZipFile(zip_path) as z:
                with z.open(speed_file) as f:
                    with pd.read_csv(f, chunksize=CHUNK_SIZE) as reader:
                        for i, chunk in enumerate(reader):
                            if i % 5 == 0:
                                print(f"    Processing chunk {i+1}...")
                            
                            chunk['measurement_tstamp'] = pd.to_datetime(chunk['measurement_tstamp'], utc=True)
                            chunk['measurement_tstamp'] = chunk['measurement_tstamp'].dt.tz_localize(None)

                            chunk['year_month_period'] = chunk['measurement_tstamp'].dt.to_period('M')

                            for year_month_period, data in chunk.groupby('year_month_period'):
                                year_month_str = year_month_period.strftime('%Y_%m')
                                temp_file_path = temp_dir_path / f"{year_month_str}.parquet"

                                data_to_write = data[['tmc_code', 'measurement_tstamp', 'speed']]
                                table = pa.Table.from_pandas(data_to_write, preserve_index=False)

                                if year_month_str not in parquet_writers:
                                    writer = pq.ParquetWriter(str(temp_file_path), table.schema)
                                    parquet_writers[year_month_str] = writer
                                else:
                                    writer = parquet_writers[year_month_str]
                                
                                writer.write_table(table)

        except Exception as e:
            print(f"Skipping {zip_path.name}: Error partitioning traffic data: {e}")
            for writer in parquet_writers.values(): writer.close()
            continue

        for writer in parquet_writers.values():
            writer.close()
        print("  Finished partitioning.")

        # -----------------------------------------
        # STEP 3 *MUST REMAIN INSIDE TEMP DIR BLOCK*
        # -----------------------------------------
        print("  Loading full year data from partitioned files...")

        try:
            parquet_files = list(temp_dir_path.glob('*.parquet'))

            if not parquet_files:
                raise FileNotFoundError(f"No parquet files found in temporary directory for {year}.")

            table = pq.read_table(
                source=parquet_files,
                columns=['tmc_code', 'measurement_tstamp', 'speed']
            )

            df_traffic_year = table.to_pandas()
            final, system_metrics = process_year_optimized(df_traffic_year, df_tmc, year)

            if final is not None and system_metrics is not None:
                all_final_list.append(final)
                all_system_metrics.append(system_metrics)

        except Exception as e:
            print(f"  Error processing year {year}: {type(e).__name__}: {e}")

    

# ====================================================================
# Final Summary Output (No Changes Needed Here)
# ====================================================================

if all_system_metrics:
    print("\n\n*** Summary of All Processed Years ***")
    df_summary = pd.DataFrame(all_system_metrics)
    # Ensure this column list matches the keys returned by process_year_optimized
    df_summary = df_summary[['year', 'total_nhs_dirmiles', 'congested_miles', 'pct_miles_congested', 'tmcs_insufficient_data', 'num_valid_tmcs', 'obs_used_for_congestion']]
    print(df_summary.to_string(index=False, float_format="%.2f"))
    print("\nConcatenating all yearly reports...")
    all_final = pd.concat(all_final_list, ignore_index=True)
else:
    print("\nNo data processed successfully.")
    sys.exit()

# ====================================================================
# Export
# ====================================================================    
min_time = min(df_summary['year'])
max_time = max(df_summary['year'])
base_filename = f"Final_Congestion_{min_time}_to_{max_time}_{tp_dict[vehicle_class]}_Yearly.csv"

output_path = PATH_FINAL / f"{base_filename}"
if output_path.exists():
    print(f"\n*** Skipping {base_filename} ***")
    print(f"  Output file already exists at: {output_path}")
else:
    print(f"  ...Exporting to {output_path}")
    all_final.to_csv(output_path, index=False)
    print("  Export complete.")

summary_output_filename = f"Summary{base_filename[5:]}"
summary_output_path = PATH_SUMMARY / summary_output_filename

if summary_output_path.exists():
    print(f"\n*** Skipping {summary_output_filename} ***")
    print(f"  Output file already exists at: {summary_output_path}")
else:
    print(f"  ...Exporting to {summary_output_filename}")
    df_summary.to_csv(summary_output_path, index=False)
    print("  Export complete.")