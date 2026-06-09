"""
IPEDS Access → CSV Extractor
============================

Pulls the C_yyyy_A completions table out of an IPEDS Access database and
writes it to CSV — the input format edu2_pipeline.py expects. This removes
the manual Access export step (the one that has produced truncated / failed
files), so the CSVs are always complete and consistently formatted.

REQUIREMENTS (Windows):
  - Microsoft Access Database Engine, bitness matching your Python.
    Check Python bitness:  python -c "import struct; print(struct.calcsize('P')*8)"
    64-bit Python needs the 64-bit Access engine; 32-bit needs 32-bit.
    Download: search "Microsoft Access Database Engine 2016 Redistributable".
  - pip install pyodbc

USAGE:
  Single file:
      python extract_access.py "C:\\path\\to\\IPEDS202223.accdb"
  It auto-detects the C-table (e.g. C2022_A) inside and writes C2022_A.csv
  next to this script.

  All databases in a folder:
      python extract_access.py --folder "I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\IPEDS"
  Finds every .accdb/.mdb, extracts each one's C-table to CSV.

NOTES:
  - The current file organization of the .accdb files makes the folder parameter less useful default to single file
  - If the Access engine isn't installed or the bitness is wrong, pyodbc will
    raise a clear driver error; the message below explains the fix.
  - Close the database in the Access application before running, or the file
    may be locked.
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import pyodbc
except ImportError:
    sys.exit('pyodbc is not installed. Run:  pip install pyodbc')

import pandas as pd


ACCESS_DRIVER = '{Microsoft Access Driver (*.mdb, *.accdb)}'

# We only need the completions table. Pattern matches C2022_A, C2023_A, etc.
CTABLE_PATTERN = re.compile(r'^C\d{4}_A$', re.IGNORECASE)


def connect(accdb_path):
    """Open a read-only connection to an Access database."""
    conn_str = f'DRIVER={ACCESS_DRIVER};DBQ={accdb_path};'
    try:
        return pyodbc.connect(conn_str, readonly=True)
    except pyodbc.Error as e:
        msg = str(e)
        hint = ''
        if 'IM002' in msg or 'driver' in msg.lower():
            hint = ('\n\nThe Microsoft Access Database Engine is missing or its '
                    'bitness does not match your Python install. Check with:\n'
                    '    python -c "import struct; print(struct.calcsize(\'P\')*8)"\n'
                    'and install the matching (32- or 64-bit) Access Database '
                    'Engine redistributable.')
        sys.exit(f'Could not open {Path(accdb_path).name}: {msg}{hint}')


def find_ctable(conn):
    """Return the name of the C_yyyy_A table in this database, or None."""
    cursor = conn.cursor()
    tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
    matches = [t for t in tables if CTABLE_PATTERN.match(t)]
    if not matches:
        return None
    # If somehow more than one, take the newest by year
    return sorted(matches)[-1]


def extract_one(accdb_path, out_dir):
    """Extract the C-table from one Access DB to CSV. Returns the output path."""
    accdb_path = Path(accdb_path)
    print(f'Opening {accdb_path.name} ...')
    conn = connect(str(accdb_path))

    table = find_ctable(conn)
    if table is None:
        conn.close()
        print(f'  No C_yyyy_A table found in {accdb_path.name} — skipped.')
        return None

    print(f'  Reading table {table} ...')
    df = pd.read_sql(f'SELECT * FROM [{table}]', conn)
    conn.close()

    out_path = Path(out_dir) / f'{table}.csv'
    df.to_csv(out_path, index=False)
    print(f'  Wrote {out_path.name}: {len(df):,} rows, {df.shape[1]} columns')
    return out_path


def main():
    ap = argparse.ArgumentParser(description='Extract IPEDS C-tables from Access to CSV.')
    ap.add_argument('path', nargs='?', help='Path to a single .accdb/.mdb file')
    ap.add_argument('--folder', help='Folder of Access databases to extract all of')
    ap.add_argument('--out', default='.', help='Output folder for CSVs (default: current dir)')
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.folder:
        folder = Path(args.folder)
        dbs = sorted(list(folder.glob('*.accdb')) + list(folder.glob('*.mdb')))
        if not dbs:
            sys.exit(f'No .accdb/.mdb files found in {folder}')
        print(f'Found {len(dbs)} Access database(s).\n')
        for db in dbs:
            extract_one(db, out_dir)
            print()
    elif args.path:
        extract_one(args.path, out_dir)
    else:
        ap.print_help()
        sys.exit('\nProvide a database path or --folder.')

    print('Done.')


if __name__ == '__main__':
    main()