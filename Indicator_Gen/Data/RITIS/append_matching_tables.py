"""
Docstring for Indicator_Gen.Data.RITIS.append_matching_tables
Author: Terrell Enoru
Date: December 2025
This script takes two files and if they have matching columns and compatible metadata (Final/Summary, vehicle class), merges them into a single file and exports it to the appropriate directory.
If Congestion_2_Monthly is set to True, it will also export an Excel file formatted for the Congestion 2 Monthly indicator.
"""
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
########## ENTER NAME OF FILES TO BE MERGED HERE ###########
file1="Summary_Congestion_2017_01_to_2024_12TAP.csv"
file2="Summary_Congestion_2025_01_to_2025_10TAP.csv"
# Set True if you want to use combined df for Monthly Congestion Plot
Congestion_2_Monthly=True
############################################################
PATH_FINAL = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/final csv")
PATH_SUMMARY = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/summary csv")

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

import functions as func

# Vehicle type codes for filename parsing - matches your existing scripts
tp_dict = {
    'Truck': 'T',
    'Pax': 'P',
    'Combined': 'TAP'
}


def extract_metadata(filename):
    """
    Extract type (Final/Summary), date, and vehicle class from filename.
    Handles formats like:
    - 2021_01TAP_final.csv
    - 2021_01T_summary.csv
    - Final_Congestion_2021_01_to_2021_06_TAP.csv
    - Summary_Congestion_2021_01_to_2021_06_T.csv
    """
    name = filename.replace('.csv', '').replace('.pdf', '')
    name_lower = name.lower()
    
    # Determine if Final or Summary
    if 'final' in name_lower:
        file_type = 'Final'
    elif 'summary' in name_lower:
        file_type = 'Summary'
    else:
        return None
    
    # Extract vehicle code (TAP, T, or P) - must be at end
    vehicle_code = None
    if name_lower.endswith('tap'):
        vehicle_code = 'TAP'
    elif name_lower.endswith('t'):
        vehicle_code = 'T'
    elif name_lower.endswith('p'):
        vehicle_code = 'P'

    if not vehicle_code:
        return None
    
    # Extract date range - look for YYYY_MM patterns
    import re
    dates = re.findall(r'\d{4}_\d{2}', name)
    
    if len(dates) == 0:
        return None
    elif len(dates) == 1:
        # Single date, assume it's the date
        min_date = dates[0]
        max_date = dates[0]
    else:
        # Multiple dates, take first and last
        min_date = min(dates)
        max_date = max(dates)
    
    return {
        'type': file_type,
        'vehicle_code': vehicle_code,
        'min_date': min_date,
        'max_date': max_date,
        'full_name': name
    }

def export_to_csv(df, metadata, output_dir='.',Monthly_Congestion_Setting=False):
    """Export dataframe to CSV format."""
    
    file_type = metadata['type'].lower()
    vehicle_code = metadata['vehicle_code']
    min_time = metadata['min_time']
    max_time = metadata['max_time']
    
    
    # Generate output filename matching your naming convention
    output_filename = f"{file_type.capitalize()}_Congestion_{min_time}_to_{max_time}{vehicle_code}"
    
    

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / f"{output_filename}.csv"
    if Monthly_Congestion_Setting:
        indicator = 'Congestion_2'
        sample_type = 'RITIS'
        geography = 'MPO'
        year_start=int(min_time.split('_')[0])
        year_end=int(max_time.split('_')[0])

        try:
            df_about = func.write_about(sample_type, indicator, year_start, year_end, geography=geography)
            output_filename = 'Congestion_2 Monthly SACOG RITIS.xlsx'
            xl_path = output_dir / output_filename
            df['mpo']='SACOG'
            with pd.ExcelWriter(xl_path, engine='xlsxwriter') as writer:
                df_about      .to_excel(writer, index=False, sheet_name='About', header=False)
                df            .to_excel(writer, index=False, sheet_name='SACOG'              )
                print(f"✓ XLSX exported: {xl_path}")
            return True
        except Exception as e:
            print(f"Error exporting Excel: {e}")
            return False


    # Export to CSV
    try:
        df.to_csv(csv_path, index=False)
        print(f"✓ CSV exported: {csv_path}")
        return True
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return False
    
def validate_and_merge(file1, file2, output_dir='.'):
    """
    Validate two CSV files and merge them.
    
    Returns:
    - (df_combined, metadata) on success
    - (None, None) on failure
    """
    
    # Extract metadata
    meta1 = extract_metadata(file1)
    meta2 = extract_metadata(file2)
    
    if not meta1 or not meta2:
        print("Error: Could not parse one or both filenames")
        print(f"  File 1: {file1}")
        print(f"  File 2: {file2}")
        return None, None
    
    # Check if both are same type (both Final or both Summary)
    if meta1['type'] != meta2['type']:
        print(f"Error: File types don't match")
        print(f"  {file1}: {meta1['type']}")
        print(f"  {file2}: {meta2['type']}")
        return None, None
    
    # Check if both are same vehicle class
    if meta1['vehicle_code'] != meta2['vehicle_code']:
        print(f"Error: Vehicle classes don't match")
        print(f"  {file1}: {meta1['vehicle_code']} ")
        print(f"  {file2}: {meta2['vehicle_code']} ")
        return None, None
    
    # Read CSV files
    try:
        if meta1['type'] == 'Final':
            file1 = PATH_FINAL / file1
            file2 = PATH_FINAL / file2
            output_dir = PATH_FINAL
        else:
            file1 = PATH_SUMMARY / file1
            file2 = PATH_SUMMARY / file2
            output_dir = PATH_SUMMARY
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        print(f"✓ Loaded {file1}: {len(df1):,} rows")
        print(f"✓ Loaded {file2}: {len(df2):,} rows")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return None, None
    except Exception as e:
        print(f"Error reading files: {e}")
        return None, None
    
    # Check if columns match
    if not df1.columns.equals(df2.columns):
        print("Error: Column names don't match")
        print(f"  File 1 columns: {list(df1.columns)}")
        print(f"  File 2 columns: {list(df2.columns)}")
        
        # Show which columns are different
        diff_cols = set(df1.columns) ^ set(df2.columns)
        if diff_cols:
            print(f"  Differing columns: {diff_cols}")
        
        return None, None
    
    # Combine dataframes
    combined_df = pd.concat([df1, df2], ignore_index=True)
    print(f"✓ Combined: {len(combined_df):,} total rows")
    
    # If 'year_month' column exists, use it for sorting and date extraction
    if 'year_month' in combined_df.columns:
        try:
            combined_df['year_month'] = pd.to_datetime(combined_df['year_month'], format='%Y_%m')
            min_time = combined_df['year_month'].min().strftime('%Y_%m')
            max_time = combined_df['year_month'].max().strftime('%Y_%m')
            combined_df['year_month'] = combined_df['year_month'].dt.strftime('%Y_%m')
            combined_df = combined_df.sort_values('year_month').reset_index(drop=True)
            print(f"✓ Sorted by year_month: {min_time} to {max_time}")
        except Exception as e:
            print(f"Warning: Could not parse year_month column: {e}")
            min_time = meta1['min_date']
            max_time = meta2['max_date']
    elif 'month' in combined_df.columns:
        try:
            combined_df['month'] = pd.to_datetime(combined_df['month'], format='%Y_%m')
            min_time = combined_df['month'].min().strftime('%Y_%m')
            max_time = combined_df['month'].max().strftime('%Y_%m')
            combined_df['month'] = combined_df['month'].dt.strftime('%Y_%m')
            combined_df = combined_df.sort_values('month').reset_index(drop=True)
            print(f"✓ Sorted by month: {min_time} to {max_time}")
        except Exception as e:
            print(f"Warning: Could not parse month column: {e}")
            min_time = meta1['min_date']
            max_time = meta2['max_date']

    else:
        # No year_month column, use metadata dates
        min_time = min(meta1['min_date'], meta2['min_date'])
        max_time = max(meta1['max_date'], meta2['max_date'])
    
    # Compile metadata for output
    metadata = {
        'type': meta1['type'],
        'vehicle_code': meta1['vehicle_code'],
        'min_time': min_time,
        'max_time': max_time
    }
    print(f"\n✓ Validation passed")
    print(f"  Type: {metadata['type']}")
    print(f"  Vehicle Code: ({metadata['vehicle_code']})")
    print(f"  Date Range: {metadata['min_time']} to {metadata['max_time']}\n")

    success=export_to_csv(combined_df, metadata, output_dir,Congestion_2_Monthly)

    if success:
        print(f"\n{'='*70}")
        print(f"✓ Process complete!")
        print(f"{'='*70}\n")
    else:
        print("\n✗ Export had issues (see warnings above)")

    return combined_df, metadata





def main():
    
    
    print(f"\n{'='*70}")
    print(f"CSV Merger for RITIS Congestion Data")
    print(f"{'='*70}\n")
    
    # Validate and merge
    df_combined, metadata = validate_and_merge(file1, file2)
    
    if df_combined is None:
        print("\n✗ Merge failed")
        sys.exit(1)
    
    
    
    
    
    


if __name__ == "__main__":
    main()