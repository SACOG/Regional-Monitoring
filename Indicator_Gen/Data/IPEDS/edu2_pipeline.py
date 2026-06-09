"""
Edu_2 Indicator Pipeline — IPEDS Completions → Degrees by Field
================================================================

Inputs:  IPEDS completions C-tables, as EITHER:
           - an Access database (.accdb/.mdb) — the C-table is read directly.
           - a CSV export (C_yyyy_A.csv), or
           
         Each source is listed with its IPEDS year in `new_years` (in main()).
Output:  Edu_2_updated.xlsx with 3 sheets (About+CIP, RawData, AggregatedData)

How to use it next year (two options):

  Option A — straight from the Access database (no manual export):
    1. Drop the new IPEDS database in the folder (e.g. IPEDS202425.accdb).
    2. Add it to `new_years` in main(), e.g. ('IPEDS202425.accdb', 2024).
    3. python edu2_pipeline.py
    Requires pyodbc + the Microsoft Access Database Engine (bitness must match
    Python). If that isn't available, use Option B.

  Option B — from a CSV export (the portable fallback):
    1. Export the C-table to CSV (or run extract_access.py to do it for you),
       with field names on the first row.
    2. Add the CSV to `new_years`, e.g. ('C2024_A.csv', 2024).
    3. python edu2_pipeline.py

Both paths feed the same logic and produce identical results; a validation
guard stops the run if any target institution is missing (catches truncated
or failed exports).

Methodology: see METHODOLOGY_NOTES.md.

Currently runs in APPEND mode: historical rows (2005-2022) are carried over
from the existing Edu_2.xlsx RawData. To do a full ground-up rebuild from
IPEDS sources alone, sources for years 2004-2020 would also be needed.
"""

from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
import os
import re
import time
import warnings
warnings.filterwarnings('ignore')


os.chdir(Path(__file__).parent)

# ============================================================================
# CONFIG
# ============================================================================

UNITID_MAP = {
    109208: 'American River College',
    110617: 'California State University-Sacramento',
    110644: 'University of California-Davis',
    113096: 'Cosumnes River College',
    122180: 'Sacramento City College',
    123341: 'Sierra College',
    126119: 'Yuba College',
    444219: 'Folsom Lake College',
}

# AWLEVEL -> Type. Four graduate codes collapse to one "Graduate" bucket.
#   3 = Associate, 5 = Bachelor, 7 = Master, 17/18/19 = Doctoral variants
AWLEVEL_TO_TYPE = {3: 'Associate', 5: 'Bachelor',
                   7: 'Graduate', 17: 'Graduate', 18: 'Graduate', 19: 'Graduate'}

# Edu_2 Year label = IPEDS C-table year + offset. The published file labels
# each C-table's data one year ahead (C2021_A data -> Year 2022), because the
# C-table sits inside the next year's IPEDS database (C2021_A is in IPEDS 2021-22).
# Verified: C2021_A reproduces published Year 2022 exactly (284/284 cells).
YEAR_OFFSET = 1

# Which majors to count. [1] = first major only (historical methodology).
MAJORNUM_FILTER = [1]


# ============================================================================
# PIPELINE
# ============================================================================


# Matches the IPEDS completions table inside an Access DB, e.g. C2022_A.
_CTABLE_PATTERN = re.compile(r'^C\d{4}_A$', re.IGNORECASE)


def _load_completions(source_path):
    """Load a C-table from either a CSV or an Access database.

    - .csv             -> read directly (the historical path; needs no drivers)
    - .accdb / .mdb    -> read the C_yyyy_A table via pyodbc (needs the
                          Microsoft Access Database Engine, bitness matching
                          Python). pyodbc is only imported when actually used,
                          so the CSV path keeps working without it.

    Returns a DataFrame with CIPCODE as string and column names upper-cased.
    """
    ext = Path(source_path).suffix.lower()

    if ext == '.csv':
        c = pd.read_csv(source_path, encoding='latin-1', dtype={'CIPCODE': str})

    elif ext in ('.accdb', '.mdb'):
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                'Reading Access databases needs pyodbc (pip install pyodbc) and '
                'the Microsoft Access Database Engine. Alternatively, export the '
                'C-table to CSV and pass that instead.')
        driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
        try:
            conn = pyodbc.connect(f'DRIVER={driver};DBQ={source_path};', readonly=True)
        except pyodbc.Error as e:
            raise RuntimeError(
                f'Could not open {Path(source_path).name}: {e}. If this is a '
                f'driver/bitness error, install the Access Database Engine that '
                f'matches your Python bitness, or use a CSV export instead.')
        # Find the C_yyyy_A table inside the database
        cur = conn.cursor()
        tables = [row.table_name for row in cur.tables(tableType='TABLE')]
        matches = sorted(t for t in tables if _CTABLE_PATTERN.match(t))
        if not matches:
            conn.close()
            raise ValueError(f'No C_yyyy_A table found in {Path(source_path).name}.')
        table = matches[-1]
        c = pd.read_sql(f'SELECT * FROM [{table}]', conn)
        conn.close()
        c['CIPCODE'] = c['CIPCODE'].astype(str).str.strip()  # IPEDS stores CIPCODE as text; match CSV handling

    else:
        raise ValueError(
            f'Unsupported source type "{ext}" for {Path(source_path).name}. '
            f'Use a .csv, .accdb, or .mdb file.')

    c.columns = c.columns.str.upper()  # normalize: some years use lowercase names
    return c


def build_rawdata_for_year(source_path, ipeds_year):
    """One year of IPEDS completions -> RawData rows.

    source_path may be a CSV export or an Access database (.accdb/.mdb).
    """
    c = _load_completions(source_path)

    df = c[c['UNITID'].isin(UNITID_MAP)].copy()
    df = df[df['AWLEVEL'].isin(AWLEVEL_TO_TYPE)]
    df = df[df['MAJORNUM'].isin(MAJORNUM_FILTER)]

    # 2-digit CIP rollup rows only. IPEDS pre-aggregates the same data at the
    # 2-digit, 4-digit, and 6-digit levels; we want only the 2-digit roll-ups
    # (summing all three would triple-count). The 2-digit rows are the ones whose
    # CIP value has no decimal/sub-series detail. We normalize first so this works
    # whether CIPCODE arrived as a zero-padded string ("01", from CSV) or as a
    # numeric/decimal value ("1", "14.0101", from Access).
    # Identify the 2-digit rollup rows in a way that works for both formats:
    #   CSV    stores CIPCODE as zero-padded text:  "01", "14", "14.0101"
    #   Access returns it as numbers/decimals:       1.0,  14.0,  14.0101
    # The 2-digit rollup is the whole-number series total (e.g. 1.0 / "01"),
    # i.e. the numeric value equals its own integer floor. Sub-series like
    # 14.0101 or "01.06" have a fractional part and are excluded.
    # The 2-digit rollup row is the one whose CIPCODE is exactly two characters
    # ("01", "44"). IPEDS also emits redundant "44.00"/"44.0000" representations
    # of the same total; keeping only the 2-char form avoids triple-counting.
    # _load_completions guarantees CIPCODE is a clean string for both CSV and
    # Access sources, so this length test works regardless of origin.
    df = df[df['CIPCODE'].str.len() == 2]
    df = df[df['CIPCODE'] != '99']               # drop institution-total rollup
    df['CIPCODE'] = df['CIPCODE'].astype(int)    # RawData stores as int

    # IPEDS renamed the total column in newer releases:
    #   2012-13 and earlier: CRACE24 (old race/ethnicity schema total)
    #   2013-14 onward:      CTOTALT
    if 'CTOTALT' in df.columns:
        total_col = 'CTOTALT'
    elif 'CRACE24' in df.columns:
        total_col = 'CRACE24'
    else:
        raise ValueError(
            f'{Path(source_path).name}: no completions total column found '
            f'(expected CTOTALT or CRACE24).')

    g = df.groupby(['UNITID', 'CIPCODE', 'AWLEVEL'], as_index=False)[total_col].sum()
    g = g.rename(columns={total_col: 'CTOTALT'})
    g['Year']   = ipeds_year + YEAR_OFFSET
    g['INSTNM'] = g['UNITID'].map(UNITID_MAP)
    g['Type']   = g['AWLEVEL'].map(AWLEVEL_TO_TYPE)

    # --- Validation guard ---------------------------------------------------
    # A truncated or failed export can silently produce too few rows (e.g. only
    # AWLEVEL=1 certificate rows survive, or whole institutions are missing),
    # which would append an empty/partial year with no error. Catch it here by
    # confirming every target institution produced at least one qualifying row.
    found_ids   = set(g['UNITID'].unique())
    missing_ids = [uid for uid in UNITID_MAP if uid not in found_ids]
    if missing_ids:
        missing_names = ', '.join(f'{UNITID_MAP[u]} ({u})' for u in missing_ids)
        raise ValueError(
            f'Export validation failed for {Path(source_path).name}: '
            f'{len(missing_ids)} of {len(UNITID_MAP)} institutions produced no '
            f'qualifying rows. Missing: {missing_names}. This usually means the '
            f'source is truncated or incomplete — re-export / re-extract the '
            f'C-table and try again.')

    return g[['Year', 'INSTNM', 'CIPCODE', 'CTOTALT', 'AWLEVEL', 'Type']]


def build_aggregated(raw_df, cip_df):
    """Roll RawData up to Year x Level x CIP with labels and % of total."""
    agg = (raw_df.groupby(['Year', 'Type', 'CIPCODE'], as_index=False)['CTOTALT']
                 .sum()
                 .rename(columns={'Year':'year','Type':'level',
                                  'CIPCODE':'cip','CTOTALT':'grads'}))

    cip_ints = [int(c) for c in cip_df['CIP Code']]
    years    = sorted(raw_df['Year'].unique())
    levels   = ['Associate', 'Bachelor', 'Graduate']

    full = pd.MultiIndex.from_product([years, levels, cip_ints],
                                      names=['year', 'level', 'cip'])
    agg = (agg.set_index(['year','level','cip'])
              .reindex(full, fill_value=0)
              .reset_index())

    lookup = cip_df.copy()
    lookup['cip'] = lookup['CIP Code'].astype(int)
    lookup = lookup.rename(columns={'Field':'field',
                                    'Monitoring Program Classification':'Classification'})
    agg = agg.merge(lookup[['cip','field','Classification']], on='cip', how='left')

    totals = agg.groupby(['year','level'])['grads'].transform('sum')
    agg['grads_pct_tot'] = (agg['grads'] / totals).where(totals > 0, 0)
    return agg[['year','level','cip','field','grads','grads_pct_tot','Classification']]


# ============================================================================
# I/O
# ============================================================================

def read_existing(path):
    """Read existing Edu_2.xlsx. About sheet has metadata + embedded CIP table."""
    wb = load_workbook(path, data_only=True)
    ws = wb['About']

    metadata_rows, cip_rows = [], []
    in_cip_table = False
    for r in range(1, ws.max_row + 1):
        a = ws.cell(row=r, column=1).value
        b = ws.cell(row=r, column=2).value
        c = ws.cell(row=r, column=3).value
        if not in_cip_table:
            if a == 'CIP Code':
                in_cip_table = True
                continue
            if a is not None:
                metadata_rows.append((a, b))
        else:
            if a is not None:
                cip_rows.append((str(a), b, c))

    about_meta = pd.DataFrame(metadata_rows, columns=['Field', 'Value'])
    cip_df = pd.DataFrame(cip_rows,
                          columns=['CIP Code', 'Field', 'Monitoring Program Classification'])
    raw_df = pd.read_excel(path, sheet_name='RawData')
    return about_meta, cip_df, raw_df


def write_output(out_path, about_meta, cip_df, raw_df, agg_df):
    """Write Edu_2 output file in the current format."""
    pivot = (agg_df.pivot_table(index='Classification', columns='year',
                                values='grads', aggfunc='sum', fill_value=0)
                   .sort_index())
    pivot['Grand Total'] = pivot.sum(axis=1)

    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        pd.DataFrame().to_excel(writer, sheet_name='About', index=False)
        raw_df.to_excel(writer, sheet_name='RawData', index=False)
        agg_df.to_excel(writer, sheet_name='AggregatedData', index=False)

        wb = writer.book
        bold = Font(bold=True)

        # ---- About sheet ----
        ws = wb['About']
        for c in range(1, 5):
            ws.cell(row=1, column=c).value = None

        r = 1
        for _, row in about_meta.iterrows():
            ws.cell(row=r, column=1, value=row['Field']).font = bold
            ws.cell(row=r, column=2, value=row['Value'])
            r += 1
        r += 1  # blank row
        for j, h in enumerate(['CIP Code', 'Field', 'Monitoring Program Classification']):
            ws.cell(row=r, column=j+1, value=h).font = bold
        r += 1
        for _, row in cip_df.iterrows():
            ws.cell(row=r, column=1, value=str(row['CIP Code']).zfill(2))
            ws.cell(row=r, column=2, value=row['Field'])
            ws.cell(row=r, column=3, value=row['Monitoring Program Classification'])
            r += 1

        # ---- AggregatedData cip -> zero-padded strings ----
        ws = wb['AggregatedData']
        for r in range(2, ws.max_row + 1):
            val = ws.cell(row=r, column=3).value
            if isinstance(val, (int, float)):
                ws.cell(row=r, column=3, value=str(int(val)).zfill(2))

        # ---- AggregatedData pivot (col I onwards) ----
        col0 = 9
        ws.cell(row=1, column=col0, value='Sum of grads').font = Font(bold=True, italic=True)
        ws.cell(row=2, column=col0, value='Row Labels').font = bold
        for j, year in enumerate(pivot.columns):
            v = int(year) if year != 'Grand Total' else year
            ws.cell(row=2, column=col0+1+j, value=v).font = bold
        for i, cls in enumerate(pivot.index):
            ws.cell(row=3+i, column=col0, value=cls)
            for j, year in enumerate(pivot.columns):
                ws.cell(row=3+i, column=col0+1+j, value=int(pivot.loc[cls, year]))


# ============================================================================
# MAIN
# ============================================================================
IPEDS_FOLDER = r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\IPEDS'       # where to look for Cyyyy_A.csv files
def main(existing_xlsx='Edu_2.xlsx',
         new_years=(
            (IPEDS_FOLDER + r'\IPEDS_2020-21_Final\IPEDS202021.accdb', 2020)
            ,(IPEDS_FOLDER + r'\IPEDS_2021-22_Final\IPEDS202122.accdb', 2021)
            ,(IPEDS_FOLDER + r'\IPEDS_2022-23_Final\IPEDS202223.accdb', 2022)
            ,(IPEDS_FOLDER + r'\IPEDS_2023-24_Final\IPEDS202324.accdb', 2023)
            ,(IPEDS_FOLDER + r'\IPEDS_2024-25_Provisional\IPEDS202425.accdb', 2024)
            ),
         output_xlsx='Edu_2_updated.xlsx'):

    about_meta, cip_df, existing_raw = read_existing(existing_xlsx)

    new_dfs = []
    for csv_path, ipeds_year in new_years:
        start_time=time.time()
        if not Path(csv_path).exists():
            print(f'  SKIP: {csv_path} not found')
            continue
        edu2_year = ipeds_year + YEAR_OFFSET
        if edu2_year in existing_raw['Year'].values:
            print(f'  SKIP: Year {edu2_year} already in RawData')
            continue
        print('\n\nSchool year: ', f'{ipeds_year}-{edu2_year}')
        print(f'  Processing {csv_path} -> Edu_2 Year {edu2_year}')
        new_dfs.append(build_rawdata_for_year(csv_path, ipeds_year))
        print(f"Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---")

    combined_raw = (pd.concat([existing_raw] + new_dfs, ignore_index=True)
                    if new_dfs else existing_raw.copy())

    max_year = combined_raw['Year'].max()
    about_meta.loc[about_meta['Field'].str.lower().str.startswith('year'), 'Value'] = f'2005-{max_year}'

    agg_df = build_aggregated(combined_raw, cip_df)
    write_output(output_xlsx, about_meta, cip_df, combined_raw, agg_df)
    print(f'\nWrote {output_xlsx} - {combined_raw["Year"].nunique()} years, ', f'{len(combined_raw)} raw rows, {len(agg_df)} aggregated rows\n')


if __name__ == '__main__':
    main()
    
