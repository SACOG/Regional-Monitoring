export=False

from pathlib import Path
from zipfile import ZipFile
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

# Path to monthly csv files
PATH_IDRIVE = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/monthly csv")

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


# ====================================================================
# Main Processing Loop
# ====================================================================

all_system_metrics = []
all_final = pd.DataFrame()
print(f"Searching for zip files in: {PATH_IDRIVE}")
zip_files = list(PATH_IDRIVE.glob('*.zip'))

if not zip_files:
    print("No zip files found. Check PATH_IDRIVE and file structure.")
    sys.exit()
else:
    print(f"Found {len(zip_files)} zip files to process.")

for zip_path in zip_files:
    
    zip_name = zip_path.name
    
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
    
    # --- Infer year_month from zip_name (e.g., '2025_01TAP.zip' -> '2025_01')
    file_base = zip_name.split(".")[0]
    year_month = file_base[:7]  # 'YYYY_MM' format
    
    speed_file = year_month + '.csv'
    tmc_file = 'TMC_Identification.csv'
    
    # --- Load Data ---
    try:
        # Load traffic speed data
        with ZipFile(zip_path) as z:
            with z.open(speed_file) as f:
                df_traffic = pd.read_csv(f, usecols=['tmc_code', 'measurement_tstamp', 'speed', 'travel_time_seconds'])
                df_traffic['measurement_tstamp'] = pd.to_datetime(df_traffic['measurement_tstamp'], utc=True)
        
        # Load TMC metadata
        with ZipFile(zip_path) as z:
            with z.open(tmc_file) as f:
                df_tmc = pd.read_csv(f, usecols=['tmc', 'f_system', 'nhs', 'miles'])
                
        print(f"Traffic records loaded: {len(df_traffic):,}")
        print(f"TMC segments loaded: {len(df_tmc):,}")
        
    except (FileNotFoundError, KeyError) as e:
        print(f"Skipping {zip_path.name}: Required file not found inside zip ({speed_file} or {tmc_file}): {e}")
        continue
    except Exception as e:
        print(f"Skipping {zip_path.name}: Error loading data: {e}")
        continue
    
    # --- Early exit if traffic data is empty ---
    if df_traffic.empty or df_tmc.empty:
        print(f"Skipping {zip_path.name}: Empty dataframes")
        continue
    
    # --- Calculating Free Flow Speeds ---
    print("  ...Calculating Free Flow Speeds...")
    df_ff = df_tmc.merge(df_traffic, left_on='tmc', right_on='tmc_code', how='inner')
    df_ff['hour'] = df_ff['measurement_tstamp'].dt.hour
    
    # Filter for overnight free-flow period and NHS roads
    ff_mask = (df_ff['hour'] >= FF_PERIOD_START) | (df_ff['hour'] < FF_PERIOD_END)
    df_ff = df_ff[ff_mask]
    df_ff['f_system'] = df_ff['f_system'].astype(float)
    df_ff = df_ff[df_ff['nhs'] > 0]
    
    if len(df_ff) == 0:
        print("  ...Insufficient data on NHS roads for free-flow calculation.")
        continue
    
    ff_speeds = df_ff.groupby('tmc_code', group_keys=False).apply(calc_freeflow_speed, include_groups=False).reset_index()
    ff_speeds.columns = ['tmc_code', 'ff_speed_art60thp']
    epochs_night = df_ff.groupby('tmc_code').size().reset_index(name='epochs_night')
    
    if ff_speeds.empty:
        print("  ...Skipping remaining steps for this file.")
        continue
    
    # Clean up to free memory
    del df_ff

    # --- Calculate Hourly Speeds ---
    print("  ...Calculating Hourly Speeds...")
    df_hourly = df_traffic.merge(df_tmc, left_on='tmc_code', right_on='tmc', how='inner')
    df_hourly['day_name'] = df_hourly['measurement_tstamp'].dt.day_name()
    df_hourly = df_hourly[df_hourly['day_name'].isin(WEEKDAYS)]
    df_hourly['hour'] = df_hourly['measurement_tstamp'].dt.hour
    
    df_hourly = df_hourly.merge(ff_speeds, on='tmc_code', how='inner')
    df_hourly_clean = df_hourly[df_hourly['speed'] > 0].copy()
    
    # Keep only necessary columns for aggregation
    df_hourly_clean = df_hourly_clean[['tmc_code', 'measurement_tstamp', 'speed', 'travel_time_seconds', 'ff_speed_art60thp', 'hour']]
    
    # Calculate harmonic average speed by TMC and hour
    hourly_stats = df_hourly_clean.groupby(['tmc_code', 'hour']).agg(
        total_epochs_hr=('measurement_tstamp', 'count'),
        havg_spd_weekdy=('speed', lambda x: len(x) / (1.0 / x).sum()),
        avg_tt_sec_weekdy=('travel_time_seconds', 'mean'),
        ff_speed_art60thp=('ff_speed_art60thp', 'first')
    ).reset_index()

    #MIN_EPOCHS = int(hourly_stats['total_epochs_hr'].quantile(0.25))
    #print(f"  ...Using MIN_EPOCHS = {MIN_EPOCHS} based on 25th percentile of hourly epochs.")
    # Apply epoch filter and calculate congestion rank
    hourly_stats = hourly_stats[hourly_stats['total_epochs_hr'] >= MIN_EPOCHS]
    
    if len(hourly_stats) == 0:
        print("  ...Skipping remaining steps due to empty hourly statistics set.")
        continue
    
    hourly_stats['cong_ratio_hr_weekdy'] = (
        hourly_stats['havg_spd_weekdy'] / hourly_stats['ff_speed_art60thp']
    )
    hourly_stats['hour_cong_rank'] = (
        hourly_stats.groupby('tmc_code')['cong_ratio_hr_weekdy']
        .rank(method='first', ascending=True)
    )
    
    # Clean up to free memory
    del df_hourly, df_hourly_clean

    # --- Calculate Worst 4 Hours Speed and Slowest Hour ---
    print("  ...Calculating Worst 4 Hours and Slowest Hour metrics...")
    
    # Worst 4 Hours
    worst_hours = hourly_stats[hourly_stats['hour_cong_rank'] < 5][['tmc_code', 'hour']]
    
    df_worst = df_traffic.merge(df_tmc, left_on='tmc_code', right_on='tmc', how='inner')
    df_worst['day_name'] = df_worst['measurement_tstamp'].dt.day_name()
    df_worst = df_worst[df_worst['day_name'].isin(WEEKDAYS)]
    df_worst['hour'] = df_worst['measurement_tstamp'].dt.hour
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
    
    # Clean up to free memory
    del df_worst, hourly_stats, worst_hours
    
    # --- Create Final Report ---
    
    # Rename tmc_code to tmc for merging
    ff_speeds = ff_speeds.rename(columns={'tmc_code': 'tmc'})
    worst_stats = worst_stats.rename(columns={'tmc_code': 'tmc'})
    slowest = slowest.rename(columns={'tmc_code': 'tmc'})
    epochs_night = epochs_night.rename(columns={'tmc_code': 'tmc'})
    
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
    all_final = pd.concat([all_final, final], ignore_index=True)
    
    # --- Calculate System wide metrics ---
    print("  ...Calculating System-wide metrics...")
    valid_mask = (final['havg_spd_worst4hrs'] > -1) & (final['ff_speed_art60thp'] > -1)
    tot_nhs_dirmiles = final[valid_mask]['miles'].sum()
    
    # Congestion defined as worst 4 hours speed < 60% of free-flow speed
    congested_mask = (final['congratio_worst4hrs'] < 0.6) & valid_mask
    congested_miles = final[congested_mask]['miles'].sum()
    
    pct_dirmi_congested = (congested_miles / tot_nhs_dirmiles * 100) if tot_nhs_dirmiles > 0 else 0
    
    # Count tmcs with valid speed metrics for congestion calculation
    num_valid_tmcs = valid_mask.sum()
    print(f"TMCs with valid speed metrics: {num_valid_tmcs:,}")

    # Total observations used in the congestion calculation (only count observations from TMCs that were actually used and have epoch data)
    obs_mask = valid_mask & (final['epochs_worst4hrs'] > -1)
    obs_used_for_congestion = int(final[obs_mask]['epochs_worst4hrs'].sum())

    # Store results for final summary
    system_metrics = {
        'month': year_month,
        'total_nhs_dirmiles': tot_nhs_dirmiles,
        'congested_miles': congested_miles,
        'pct_miles_congested': pct_dirmi_congested,
        'tmcs_insufficient_data': len(final[~valid_mask]),
        'num_valid_tmcs': num_valid_tmcs,
        'obs_used_for_congestion': obs_used_for_congestion
    }
    all_system_metrics.append(system_metrics)
    
    print(f"  Total NHS directional miles: {tot_nhs_dirmiles:,.2f}")
    print(f"  Percent of miles congested: {pct_dirmi_congested:.2f}%")

# ====================================================================
# Final Summary Output
# ====================================================================

if all_system_metrics:
    print("\n\n*** Summary of All Processed Months ***")
    df_summary = pd.DataFrame(all_system_metrics)
    # Reorder columns for a cleaner look
    df_summary = df_summary[['month', 'total_nhs_dirmiles', 'congested_miles', 'pct_miles_congested', 
                         'tmcs_insufficient_data', 'num_valid_tmcs', 'obs_used_for_congestion']]
    print(df_summary.to_string(index=False, float_format="%.2f"))
else:
    print("\nNo data processed successfully.")
    sys.exit()

# ====================================================================
# Export
# ====================================================================    
# name output file based on vehicle class and date range
min_time = min(df_summary['month'])
max_time = max(df_summary['month'])
base_filename = f"Final_Congestion_{min_time}_to_{max_time}{tp_dict[vehicle_class]}.csv"

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