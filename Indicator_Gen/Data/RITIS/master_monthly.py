export=False

import subprocess
import sys
from pathlib import Path
import time

# ====================================================================
# Configuration
# ====================================================================

# Vehicle type codes
tp_dict = {
    'Truck': 'T',
    'Pax': 'P',
    'Combined': 'TAP'
}

# Choose vehicle class to process
vehicle_class = 'Combined'  # Options: 'Truck', 'Pax', 'Combined'

# Path to scripts
PATH_SCRIPTS = Path(__file__).parent
create_yearly_script = PATH_SCRIPTS / 'create_current_year_table.py'
combine_yearly_script = PATH_SCRIPTS / 'combine_yearly_tables.py'
combine_monthly_script = PATH_SCRIPTS / 'combine_monthly_tables.py'
append_script = PATH_SCRIPTS / 'append_matching_tables.py'

# Paths for file discovery
PATH_SUMMARY = Path(r"I:/Projects/Josh/Regional Monitoring/Congestion/summary csv")

# ====================================================================
# Helper Functions
# ====================================================================

def run_script(script_path, script_name):
    """Run a Python script and return True if successful."""
    print(f"\n{'='*70}")
    print(f"Running: {script_name}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {script_name} failed with error code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ Error running {script_name}: {e}")
        return False


def find_latest_files(vehicle_code):
    """
    Find the most recent yearly summary and the most recent monthly summary.
    Returns (yearly_file, monthly_file) or (None, None) if not found.
    """
    
    # Look for yearly file (contains "Yearly" in name)
    yearly_files = list(PATH_SUMMARY.glob(f'Summary_Congestion_*{vehicle_code}_Yearly.csv'))
    if not yearly_files:
        print("  No yearly summary file found")
        return None, None
    
    yearly_files.sort(key=lambda x: x.stat().st_mtime)
    yearly_file = yearly_files[-1].name
    print(f"  Found yearly: {yearly_file}")
    
    # Look for monthly file (does NOT contain "Yearly" in name)
    monthly_files = [f for f in PATH_SUMMARY.glob(f'Summary_Congestion_*{vehicle_code}.csv') 
                     if 'Yearly' not in f.name]
    
    if not monthly_files:
        print("  No monthly summary file found")
        return None, None
    
    monthly_files.sort(key=lambda x: x.stat().st_mtime)
    monthly_file = monthly_files[-1].name
    print(f"  Found monthly: {monthly_file}")
    
    return yearly_file, monthly_file


def update_append_script(file1, file2):
    """Update the file names in append_matching_tables.py"""
    try:
        with open(append_script, 'r') as f:
            content = f.read()
        
        # Replace the file names
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('file1='):
                lines[i] = f'file1="{file1}"'
            elif line.strip().startswith('file2='):
                lines[i] = f'file2="{file2}"'
        
        with open(append_script, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✓ Updated {append_script.name}")
        print(f"  file1: {file1}")
        print(f"  file2: {file2}")
        return True
    except Exception as e:
        print(f"✗ Error updating append_matching_tables.py: {e}")
        return False


# ====================================================================
# Main Execution
# ====================================================================

def main():
    print(f"\n{'='*70}")
    print(f"RITIS Congestion Data Processing Pipeline")
    print(f"Vehicle Class: {vehicle_class}")
    print(f"{'='*70}")
    
    
    time.sleep(2)
    
    # Step 2: Combine all yearly tables
    print("\n[STEP 2/4] Combining all yearly tables...")
    if not run_script(combine_yearly_script, 'combine_yearly_tables.py'):
        print("\n✗ Pipeline stopped: Could not combine yearly tables")
        sys.exit(1)
    
    time.sleep(2)
    
    # Step 3: Combine monthly tables
    print("\n[STEP 3/4] Combining monthly tables...")
    if not run_script(combine_monthly_script, 'combine_monthly_tables.py'):
        print("\n✗ Pipeline stopped: Could not combine monthly tables")
        sys.exit(1)
    
    time.sleep(2)
    
    # Step 4: Append matching summary tables
    print("\n[STEP 4/4] Appending summary tables...")
    
    # Find the two most recent summary files
    file1, file2 = find_latest_files(tp_dict[vehicle_class])
    
    if not file1 or not file2:
        print("\n✗ Could not find summary files to append")
        print("  Expected at least 2 Summary CSV files in:")
        print(f"  {PATH_SUMMARY}")
        sys.exit(1)
    
    print(f"\nFound summary files to merge:")
    print(f"  File 1: {file1}")
    print(f"  File 2: {file2}")
    
    # Update append_matching_tables.py with the file names
    if not update_append_script(file1, file2):
        print("\n✗ Pipeline stopped: Could not update append script")
        sys.exit(1)
    
    if not run_script(append_script, 'append_matching_tables.py'):
        print("\n✗ Pipeline stopped: Could not append summary tables")
        sys.exit(1)
    
    # Success!
    print(f"\n{'='*70}")
    print(f"✓ Pipeline completed successfully!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()