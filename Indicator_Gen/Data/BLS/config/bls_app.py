import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

import importlib.util
from pathlib import Path

_bls_config = Path(__file__).parent

def _load(name):
    key = f"_bls_module_{name}"
    if key not in st.session_state:
        spec = importlib.util.spec_from_file_location(
            f"bls_{name}",
            _bls_config / f"{name}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        st.session_state[key] = mod
    return st.session_state[key]

pre  = _load("pre")
get  = _load("get")
post = _load("post")

# ═══════════════════════════════════════════════════════════════════════════
# 1. SETUP & UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

FILE_API = get.PATH_CONFIG / 'api_key.txt'

def load_api_key():
    try:
        with open(FILE_API, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        st.error(f"API Key file not found at {FILE_API}")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 2. SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

if 'bls_step' not in st.session_state:
    st.session_state.bls_step = 'configure'
if 'bls_params' not in st.session_state:
    st.session_state.bls_params = None
if 'bls_df_raw' not in st.session_state:
    st.session_state.bls_df_raw = None
if 'bls_df_processed' not in st.session_state:
    st.session_state.bls_df_processed = None
if 'bls_df_meta' not in st.session_state:
    st.session_state.bls_df_meta = None

def reset_app():
    st.session_state.bls_step = 'configure'
    st.session_state.bls_params = None
    st.session_state.bls_df_raw = None
    st.session_state.bls_df_processed = None
    st.session_state.bls_df_meta = None
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# 3. STEP 1: CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def show_configuration():
    st.title("📊 BLS Data Pipeline")
    st.markdown("### Step 1: Configure Request")
    
    yaml_bls = pre.load_yaml()
    
    projects = yaml_bls.get('Project', [])
    project = st.selectbox("📁 Which project are you pulling data for?", projects)
    
    indicators = list(yaml_bls['Indicators'].get(project, {}).keys())
    indicator = st.selectbox("📈 Which indicator do you need?", indicators)
    
    meta = yaml_bls['Indicators'][project][indicator]
    export_loc = meta.get('sp_location', '')
    folder = meta.get('folder', '')
    percentages = meta.get('percentages', 'No')
    weighted_by = meta.get('weighted_by', 'No')
    
    surveys = meta['survey']
    if isinstance(surveys, list):
        survey = st.selectbox("🔍 Which survey do you want to pull data from?", surveys)
    else:
        survey = surveys
        st.info(f"Survey: {survey}")

    st.markdown("---")
    
    survey_meta = yaml_bls.get('Surveys', {}).get(survey, {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_type_text = size_code_text = owner_code_text = measure_type_text = "N/A"

        if survey in ['SM', 'CE', 'EN']:
            data_types = survey_meta.get('data_type', [])
            data_type_text = st.selectbox("📊 Which data type do you want to request?", data_types)
        
        if survey == 'EN':
            size_code_text = st.selectbox("📏 Which employer size category?", survey_meta.get('size_type', []))
            owner_code_text = st.selectbox("🏢 Which ownership category?", survey_meta.get('owner_type', []))
            
        if survey == 'LA':
            measure_type_text = st.selectbox("📏 Which measure type?", survey_meta.get('measure_type', []))

    with col2:
        seasonal_adj = st.radio("❄️ Do you want seasonally adjusted estimates?", ["No", "Yes"], horizontal=True)
        seasonal_code = 'S' if seasonal_adj == "Yes" else 'U'
        
        geographies = survey_meta.get('geographies_available', [])
        geography = st.selectbox("🌎 Which geography do you want to pull data for?", geographies)
        
        available_years = survey_meta.get('years_available', [])
        all_years = st.checkbox("Pull all years available?", value=True)
        if all_years:
            years_to_import = available_years
        else:
            years_to_import = st.multiselect("Select years", available_years, default=[max(available_years)])

    st.markdown("---")
    
    if st.button("📥 Fetch Raw Data", use_container_width=True, type="primary"):
        if not years_to_import:
            st.error("Please select at least one year.")
            return

        st.session_state.bls_params = {
            'Project': project,
            'Indicator': indicator,
            'Survey': survey,
            'Geography': geography,
            'Years': sorted(years_to_import),
            'Seasonal Code': seasonal_code,
            'Percentages': percentages,
            'Weighted By': weighted_by,
            'Data Type': data_type_text,
            'Size Code': size_code_text,
            'Owner Code': owner_code_text,
            'Measure Type': measure_type_text,
            'Export Location': export_loc,
            'SP Folder': folder
        }
        
        st.session_state.bls_step = 'fetching'
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# 4. STEP 2: FETCH & VIEW RAW DATA
# ═══════════════════════════════════════════════════════════════════════════

def do_fetch():
    api_key = load_api_key()
    if not api_key: st.stop()
    
    yaml_bls = pre.load_yaml()
    params = st.session_state.bls_params

    with st.status("Fetching data from BLS API...", expanded=True) as status:
        df_raw = get.get_data_any(api_key, params, yaml_bls)
        
        if df_raw is None or df_raw.empty:
            status.update(label="❌ API returned no data", state="error")
            st.error("No data found for these parameters.")
            if st.button("Back"): reset_app()
            return
            
        st.session_state.bls_df_raw = df_raw
        status.update(label="✅ Fetch Complete!", state="complete")
        
    st.session_state.bls_step = 'view_raw'
    st.rerun()

def show_raw_data():
    params = st.session_state.bls_params
    df_raw = st.session_state.bls_df_raw
    
    st.title("📥 Step 2: Raw API Data")
    st.subheader(f"Indicator: {params['Indicator']} | Survey: {params['Survey']}")
    
    st.metric("Raw Rows", f"{len(df_raw):,}")
    st.dataframe(df_raw, use_container_width=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv_raw = df_raw.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download Raw CSV", csv_raw, f"{params['Indicator']}_raw.csv", "text/csv")
        
    with col2:
        if st.button("⚙️ Process Data", type="primary", use_container_width=True):
            st.session_state.bls_step = 'processing'
            st.rerun()
            
    with col3:
        if st.button("🔄 Start Over", use_container_width=True):
            reset_app()

# ═══════════════════════════════════════════════════════════════════════════
# 5. STEP 3: PROCESS & VIEW FINAL DATA
# ═══════════════════════════════════════════════════════════════════════════

def do_process():
    params = st.session_state.bls_params
    df_raw = st.session_state.bls_df_raw
    yaml_bls = pre.load_yaml()
    indicator = params['Indicator']
    
    with st.status("Running Post-Processing...", expanded=True) as status:
        # 1. Base Processing (Extracts metadata and basic formats)
        df_base, df_meta = post.proc_bls(df_raw, params, yaml_bls)
        st.session_state.bls_df_meta = df_meta
        
        # 2. Indicator-Specific Routing (from your 2__process_BLS.py)
        if indicator == 'Jobs_1':
            df_final = post.jobs_1(df_base, params['Percentages'], params['Geography'])
            st.session_state.bls_df_processed = df_final
            
        elif indicator == 'Jobs_2':
            df_msa, df_mpo = post.jobs_2(df_base, params['Percentages'], params['Geography'], df_meta)
            st.session_state.bls_df_processed = (df_msa, df_mpo)
            
        elif indicator == 'Jobs_3':
            df_1, df_2 = post.jobs_3(df_base)
            st.session_state.bls_df_processed = (df_1, df_2)
            
        elif indicator == 'Labor_2':
            df_final = post.labor_2(df_base)
            st.session_state.bls_df_processed = df_final
            
        else:
            # Fallback if no specific processing exists
            st.session_state.bls_df_processed = df_base
            
        status.update(label="✅ Processing Complete!", state="complete")
        
    st.session_state.bls_step = 'view_processed'
    st.rerun()

def show_processed_data():
    params = st.session_state.bls_params
    df_proc = st.session_state.bls_df_processed
    df_meta = st.session_state.bls_df_meta
    
    st.title("✅ Step 3: Processed Data")
    st.subheader(f"Final output for {params['Indicator']}")
    
    # Handle single dataframe vs tuple (Jobs_2 and Jobs_3 return two dataframes)
    if isinstance(df_proc, tuple):
        tab1, tab2, tab_meta = st.tabs(["📊 Output 1", "📊 Output 2", "ℹ️ Series Metadata"])
        
        with tab1:
            st.dataframe(df_proc[0], use_container_width=True)
            csv1 = df_proc[0].to_csv(index=False).encode('utf-8')
            st.download_button("💾 Download Output 1", csv1, f"{params['Indicator']}_1.csv", "text/csv")
            
        with tab2:
            st.dataframe(df_proc[1], use_container_width=True)
            csv2 = df_proc[1].to_csv(index=False).encode('utf-8')
            st.download_button("💾 Download Output 2", csv2, f"{params['Indicator']}_2.csv", "text/csv")
            
    else:
        tab1, tab_meta = st.tabs(["📊 Processed Data", "ℹ️ Series Metadata"])
        
        with tab1:
            st.dataframe(df_proc, use_container_width=True)
            csv_main = df_proc.to_csv(index=False).encode('utf-8')
            st.download_button("💾 Download Processed CSV", csv_main, f"{params['Indicator']}_final.csv", "text/csv")
            
    with tab_meta:
        st.dataframe(df_meta, use_container_width=True)
        csv_meta = df_meta.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download Metadata CSV", csv_meta, f"{params['Indicator']}_metadata.csv", "text/csv")

    st.markdown("---")
    if st.button("🔄 Start New Request", type="primary"):
        reset_app()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════

if st.session_state.bls_step == 'configure':
    show_configuration()
elif st.session_state.bls_step == 'fetching':
    do_fetch()
elif st.session_state.bls_step == 'view_raw':
    show_raw_data()
elif st.session_state.bls_step == 'processing':
    do_process()
elif st.session_state.bls_step == 'view_processed':
    show_processed_data()