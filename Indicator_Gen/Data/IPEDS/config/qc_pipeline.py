"""
Edu_2 Pipeline QC — Validation Report
=====================================

Validates that edu2_pipeline.py produces the same numbers as the published
Edu_2.xlsx RawData, for any IPEDS C_yyyy_A.csv files available locally.

USAGE:
    Put any number of IPEDS C-table CSV exports in ./ipeds_data/ (or change
    IPEDS_FOLDER below), then:

        python qc_pipeline.py

    Works with whatever subset of years you have — missing years are simply
    skipped. Years that don't yet exist in the published file (e.g. 2023, 2024)
    are reported as "new-year generation, no benchmark available".

WHAT IT DOES:
    For each Cyyyy_A.csv found, runs the same pipeline code that produces the
    production indicator (imported from edu2_pipeline.py) and compares each
    (Institution × CIP × AwardLevel) cell against the published Edu_2.xlsx
    RawData row for the corresponding Edu_2 year (= IPEDS year + 1).

    Reports per-year match counts and a final PASS / FAIL.
"""

import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime
import os

os.chdir(Path(__file__).parent)


# Import the actual production pipeline functions (not duplicated here)
from edu2_pipeline import build_rawdata_for_year, YEAR_OFFSET


# ============================================================================
# CONFIG
# ============================================================================

IPEDS_FOLDER = r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\IPEDS\edu2'       # where to look for Cyyyy_A.csv files
PUBLISHED_FILE = 'Edu_2.xlsx'       # ground truth
MISMATCH_PREVIEW_ROWS = 15          # how many mismatches to show if any year fails


# ============================================================================
# HELPERS
# ============================================================================

def scan_folder(folder):
    """Return [(path, ipeds_year), ...] for every Cyyyy_A.csv in folder."""
    folder = Path(folder)
    if not folder.exists():
        return []
    found = []
    for p in sorted(folder.glob('C*_A.csv')):
        m = re.match(r'C(\d{4})_A\.csv$', p.name)
        if m:
            found.append((p, int(m.group(1))))
    return found


def compare_year(pipeline_df, published_raw, edu2_year):
    """Compare pipeline output to published RawData for one Edu_2 year."""
    p = pipeline_df.copy()
    e = published_raw[published_raw['Year'] == edu2_year].copy()

    # Institution name casing varies across years in the published file
    # (UPPERCASE in early years, Title Case later). Compare case-insensitively.
    p['_k'] = p['INSTNM'].str.lower()
    e['_k'] = e['INSTNM'].str.lower()

    # CIPCODE type differs: published file stores zero-padded strings ('01'),
    # pipeline outputs integers (1). Normalize both to int before merging,
    # otherwise '01' != 1 and nothing joins (cell counts match but 0 matches).
    p['CIPCODE'] = p['CIPCODE'].astype(int)
    e['CIPCODE'] = e['CIPCODE'].astype(int)

    merged = e.merge(p, on=['Year', '_k', 'CIPCODE', 'AWLEVEL'],
                     suffixes=('_pub', '_pipe'), how='outer', indicator=True)

    both = merged[merged['_merge'] == 'both']
    matching   = int((both['CTOTALT_pub'] == both['CTOTALT_pipe']).sum())
    mismatches = both[both['CTOTALT_pub'] != both['CTOTALT_pipe']]
    only_pub   = int((merged['_merge'] == 'left_only').sum())
    only_pipe  = int((merged['_merge'] == 'right_only').sum())

    return {
        'edu2_year':  edu2_year,
        'pub_cells':  len(e),
        'pipe_cells': len(p),
        'in_both':    len(both),
        'matching':   matching,
        'only_pub':   only_pub,
        'only_pipe':  only_pipe,
        'mismatches': mismatches,
        'pass':       matching == len(both) and only_pub == 0 and only_pipe == 0,
    }


# ============================================================================
# REPORT
# ============================================================================

def hr(width=72, ch='='):
    print(ch * width)


def main():
    width = 72
    print()
    hr()
    print('  Edu_2 Pipeline QC — Validation Report')
    hr()
    print(f'  Ground truth file:  {PUBLISHED_FILE}')
    print( '  Pipeline module:    edu2_pipeline.py')
    print(f'  Source folder:      {IPEDS_FOLDER}/')
    print(f'  Run timestamp:      {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    hr()
    print()

    # Discover available IPEDS files
    files = scan_folder(IPEDS_FOLDER)
    if not files:
        print(f'  ERROR: no Cyyyy_A.csv files found in ./{IPEDS_FOLDER}/')
        print( '  Add exports there and rerun. Expected filename pattern: C2023_A.csv')
        sys.exit(1)

    print(f'  Found {len(files)} IPEDS file(s):')
    for path, year in files:
        print(f'    {path.name}  (IPEDS year {year})')
    print()

    # Load published ground truth once
    published_raw = pd.read_excel(PUBLISHED_FILE, sheet_name='RawData')
    published_years = set(published_raw['Year'].unique().tolist())

    # Run each year through the pipeline and compare
    qc_results, new_year_results = [], []
    for path, ipeds_year in files:
        edu2_year = ipeds_year + YEAR_OFFSET
        pipeline_df = build_rawdata_for_year(str(path), ipeds_year)

        if edu2_year in published_years:
            result = compare_year(pipeline_df, published_raw, edu2_year)
            result['source'] = path.name
            qc_results.append(result)
        else:
            new_year_results.append({
                'source':    path.name,
                'edu2_year': edu2_year,
                'pipe_cells': len(pipeline_df),
            })

    # ---- Per-year QC detail ----
    hr(width, '-')
    print('  QC AGAINST PUBLISHED VALUES')
    hr(width, '-')

    if not qc_results:
        print('  No overlap with published years — nothing to validate against.')
        print(f'  To QC the pipeline, add a CSV for any IPEDS year between'
              f' {min(published_years)-YEAR_OFFSET} and'
              f' {max(published_years)-YEAR_OFFSET}.')
    else:
        for r in qc_results:
            status = '✓ PASS' if r['pass'] else '✗ FAIL'
            print()
            print(f'  {r["source"]}  →  Edu_2 Year {r["edu2_year"]}   [{status}]')
            print(f'    Published cells:    {r["pub_cells"]:>5}')
            print(f'    Pipeline cells:     {r["pipe_cells"]:>5}')
            print(f'    Exact matches:      {r["matching"]:>5} / {r["in_both"]}')
            if r['only_pub'] or r['only_pipe']:
                print(f'    Cells only in published:  {r["only_pub"]}')
                print(f'    Cells only in pipeline:   {r["only_pipe"]}')
            if not r['pass'] and len(r['mismatches']):
                print(f'\n    First {MISMATCH_PREVIEW_ROWS} mismatched cells:')
                m = r['mismatches'].head(MISMATCH_PREVIEW_ROWS).copy()
                m['inst'] = m['INSTNM_pub'].fillna(m['INSTNM_pipe'])
                cols = ['inst', 'CIPCODE', 'AWLEVEL', 'CTOTALT_pub', 'CTOTALT_pipe']
                for _, row in m[cols].iterrows():
                    print(f'      {row["inst"]:<42}  '
                          f'CIP {row["CIPCODE"]:>2}  AW {row["AWLEVEL"]:>2}  '
                          f'pub={int(row["CTOTALT_pub"]):>4}  pipe={int(row["CTOTALT_pipe"]):>4}')

    # ---- New years (no benchmark) ----
    if new_year_results:
        print()
        hr(width, '-')
        print('  NEW YEARS (no published benchmark — pipeline output for review)')
        hr(width, '-')
        for nyr in new_year_results:
            print(f'  {nyr["source"]}  →  Edu_2 Year {nyr["edu2_year"]}: '
                  f'{nyr["pipe_cells"]} cells generated')

    # ---- Final summary ----
    print()
    hr()
    print('  SUMMARY')
    hr()
    if qc_results:
        passed = sum(1 for r in qc_results if r['pass'])
        total_cells   = sum(r['in_both']  for r in qc_results)
        total_matches = sum(r['matching'] for r in qc_results)
        print(f'  Years validated against published data:   {len(qc_results)}')
        print(f'  Years passed:                             {passed} / {len(qc_results)}')
        print(f'  Total cells checked:                      {total_cells}')
        print(f'  Total cells matching exactly:             {total_matches} / {total_cells}')
        if new_year_results:
            print(f'  New years generated (no benchmark):       {len(new_year_results)}')
        print()
        if passed == len(qc_results):
            print('  RESULT: ✓ PIPELINE VALIDATED')
        else:
            print(f'  RESULT: ✗ {len(qc_results) - passed} YEAR(S) FAILED VALIDATION')
    else:
        print('  No QC performed (no overlap years available).')
        if new_year_results:
            print(f'  New years generated: {len(new_year_results)}')
    hr()
    print()


if __name__ == '__main__':
    main()
