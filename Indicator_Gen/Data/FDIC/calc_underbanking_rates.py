

'''
Redownload the latest year available:  https://household-survey.fdic.gov/custom-data
"First Select Topic" = Bank Account Ownership
"Then Select Variable" = Unbanked and underbanked

Download data for both the Sacramento MSA and the state of California
Copy downloads over to I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\FDIC

Then, run python file in terminal (set EXPORT=True if ready to export data)

Banking access
    Households without full banking access (unbanked + underbanked)
    Primary panel: Sacramento MSA stacked-bar time series (FDIC NSUUH)
    Supplementary: California state race breakdown (FDIC NSUUH)
'''



# Setup --------------------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
from IPython.display import display
import re
import csv
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent/'config'))
import functions as func


def parse_fdic_single_year(path):
    """Parse one FDIC single-year MSA CSV → (year, unbanked, underbanked)."""
    with open(path) as f:
        reader = list(csv.reader(f))
    title = reader[0][0] if reader and reader[0] else ''
    year_match = re.search(r',\s*(\d{4})\s+by', title)
    if not year_match:
        return None
    year = int(year_match.group(1))
    for row in reader:
        if row and row[0].strip() == 'All Households' and len(row) >= 5:
            try:
                return year, float(row[3]) / 100, float(row[4]) / 100
            except (ValueError, IndexError):
                return None
    return None


def parse_fdic_multiyear(path):
    """Parse the multi-year unbanked-only Sac MSA CSV → {year: unbanked_pct}."""
    with open(path) as f:
        reader = list(csv.reader(f))
    if len(reader) < 5:
        return {}
    # Year row is row 4 (index 3); each year occupies 4 columns
    year_row = reader[3]
    years = [(int(c.strip()), i) for i, c in enumerate(year_row)
             if c.strip().isdigit() and len(c.strip()) == 4]
    data_row = next((row for row in reader if row and row[0].strip() == 'All Households'), None)
    if not data_row:
        return {}
    result = {}
    for year, col in years:
        try:
            v = data_row[col + 2].strip()
            if v and v != 'NA':
                result[year] = float(v) / 100
        except (ValueError, IndexError):
            continue
    return result


def parse_fdic_ca_race(path):
    """Parse the Race/Ethnicity section of a CA state FDIC CSV → DataFrame."""
    mapping = {
        'Asian': 'Asian', 'Black': 'Black', 'Hispanic': 'Hispanic',
        'American Indian or Alaska Native': 'Native',
        'Two or More Races': 'Other', 'White': 'White',
    }
    rows = {}
    with open(path) as f:
        in_race = False
        for row in csv.reader(f):
            if not row:
                continue
            cell = row[0].strip()
            if 'Race/Ethnicity' in cell:
                in_race = True
                continue
            if not in_race:
                continue
            if '(PCT)' in cell:
                in_race = False
                continue
            display = mapping.get(cell)
            if display is None:
                continue
            try:
                unb, und = row[3].strip(), row[4].strip()
                if unb == 'NA' or und == 'NA':
                    rows[display] = None
                else:
                    rows[display] = [float(unb)/100, float(und)/100, (float(unb) + float(und)) / 100]
            except (ValueError, IndexError):
                rows[display] = None
    return pd.DataFrame([{'race': r, 'unbanked_pct': rows.get(r)[0], 'underbanked_pct': rows.get(r)[1], 'no_full_access_pct': rows.get(r)[2]} for r in RACE_ORDER])


def proc_fdic():

    print('\n\nFDIC Underbanking Rates')
    """Assemble Sacramento MSA time series + CA state race breakdown."""
    timeseries = {}

    # Multi-year file provides unbanked across years
    for path in SOURCE_DIR.glob('*Sacramento*MultiYear*.csv'): ## TODO: What is this multi year file?
        for year, unb in parse_fdic_multiyear(path).items():
            timeseries.setdefault(year, {})['unbanked_pct'] = unb

    # Single-year files provide unbanked + underbanked
    for path in SOURCE_DIR.glob('*Sacramento*.csv'):
        if 'MultiYear' in path.name:
            continue
        parsed = parse_fdic_single_year(path)
        if parsed:
            year, unb, und = parsed
            timeseries.setdefault(year, {})['unbanked_pct'] = unb
            timeseries[year]['underbanked_pct'] = und

    if not timeseries:
        print('\n⚠ No FDIC Sacramento MSA files found in source_files/')
        print('   Expected: *Sacramento*MultiYear*.csv and/or *Sacramento*{YEAR}*.csv')
        ts_df = None
    else:
        ts_df = pd.DataFrame([
            {'year': y, 'unbanked_pct': d.get('unbanked_pct'),
             'underbanked_pct': d.get('underbanked_pct')}
            for y, d in sorted(timeseries.items())
        ])
        ts_df['no_full_access_pct'] = ts_df['unbanked_pct'] + ts_df['underbanked_pct']

    # CA state race breakdown — auto-parse from native CSV
    race_df = None
    ca_files = list(SOURCE_DIR.glob('*California*.csv'))
    if ca_files:
        latest = sorted(ca_files,
                       key=lambda p: (re.search(r'(\d{4})', p.name) or
                                      type('', (), {'group': lambda *_: '0000'})()).group(1))[-1]
        race_df = parse_fdic_ca_race(latest)
        print(f'  Parsed CA race breakdown from: {latest.name}')
    else:
        print('\n⚠ No FDIC California state file found in source_files/')
        print('   Expected: *California*.csv')

    ts_df   = ts_df  .rename(columns={'year':'Year', 'unbanked_pct':'Unbanked (%)', 'underbanked_pct':'Underbanked (%)', 'no_full_access_pct':'No Full Access (%)'})
    race_df = race_df.rename(columns={'race':'Race/Ethnicity', 'unbanked_pct':'Unbanked (%)', 'underbanked_pct':'Underbanked (%)', 'no_full_access_pct':'No Full Access (%)'})
    race_df['Year'] = ts_df['Year'].max()
    race_df = race_df.set_index('Year').reset_index()

    return ts_df, race_df





# Main --------------------------------------------------------------------------------------------------------------------------------------------------------------------


EXPORT=False

SOURCE_DIR = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\FDIC')
PATH_SERVER = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data')
PATH_SP = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\Economy\Income\Income_8 Underbanked')

RACE_ORDER = ['Asian', 'Black', 'Hispanic', 'White']


INDICATOR='Income_8'
GEO='Sacramento 4-County MSA'


if __name__ == '__main__':

    df_msa, df_ca = proc_fdic()
    if df_msa is None or df_ca is None:
        print('\nERROR: Metric 3 data incomplete. Place FDIC CSVs in source_files/ and re-run.')
        sys.exit(1)
    
    
    if EXPORT:
        
        params = {
            'sample': 'FDIC'
            , 'indicator': INDICATOR
            , 'geo': GEO
            , 'start_year': df_msa['Year'].min()
            , 'end_year': df_msa['Year'].max()
            , 'estimate': None
            , 'moe_thresh': None
        }

        df_about = func.write_about(params)
        print("About page documentation table:")
        display(df_about)


        paths = [PATH_SP, PATH_SERVER]
        workbook_name = f'{INDICATOR} FDIC.xlsx'

        for path_ in paths:
            file_out = path_ / workbook_name
            with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
                df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                df_msa  .to_excel(writer, index=False, sheet_name='MSA'      )
                df_ca   .to_excel(writer, index=False, sheet_name='Statewide')
            print("Exported: ", path_)
