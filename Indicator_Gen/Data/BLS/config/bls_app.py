"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    BLS DATA PIPELINE STREAMLIT GUI                        ║
║                                                                           ║
║  Similar to Census GUI - Step-based workflow with session state          ║
║  Replaces: 1__request_BLS.py + 2__process_BLS.py                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

SETUP INSTRUCTIONS
══════════════════════════════════════════════════════════════════════════════

1. Place this file in: Data/BLS/config/

2. Ensure these files exist:
   ✓ bls.yaml               (configuration)
   ✓ bls.xlsx               (data configuration)
   ✓ config/pre.py          (parameter functions)
   ✓ config/get.py          (API request functions)
   ✓ config/post.py         (processing functions)
   ✓ ../config/area_codes.xlsx (geographic codes)

3. Run with:
   streamlit run bls_gui.py

4. Set your API key in: config/api_key.txt

══════════════════════════════════════════════════════════════════════════════
"""
import requests
import json
import functools as ft
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import yaml
import pre
import get
import post
# ═══════════════════════════════════════════════════════════════════════════
# SETUP PATHS & IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

path_code = Path(__file__).parent
path_config = path_code
path_config0 = path_code.parent.parent / 'config'


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIG
# ═══════════════════════════════════════════════════════════════════════════

FILE_API = path_config / 'api_key.txt'
FILE_RUNS = path_config / 'runs'
FILE_RUNS.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="📊 BLS Data Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

if 'step' not in st.session_state:
    st.session_state.step = 'configure'
    st.session_state.df_raw = None
    st.session_state.df_processed = None
    st.session_state.params = None
    st.session_state.timestamp = None
    st.session_state.df_series_area = None

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def load_yaml_config():
    """Load BLS YAML configuration"""
    path_yaml = path_config / 'bls.yaml'
    try:
        with open(path_yaml, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error(f"❌ Config file not found: {path_yaml}")
        st.stop()

def load_api_key():
    """Load BLS API key"""
    try:
        with open(FILE_API, 'r') as f:
            key = f.read().strip()
        if not key:
            st.error("❌ API key file is empty!")
            st.stop()
        return key
    except FileNotFoundError:
        st.error(f"❌ API key file not found: {FILE_API}")
        st.info("Create a file with your BLS API key at:\n" + str(FILE_API))
        st.stop()

def save_run_log(params):
    """Save run configuration to file"""
    indicator = params['Indicator']
    file_run = FILE_RUNS / f'{indicator}.txt'
    
    years_str = ', '.join([str(y) for y in params['Years']])
    
    with open(file_run, 'w') as f:
        f.write(f"Project: {params['Project']}\n")
        f.write(f"Indicator: {indicator}\n")
        f.write(f"Survey: {params['Survey']}\n")
        f.write(f"Geography: {params['Geography']}\n")
        f.write(f"Data Type: {params['Data Type']}\n")
        f.write(f"Employer Size: {params['Size Code']}\n")
        f.write(f"Ownership Type: {params['Owner Code']}\n")
        f.write(f"Measure Type: {params['Measure Type']}\n")
        f.write(f"Seasonal Adjustment: {'Yes' if params['Seasonal Code'] == 'S' else 'No'}\n")
        f.write(f"Years Imported: {years_str}\n")

def read_area_local(indicator, survey):
    df = pd.read_excel(path_config / 'bls.xlsx', sheet_name='area_codes', dtype=str)
    df.columns = df.columns.str.strip()

    df = df[df['Survey'] == survey]
    df = df[df['Indicator Name'].str.contains(indicator, na=False)]
    df = df[df['Include'] == 'Yes']

    return df.reset_index(drop=True)

def read_industries_local(indicator, survey):
    df = pd.read_excel(path_config / 'bls.xlsx', sheet_name='industry_codes', dtype=str)
    df.columns = df.columns.str.strip()

    df = df[df['Survey'] == survey]
    df = df[df['Include'] == 'Yes']
    df = df[df['Indicator Name'].str.contains(indicator, na=False)]

    return df


def get_bls_code(sheet_name, text_col, code_col, search_text):
    """Helper to map UI text labels back to BLS numeric codes."""
    try:
        # Load the specific code sheet from your CSVs
        df = pd.read_csv(f"bls.xlsx - {sheet_name}.csv", dtype=str)
        match = df[df[text_col].str.strip() == str(search_text).strip()]
        return match.iloc[0][code_col] if not match.empty else ""
    except:
        return ""

def construct_series_ids_local(params, yaml_config):
    survey = params['Survey']
    geography = params['Geography']
    seasonal = params['Seasonal Code']
    indicator = params['Indicator']

    # 1. Map UI selections to numeric API codes
    dt_code = get_bls_code('datatype_codes', 'data_type_text', 'data_type_code', params.get('Data Type'))
    ms_code = get_bls_code('measure_codes', 'measure_type_text', 'measure_code', params.get('Measure Type'))
    sz_code = get_bls_code('size_codes', 'size_code_text', 'size_code', params.get('Size Code'))
    ow_code = get_bls_code('owner_codes', 'owner_code_text', 'owner_code', params.get('Owner Code'))

    # 2. Get Geographies (Filter by survey and type)
    df_area = read_area_local(indicator, survey)
    if geography == 'MSA':
        df_area = df_area[df_area['area_type_code'].isin(['B', 'M'])]
    elif geography == 'Counties':
        df_area = df_area[df_area['area_type_code'] == 'F']
    
    # 3. Get Industries
    df_ind = read_industries_local(indicator, survey)
    sectors = df_ind['industry_code'].astype(str).tolist()

    series_dict = {}

    # 4. Construct IDs with strict length requirements
    if survey == 'CE': # National (13 chars)
        series_dict["National"] = [f"CE{seasonal}{s.zfill(8)}{dt_code.zfill(2)}" for s in sectors]

    elif not df_area.empty:
        for _, row in df_area.iterrows():
            area = str(row['area_code'])
            name = row['area_text']
            
            if survey == 'SM': # State/Area (20 chars)
                # Note: SM needs a 2-digit state prefix. 
                # If area is 5 digits (MSA), we prefix with state (e.g., 39 for OH)
                state_prefix = "39" if "OH" in indicator else "06" 
                series = [f"SM{seasonal}{state_prefix}{area.zfill(5)}{s.zfill(8)}{dt_code.zfill(2)}" for s in sectors]
            
            elif survey == 'EN': # QCEW (17 chars)
                series = [f"EN{seasonal}{area.zfill(5)}{dt_code}{sz_code}{ow_code}{s.ljust(6, '0')[:6]}" for s in sectors]
            
            elif survey == 'LA': # LAUS (20 chars)
                series = [f"LA{seasonal}{area.zfill(15)}{ms_code.zfill(2)}"]
            
            series_dict[name] = series

    return series_dict

# ═══════════════════════════════════════════════════════════════════════════
# CATALOG VALIDATION - BLS Series Flat Files
# ═══════════════════════════════════════════════════════════════════════════

# Strategy:
#   1. Try to load from local parquet files in catalog/ (committed to repo).
#      These are generated once by running download_bls_catalogs.py locally.
#   2. If the parquet file is missing, fall back to downloading from BLS.
#      This keeps local dev working without the catalog/ folder pre-populated.
#   3. If both fail, return {} and the UI falls back to yaml year defaults.
#
# To generate the catalog/ files: run download_bls_catalogs.py locally,
# then commit the catalog/ folder to your repo so Streamlit has them.

CATALOG_URLS = {
    'SM': 'https://download.bls.gov/pub/time.series/sm/sm.series',
    'CE': 'https://download.bls.gov/pub/time.series/ce/ce.series',
    'EN': 'https://download.bls.gov/pub/time.series/en/en.series',
    'LA': 'https://download.bls.gov/pub/time.series/la/la.series',
}

CATALOG_DIR = path_code / 'catalog'


def _df_to_catalog_dict(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    df['series_id']  = df['series_id'].str.strip()
    df['begin_year'] = pd.to_numeric(df['begin_year'], errors='coerce')
    df['end_year']   = pd.to_numeric(df['end_year'],   errors='coerce')
    df = df.dropna(subset=['begin_year', 'end_year'])
    return dict(zip(
        df['series_id'],
        zip(df['begin_year'].astype(int), df['end_year'].astype(int))
    ))


@st.cache_data(show_spinner=False, ttl=86400)
def load_series_catalog(survey):
    """
    Load the BLS series catalog for a given survey.
    Tries local parquet first (fast, works on Streamlit Cloud),
    then falls back to downloading from BLS (works locally without catalog/).
    Returns a dict: series_id -> (begin_year, end_year).
    Returns {} if both sources fail — callers must handle this gracefully.
    """
    # ── 1. Try local parquet ──────────────────────────────────────────────
    local_path = CATALOG_DIR / f'{survey.lower()}_series.parquet'
    if local_path.exists():
        try:
            df = pd.read_parquet(local_path)
            catalog = _df_to_catalog_dict(df)
            if catalog:
                return catalog
        except Exception:
            pass  # corrupt file — fall through to network

    # ── 2. Try network download ───────────────────────────────────────────
    url = CATALOG_URLS.get(survey)
    if not url:
        return {}
    try:
        import requests as _requests
        from io import StringIO
        r = _requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text), sep='\t', dtype=str)
        catalog = _df_to_catalog_dict(df)
        # Opportunistically cache to disk so next load is instant
        try:
            CATALOG_DIR.mkdir(exist_ok=True)
            df_save = pd.DataFrame([
                {'series_id': k, 'begin_year': v[0], 'end_year': v[1]}
                for k, v in catalog.items()
            ])
            df_save.to_parquet(local_path, index=False)
        except Exception:
            pass  # non-fatal — we still have the catalog in memory
        return catalog
    except Exception as e:
        # Store the real reason so get_catalog_year_range can surface it
        load_series_catalog._last_error = str(e)
        return {}


def get_valid_year_range_from_catalog(series_ids, catalog):
    """
    Given a list of series IDs and a catalog dict, return the tightest
    valid year window that covers ALL requested series — i.e. the latest
    begin_year and earliest end_year across all series.

    Returns (begin_year, end_year, coverage_info) where coverage_info is a
    list of dicts describing each series' availability for display in the UI.
    """
    coverage = []
    found_begin = []
    found_end   = []

    for sid in series_ids:
        if sid in catalog:
            b, e = catalog[sid]
            found_begin.append(b)
            found_end.append(e)
            coverage.append({'series_id': sid, 'begin_year': b, 'end_year': e, 'found': True})
        else:
            coverage.append({'series_id': sid, 'begin_year': None, 'end_year': None, 'found': False})

    if not found_begin:
        return None, None, coverage

    # The window where ALL series have data is [max(begin), min(end)]
    valid_begin = int(max(found_begin))
    valid_end   = int(min(found_end))

    return valid_begin, valid_end, coverage


def build_preview_series_ids(survey, geography, seasonal_code, indicator, yaml_config):
    """
    Build the series IDs for the current config so we can look them up in
    the catalog — without needing codes from the xlsx (we filter by pattern).
    This is a lightweight version that constructs just enough to do the lookup.
    We use the read_area_local / read_industries_local helpers already in this file.
    """
    try:
        df_area = read_area_local(indicator, survey)
        if geography == 'MSA':
            df_area = df_area[df_area['area_type_code'].isin(['B', 'M'])]
        elif geography == 'Counties':
            df_area = df_area[df_area['area_type_code'] == 'F']

        df_ind = read_industries_local(indicator, survey)
        sectors = df_ind['industry_code'].astype(str).str.strip().tolist()

        series_ids = []

        if survey == 'CE':
            # CE series IDs are prefix + seasonal + industry(8) + datatype(2)
            # We don't know datatype yet, so just check the first sector with wildcard
            # Instead, return a representative list using all datatypes 01-08
            for s in sectors:
                for dt in ['01','02','03','06','11']:
                    series_ids.append(f"CE{seasonal_code}{s.zfill(8)}{dt}")

        elif survey == 'SM':
            for _, row in df_area.iterrows():
                area = str(row['area_code']).strip().zfill(5)
                state = str(row.get('State FIPS', '')).strip().zfill(2)
                for s in sectors:
                    for dt in ['01','02','03','06','11']:
                        series_ids.append(f"SM{seasonal_code}{state}{area}{s.zfill(8)}{dt}")

        elif survey == 'EN':
            for _, row in df_area.iterrows():
                area = str(row['area_code']).strip().zfill(5)
                for s in sectors:
                    series_ids.append(f"EN{seasonal_code}{area}10{s.ljust(6,'0')[:6]}")

        elif survey == 'LA':
            for _, row in df_area.iterrows():
                area = str(row['area_code']).strip()
                for ms in ['03','04','05','06']:
                    series_ids.append(f"LA{seasonal_code}{area}{ms}")

        return series_ids

    except Exception:
        return []


def get_catalog_year_range(survey, geography, seasonal_code, indicator, yaml_config):
    """
    Top-level function called from the UI. Returns (begin_year, end_year, status_msg).
    Uses cached catalog so it's fast after first load.
    """
    catalog = load_series_catalog(survey)
    if not catalog:
        err = getattr(load_series_catalog, '_last_error', None)
        if err:
            if 'resolve' in err.lower() or 'name resolution' in err.lower() or 'connection' in err.lower():
                detail = "network unreachable — commit the catalog/ folder to your repo (see download_bls_catalogs.py)"
            else:
                detail = err
            return None, None, f"⚠️ BLS catalog unavailable ({detail}) — using default year range"
        local_path = CATALOG_DIR / f'{survey.lower()}_series.parquet'
        return None, None, f"⚠️ Catalog file not found ({local_path.name}) — run download_bls_catalogs.py locally then commit catalog/ to your repo"

    preview_ids = build_preview_series_ids(survey, geography, seasonal_code, indicator, yaml_config)
    if not preview_ids:
        return None, None, "⚠️ Could not construct series IDs for catalog lookup"

    # Only look up IDs that are actually in the catalog
    valid_begin, valid_end, coverage = get_valid_year_range_from_catalog(preview_ids, catalog)

    found_count = sum(1 for c in coverage if c['found'])
    total_count = len(coverage)

    if valid_begin is None:
        return None, None, f"⚠️ None of the {total_count} series IDs found in BLS catalog"

    if valid_end < valid_begin:
        return None, None, f"⚠️ No overlapping year range found across series"

    status = f"✅ Catalog loaded — {found_count}/{total_count} series found · Valid years: **{valid_begin}–{valid_end}**"
    return valid_begin, valid_end, status


def get_all_valid_years_by_datatype(survey, geography, seasonal_code, indicator, yaml_config):
    """
    Returns a dict mapping each data_type_code suffix -> (begin_year, end_year)
    so the UI can show per-data-type availability.
    """
    catalog = load_series_catalog(survey)
    if not catalog:
        return {}

    try:
        df_area = read_area_local(indicator, survey)
        if geography == 'MSA':
            df_area = df_area[df_area['area_type_code'].isin(['B', 'M'])]
        elif geography == 'Counties':
            df_area = df_area[df_area['area_type_code'] == 'F']

        df_ind = read_industries_local(indicator, survey)
        sectors = df_ind['industry_code'].astype(str).str.strip().tolist()

        # Data type codes used by SM/CE
        dt_codes = {'01':'All Employees, in Thousands',
                    '02':'Average Weekly Hours of All Employees',
                    '03':'Average Hourly Earnings of All Employees, in Dollars',
                    '06':'Production or Nonsupervisory Employees, in Thousands',
                    '11':'Average Weekly Earnings of All Employees, in Dollars'}

        result = {}

        for dt_code, dt_label in dt_codes.items():
            series_for_dt = []

            if survey == 'CE':
                for s in sectors:
                    series_for_dt.append(f"CE{seasonal_code}{s.zfill(8)}{dt_code}")

            elif survey == 'SM':
                for _, row in df_area.iterrows():
                    area  = str(row['area_code']).strip().zfill(5)
                    state = str(row.get('State FIPS','')).strip().zfill(2)
                    for s in sectors:
                        series_for_dt.append(f"SM{seasonal_code}{state}{area}{s.zfill(8)}{dt_code}")

            b, e, _ = get_valid_year_range_from_catalog(series_for_dt, catalog)
            if b is not None and e >= b:
                result[dt_label] = (b, e)

        return result

    except Exception:
        return {}


def get_all_valid_years_by_measure(survey, geography, seasonal_code, indicator, yaml_config):
    """
    For LA survey: returns dict mapping measure label -> (begin_year, end_year)
    """
    catalog = load_series_catalog(survey)
    if not catalog:
        return {}

    try:
        df_area = read_area_local(indicator, survey)
        if geography == 'MSA':
            df_area = df_area[df_area['area_type_code'].isin(['B', 'M'])]
        elif geography == 'Counties':
            df_area = df_area[df_area['area_type_code'] == 'F']

        measure_codes = {
            '03': 'Unemployment Rate',
            '04': 'Unemployment',
            '05': 'Employment',
            '06': 'Labor Force',
        }

        result = {}
        for ms_code, ms_label in measure_codes.items():
            series_for_ms = []
            for _, row in df_area.iterrows():
                area = str(row['area_code']).strip()
                series_for_ms.append(f"LA{seasonal_code}{area}{ms_code}")
            b, e, _ = get_valid_year_range_from_catalog(series_for_ms, catalog)
            if b is not None and e >= b:
                result[ms_label] = (b, e)

        return result

    except Exception:
        return {}


def get_data_local(api_key, params, yaml_config):
    series_dict = construct_series_ids_local(params, yaml_config)

    # Flatten series list
    all_series = []
    for v in series_dict.values():
        all_series.extend(v)

    if not all_series:
        raise ValueError("No valid series generated from configuration.")

    # Chunk into groups of 50
    chunks = [all_series[i:i+50] for i in range(0, len(all_series), 50)]

    year_start = min(params['Years'])
    year_end = max(params['Years'])

    results = []

    for chunk in chunks:
        url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        headers = {'Content-type': 'application/json'}

        payload = json.dumps({
            "seriesid": chunk,
            "startyear": year_start,
            "endyear": year_end,
            "registrationkey": api_key
        })

        response = requests.post(url, headers=headers, data=payload).json()

        for series in response.get('Results', {}).get('series', []):
            sid = series['seriesID']
            df = pd.DataFrame(series['data'])

            if df.empty:
                continue

            df['seriesID'] = sid
            results.append(df)

    if not results:
        raise ValueError("API returned no data.")

    df_final = pd.concat(results, ignore_index=True)
    return df_final

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def step_configure():
    """Configuration step - gather all parameters"""
    
    st.title("📊 BLS Data Pipeline - Configuration")
    st.markdown("Configure your BLS data request in the left panel →")
    
    yaml_config = load_yaml_config()
    
    # LEFT COLUMN: CONFIGURATION INPUTS
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown("---")
        
        # Step 1: Project
        st.subheader("1️⃣ Project")
        projects = yaml_config['Project']
        project = st.selectbox(
            "Select project:",
            projects,
            label_visibility="collapsed",
            key="select_project"
        )
        st.caption(f"Selected: **{project}**")
        
        # Step 2: Indicator
        st.subheader("2️⃣ Indicator")
        indicators = list(yaml_config['Indicators'][project].keys())
        indicator = st.selectbox(
            "Select indicator:",
            indicators,
            label_visibility="collapsed",
            key="select_indicator"
        )
        st.caption(f"Selected: **{indicator}**")
        
        indicator_config = yaml_config['Indicators'][project][indicator]
        
        # Step 3: Survey
        st.subheader("3️⃣ Survey")
        surveys = indicator_config['survey']
        if isinstance(surveys, list):
            survey = st.selectbox(
                "Select survey:",
                surveys,
                label_visibility="collapsed",
                key="select_survey"
            )
        else:
            survey = surveys
            st.info(f"📌 Fixed: **{survey}**")
        
        survey_config = yaml_config['Surveys'][survey]
        
        # Step 9: Seasonal Adjustment
        st.subheader("9️⃣ Seasonal Adjustment")
        seasonal_adj = st.radio(
            "Include seasonal adjustment?",
            ["Yes", "No"],
            horizontal=True,
            label_visibility="collapsed",
            key="select_seasonal"
        )
        seasonal_code = 'S' if seasonal_adj == 'Yes' else 'U'
        st.caption(f"Selected: **{seasonal_adj}**")
        
        # Step 4: Geography
        st.subheader("4️⃣ Geography")
        geographies = survey_config['geographies_available']
        geography = st.selectbox(
            "Select geography level:",
            geographies,
            label_visibility="collapsed",
            key="select_geography"
        )
        st.caption(f"Selected: **{geography}**")
        
        # Step 5: Data Type (conditional)
        st.subheader("5️⃣ Data Type")
        if survey_config.get('data_type_code', False):
            data_types = survey_config.get('data_type', [])

            # Load catalog availability per data type so we can annotate options
            if survey in ['SM', 'CE']:
                with st.spinner("🔍 Checking data availability..."):
                    dt_availability = get_all_valid_years_by_datatype(
                        survey, geography, seasonal_code, indicator, yaml_config
                    )
                # Build annotated labels: "All Employees, in Thousands  [2000–2025]"
                dt_labels = []
                for dt in data_types:
                    if dt in dt_availability:
                        b, e = dt_availability[dt]
                        dt_labels.append(f"{dt}  ✅ [{b}–{e}]")
                    else:
                        dt_labels.append(f"{dt}  ⚠️ [not available]")
                dt_label_to_value = {lbl: val for lbl, val in zip(dt_labels, data_types)}

                selected_label = st.selectbox(
                    "Select data type:",
                    dt_labels,
                    label_visibility="collapsed",
                    key="select_data_type"
                )
                data_type = dt_label_to_value[selected_label]
            else:
                data_type = st.selectbox(
                    "Select data type:",
                    data_types,
                    label_visibility="collapsed",
                    key="select_data_type"
                )
        else:
            data_type = "N/A"
            st.info("📌 Not applicable for this survey")
        st.caption(f"Selected: **{data_type}**")
        
        # Step 6: Employer Size (conditional - EN survey)
        st.subheader("6️⃣ Employer Size")
        if survey == 'EN':
            size_types = survey_config.get('size_type', [])
            size_code = st.selectbox(
                "Select employer size:",
                size_types,
                label_visibility="collapsed",
                key="select_size"
            )
        else:
            size_code = "N/A"
            st.info("📌 Not applicable for this survey")
        st.caption(f"Selected: **{size_code}**")
        
        # Step 7: Ownership Type (conditional - EN survey)
        st.subheader("7️⃣ Ownership Type")
        if survey == 'EN':
            owner_types = survey_config.get('owner_type', [])
            owner_code = st.selectbox(
                "Select ownership type:",
                owner_types,
                label_visibility="collapsed",
                key="select_owner"
            )
        else:
            owner_code = "N/A"
            st.info("📌 Not applicable for this survey")
        st.caption(f"Selected: **{owner_code}**")
        
        # Step 8: Measure Type (conditional - LA survey)
        st.subheader("8️⃣ Measure Type")
        if survey == 'LA':
            measure_types = survey_config.get('measure_type', [])

            # Annotate with catalog availability
            with st.spinner("🔍 Checking measure availability..."):
                ms_availability = get_all_valid_years_by_measure(
                    survey, geography, seasonal_code, indicator, yaml_config
                )
            ms_labels = []
            for mt in measure_types:
                if mt in ms_availability:
                    b, e = ms_availability[mt]
                    ms_labels.append(f"{mt}  ✅ [{b}–{e}]")
                else:
                    ms_labels.append(f"{mt}  ⚠️ [not available]")
            ms_label_to_value = {lbl: val for lbl, val in zip(ms_labels, measure_types)}

            selected_ms_label = st.selectbox(
                "Select measure type:",
                ms_labels,
                label_visibility="collapsed",
                key="select_measure"
            )
            measure_type = ms_label_to_value[selected_ms_label]
        else:
            measure_type = "N/A"
            st.info("📌 Not applicable for this survey")
        st.caption(f"Selected: **{measure_type}**")
        
        
        
        # Step 10: Years
        st.subheader("🔟 Years")
        years_available = survey_config.get('years_available', [])
        year_min_default = min(years_available)
        year_max_default = max(years_available)

        # Query catalog to get the real valid range for current config
        with st.spinner("🔍 Looking up valid year range..."):
            cat_begin, cat_end, cat_status = get_catalog_year_range(
                survey, geography, seasonal_code, indicator, yaml_config
            )

        # Use catalog range if available, otherwise fall back to yaml defaults
        if cat_begin is not None and cat_end is not None and cat_end >= cat_begin:
            year_min = cat_begin
            year_max = cat_end
            st.markdown(cat_status)
        else:
            year_min = year_min_default
            year_max = year_max_default
            st.warning(cat_status or "⚠️ Using default year range from config")

        years_option = st.radio(
            "Year selection:",
            ["All available", "Custom range", "Single year"],
            label_visibility="collapsed",
            key="select_years_option"
        )

        if years_option == "All available":
            years_list = list(range(year_min, year_max + 1))
            st.caption(f"Selected: **{year_min}–{year_max}** ({len(years_list)} years)")
        elif years_option == "Custom range":
            year_start = st.slider(
                "Start year:",
                year_min, year_max, year_min,
                key="year_start"
            )
            year_end = st.slider(
                "End year:",
                year_start, year_max, year_max,
                key="year_end"
            )
            years_list = list(range(year_start, year_end + 1))
            st.caption(f"Selected: **{year_start}–{year_end}** ({len(years_list)} years)")
        else:  # Single year
            single_year = st.selectbox(
                "Select year:",
                list(range(year_min, year_max + 1)),
                index=year_max - year_min,  # default to most recent
                label_visibility="collapsed",
                key="single_year"
            )
            years_list = [single_year]
            st.caption(f"Selected: **{single_year}**")
        
        st.markdown("---")
        
        # DOWNLOAD BUTTON
        if st.button("⬇️ DOWNLOAD DATA NOW", use_container_width=True, type="primary"):
            
            # Build parameters dict
            params = {
                'Project': project,
                'Indicator': indicator,
                'Survey': survey,
                'Geography': geography,
                'Years': years_list,
                'Seasonal Code': seasonal_code,
                'Data Type': data_type,
                'Size Code': size_code,
                'Owner Code': owner_code,
                'Measure Type': measure_type,
                'Export Location': indicator_config.get('sp_location'),
                'SP Folder': indicator_config.get('folder'),
                'Percentages': indicator_config.get('percentages', 'No'),
                'Weighted By': indicator_config.get('weighted_by', 'No')
            }
            
            st.session_state.params = params
            st.session_state.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save run log
            save_run_log(params)
            
            # Load API key and call get_data_any
            api_key = load_api_key()
            
            with st.spinner("📡 Downloading from BLS API..."):
                try:
                    df_bls = get_data_local(api_key, params, yaml_config)
                    st.session_state.df_raw = df_bls
                    st.session_state.step = 'downloaded'
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ API Error: {e}")
                    st.info("Check your API key and configuration")
    
    # RIGHT COLUMN: SUMMARY
    with st.container():
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.markdown("### 📋 Configuration Summary")
            summary_data = {
                'Project': project,
                'Indicator': indicator,
                'Survey': survey,
                'Geography': geography,
                'Data Type': data_type,
                'Employer Size': size_code,
                'Ownership': owner_code,
                'Measure': measure_type,
                'Seasonal': seasonal_adj,
                'Years': f"{min(years_list)}-{max(years_list)}" if years_list else "N/A",
                'Year Count': len(years_list)
            }
            
            for key, val in summary_data.items():
                if val and val != "N/A":
                    st.write(f"**{key}:** {val}")
        
        with col2:
            st.markdown("### 📊 Survey Info")
            st.write(f"**Surveys:**")
            for survey_name, config in yaml_config['Surveys'].items():
                st.caption(f"  • {survey_name}: {config['geographies_available']}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: RAW DATA DOWNLOADED
# ═══════════════════════════════════════════════════════════════════════════

def step_downloaded():
    """Show raw data and options"""
    
    st.title("✅ Data Downloaded")
    st.markdown("### 📥 Raw BLS Data")
    
    df = st.session_state.df_raw
    params = st.session_state.params
    
    # METRICS
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", f"{df.shape[1]}")
    with col3:
        st.metric("Download Time", st.session_state.timestamp)
    with col4:
        st.metric("Survey", params['Survey'])
    
    # RAW DATA PREVIEW
    st.markdown("---")
    st.write("### Preview (first 20 rows)")
    st.dataframe(df.head(20), use_container_width=True)
    
    # DATA INFO
    with st.expander("📊 Data Information"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Column Names:**")
            for col in df.columns:
                st.caption(f"  • {col}")
        with col2:
            st.write("**Data Types:**")
            for col, dtype in df.dtypes.items():
                st.caption(f"  • {col}: {dtype}")
    
    # BUTTONS
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="💾 Download Raw CSV",
            data=csv_data,
            file_name=f"{params['Indicator']}_{params['Geography']}_BLS_raw.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        if st.button("⚙️ Process & Download", use_container_width=True, type="primary"):
            st.session_state.step = 'processing'
            st.rerun()
    
    with col3:
        if st.button("🔄 Start Over", use_container_width=True):
            st.session_state.step = 'configure'
            st.session_state.df_raw = None
            st.session_state.df_processed = None
            st.session_state.params = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def step_processing():
    """Process raw BLS data"""
    
    st.title("⚙️ Processing Data")
    st.markdown("Running processing pipeline...")
    
    df_raw = st.session_state.df_raw
    params = st.session_state.params
    indicator = params['Indicator']
    survey = params['Survey']
    geography = params['Geography']
    percentages = params['Percentages']
    
    yaml_config = load_yaml_config()
    
    with st.spinner("🔄 Processing BLS data..."):
        try:
            # Main processing
            df_processed, df_series_area = post.proc_bls(df_raw, params, yaml_config)
            
            # Indicator-specific processing
            if indicator == 'Jobs_1':
                df_final = post.jobs_1(df_processed, percentages, geography)
                st.session_state.df_processed = df_final
                st.session_state.step = 'processed'
                
            elif indicator == 'Jobs_2':
                df_msa, df_mpo = post.jobs_2(df_processed, percentages, geography, df_series_area)
                st.session_state.df_processed = (df_msa, df_mpo)
                st.session_state.step = 'processed_multi'
                
            elif indicator == 'Jobs_3':
                df_1, df_2 = post.jobs_3(df_processed)
                st.session_state.df_processed = (df_1, df_2)
                st.session_state.step = 'processed_multi'
                
            elif indicator == 'Labor_2':
                df_final = post.labor_2(df_processed)
                st.session_state.df_processed = df_final
                st.session_state.step = 'processed'
            
            st.session_state.df_series_area = df_series_area
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Processing Error: {e}")
            st.info("This may be due to missing reference data (weights, CPI, etc.)")
            
            if st.button("⬅️ Back to Raw Data"):
                st.session_state.step = 'downloaded'
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: PROCESSED DATA (Single Output)
# ═══════════════════════════════════════════════════════════════════════════

def step_processed():
    """Show processed data"""
    
    st.title("✅ Data Processed")
    st.markdown("### 📊 Processed BLS Data")
    
    df = st.session_state.df_processed
    params = st.session_state.params
    indicator = params['Indicator']
    
    # METRICS
    col1, col2, col3, col4 = col4, col5, col6 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", f"{df.shape[1]}")
    with col3:
        st.metric("Indicator", indicator)
    
    # PROCESSED DATA PREVIEW
    st.markdown("---")
    st.write("### Preview (first 20 rows)")
    st.dataframe(df.head(20), use_container_width=True)
    
    # DOWNLOAD BUTTON
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv_data,
            file_name=f"{indicator}_{params['Geography']}_BLS_processed.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        if st.button("🔄 Start Over", use_container_width=True):
            st.session_state.step = 'configure'
            st.session_state.df_raw = None
            st.session_state.df_processed = None
            st.session_state.params = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: PROCESSED DATA (Multiple Outputs)
# ═══════════════════════════════════════════════════════════════════════════

def step_processed_multi():
    """Show multiple processed dataframes"""
    
    st.title("✅ Data Processed")
    st.markdown("### 📊 Processed BLS Data (Multiple Outputs)")
    
    df_1, df_2 = st.session_state.df_processed
    params = st.session_state.params
    indicator = params['Indicator']
    
    # TABS FOR DIFFERENT OUTPUTS
    tab1, tab2 = st.tabs(["📊 Output 1", "📊 Output 2"])
    
    with tab1:
        st.write(f"**Shape:** {df_1.shape[0]:,} rows × {df_1.shape[1]} columns")
        st.dataframe(df_1.head(20), use_container_width=True)
        
        csv_data = df_1.to_csv(index=False)
        st.download_button(
            label="💾 Download Output 1 CSV",
            data=csv_data,
            file_name=f"{indicator}_{params['Geography']}_BLS_output1.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with tab2:
        st.write(f"**Shape:** {df_2.shape[0]:,} rows × {df_2.shape[1]} columns")
        st.dataframe(df_2.head(20), use_container_width=True)
        
        csv_data = df_2.to_csv(index=False)
        st.download_button(
            label="💾 Download Output 2 CSV",
            data=csv_data,
            file_name=f"{indicator}_{params['Geography']}_BLS_output2.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # START OVER BUTTON
    st.markdown("---")
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.step = 'configure'
        st.session_state.df_raw = None
        st.session_state.df_processed = None
        st.session_state.params = None
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN APP LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main application router"""
    
    step = st.session_state.step
    
    if step == 'configure':
        step_configure()
    elif step == 'downloaded':
        step_downloaded()
    elif step == 'processing':
        step_processing()
    elif step == 'processed':
        step_processed()
    elif step == 'processed_multi':
        step_processed_multi()
    else:
        st.error(f"❌ Unknown step: {step}")

if __name__ == '__main__':
    main()