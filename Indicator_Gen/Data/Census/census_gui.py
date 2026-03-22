"""
Census Data Request Pipeline - Fixed Version
Properly handles processing without resetting page
Run: streamlit run census_gui.py
"""

import streamlit as st
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

st.set_page_config(page_title="Census Data Request", layout="wide")

st.markdown("""
<style>
.main { padding-top: 2rem; }
.stButton>button { width: 100%; height: 50px; border-radius: 10px; font-size: 16px; font-weight: bold; }
.success-box { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; }
.info-box { background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 15px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ===============================================
# LOAD CONFIG & AREA CODES
# ===============================================

try:
    path_code = Path(__file__).parent
    path_config = path_code / 'config'
    path_config0 = path_code.parent / 'config'
    path_yaml = path_config / 'census.yaml'
    
    with open(path_yaml, 'r') as f:
        yaml_config = yaml.load(f, Loader=yaml.SafeLoader)
    
    # Load area_codes.xlsx
    area_codes_file = path_config0 / 'area_codes.xlsx'
    df_states = pd.read_excel(area_codes_file, sheet_name='StateNames')[['STATE', 'Postal']]
    df_counties = pd.read_excel(area_codes_file, sheet_name='CountyFIPS')[['STATE', 'COUNTYNAME']]
    df_msa = pd.read_excel(area_codes_file, sheet_name='MSAcodes')[['State', 'MSA']].drop_duplicates()
    
    runs_dir = path_config / 'runs'
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    sys.path.append(str(path_config))
    import pre
    import get
    import post
    
    sys.path.append(str(path_config0))
    
    with open(path_config / 'api_key.txt', 'r') as f:
        api_key = f.read().strip()
    
except Exception as e:
    st.error(f"❌ Error loading configuration: {str(e)}")
    st.stop()

# ===============================================
# INITIALIZE SESSION STATE
# ===============================================

if 'step' not in st.session_state:
    st.session_state.step = 'configure'  # 'configure', 'downloaded', 'processed'
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None
if 'df_processed' not in st.session_state:
    st.session_state.df_processed = None
if 'params' not in st.session_state:
    st.session_state.params = None
if 'timestamp' not in st.session_state:
    st.session_state.timestamp = None

# ===============================================
# HEADER
# ===============================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("📊 Census Data Pipeline")
    st.markdown("Download & Process")

st.markdown("---")

# ===============================================
# STEP 1: CONFIGURATION
# ===============================================

if st.session_state.step == 'configure':
    
    col_settings, col_preview = st.columns([1, 1])
    
    with col_settings:
        st.header("📋 Configure")
        
        # Project
        st.subheader("1️⃣ Project")
        projects = yaml_config['Project']
        project = st.selectbox("Which project?", projects, key="proj")
        
        # Indicator
        st.subheader("2️⃣ Indicator")
        indicators = list(yaml_config['Indicators'].get(project, {}).keys())
        indicator = st.selectbox("Which indicator?", indicators, key="ind")
        indicator_config = yaml_config['Indicators'][project][indicator]
        
        # Sample
        st.subheader("3️⃣ Sample Type")
        sample_options = indicator_config.get('sample', 'ACS')
        if isinstance(sample_options, str):
            sample_options = [sample_options]
        
        if len(sample_options) == 1:
            sample_type = sample_options[0]
            st.info(f"**{sample_type}**")
        else:
            sample_type = st.selectbox("Which sample?", sample_options, key="samp")
        
        # Estimate
        st.subheader("4️⃣ Estimate")
        available_estimates = list(yaml_config['Samples'][sample_type].keys())
        estimate = st.selectbox("Which estimate?", available_estimates, key="est")
        
        # Geography Level
        st.subheader("5️⃣ Geography Level")
        available_geos = yaml_config['Samples'][sample_type][estimate].get('geographies_available', [])
        geography_level = st.selectbox("Which level?", available_geos, key="geo_level")
        
        # Specific Geographies
        st.subheader("6️⃣ Select Specific Geographies")
        
        selected_geographies = []
        
        if geography_level == 'National':
            st.info("**National Coverage - All USA**")
            selected_geographies = ['*']
        
        elif geography_level == 'States':
            states_list = sorted(df_states['Postal'].unique())
            selected_states = st.multiselect("Select states:", states_list, default=['CA'], key="states_select")
            selected_geographies = selected_states
        
        elif geography_level == 'Counties':
            states_list = sorted(df_states['Postal'].unique())
            selected_states = st.multiselect("Select state(s) first:", states_list, default=['CA'], key="county_states")
            
            if selected_states:
                counties_in_states = df_counties[df_counties['STATE'].isin(selected_states)]['COUNTYNAME'].unique()
                selected_counties = st.multiselect(
                    "Select counties:",
                    sorted(counties_in_states),
                    default=[c for c in ['Sacramento', 'Placer', 'El Dorado'] if c in counties_in_states],
                    key="counties_select"
                )
                selected_geographies = selected_counties
        
        elif geography_level == 'MSA':
            msa_list = sorted(df_msa['MSA'].dropna().unique())
            selected_msa = st.multiselect("Select MSA(s):", msa_list, default=['Sacramento, CA'], key="msa_select")
            selected_geographies = selected_msa
        
        elif geography_level == 'Block Groups':
            states_list = sorted(df_states['Postal'].unique())
            selected_states = st.multiselect("Select state(s):", states_list, default=['CA'], key="bg_states")
            if selected_states:
                counties_in_states = df_counties[df_counties['STATE'].isin(selected_states)]['COUNTYNAME'].unique()
                selected_counties = st.multiselect("Select counties:", sorted(counties_in_states), 
                    default=[c for c in ['Sacramento', 'Placer', 'El Dorado'] if c in counties_in_states], key="bg_counties_select")
                selected_geographies = selected_counties
        
        elif geography_level == 'Tracts':
            states_list = sorted(df_states['Postal'].unique())
            selected_states = st.multiselect("Select state(s):", states_list, default=['CA'], key="tract_states")
            if selected_states:
                counties_in_states = df_counties[df_counties['STATE'].isin(selected_states)]['COUNTYNAME'].unique()
                selected_counties = st.multiselect("Select counties:", sorted(counties_in_states),
                    default=[c for c in ['Sacramento', 'Placer', 'El Dorado'] if c in counties_in_states], key="tract_counties_select")
                selected_geographies = selected_counties
        
        elif geography_level == 'Places':
            states_list = sorted(df_states['Postal'].unique())
            selected_states = st.multiselect("Select state(s):", states_list, default=['CA'], key="place_states")
            selected_geographies = selected_states
        
        else:
            selected_geographies = [geography_level]
        
        # Years
        st.subheader("7️⃣ Years")
        available_years = yaml_config['Samples'][sample_type][estimate].get('years_available', [])
        
        if available_years == ['timeseries']:
            st.info("**LEHD Data - Quarterly Timeseries**")
            years_to_import = 'timeseries'
        else:
            year_option = st.radio("Year selection:", ['All available', 'Custom range', 'Single year'], horizontal=True, key="year_opt")
            
            if year_option == 'All available':
                years_to_import = available_years
            elif year_option == 'Custom range':
                col_y1, col_y2 = st.columns(2)
                with col_y1:
                    start_idx = st.selectbox("Start:", range(len(available_years)), key="start", format_func=lambda i: str(available_years[i]))
                with col_y2:
                    end_idx = st.selectbox("End:", range(len(available_years)), key="end", index=len(available_years)-1, format_func=lambda i: str(available_years[i]))
                years_to_import = available_years[start_idx:end_idx+1]
            else:
                year_idx = st.selectbox("Select year:", range(len(available_years)), key="single", format_func=lambda i: str(available_years[i]), index=len(available_years)-1)
                years_to_import = [available_years[year_idx]]
        
        # MOE
        st.subheader("8️⃣ Margin of Error")
        if sample_type not in ['DEC', 'LEHD']:
            include_moe = st.checkbox("Include MOE?", True, key="moe")
        else:
            st.info(f"⚠️ {sample_type} has no MOE")
            include_moe = False
    
    # Preview
    with col_preview:
        st.header("📊 Preview")
        st.markdown('<div class="info-box"><strong>Configuration Summary</strong></div>', unsafe_allow_html=True)
        
        if isinstance(years_to_import, list):
            year_display = f"{min(years_to_import)} to {max(years_to_import)}" if len(years_to_import) > 1 else str(years_to_import[0])
        else:
            year_display = years_to_import
        
        geo_display = ', '.join(selected_geographies) if selected_geographies and selected_geographies != ['*'] else 'National'
        
        summary_data = {
            'Parameter': ['Project', 'Indicator', 'Sample', 'Estimate', 'Geography', 'Geographies', 'Years', 'MOE', 'Metric'],
            'Value': [project, indicator, sample_type, estimate, geography_level, geo_display[:30] + '...' if len(geo_display) > 30 else geo_display, year_display, 'Yes' if include_moe else 'No', indicator_config.get('metric')]
        }
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        
        st.subheader("📋 Indicator Details")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.write(f"**Variables:** {indicator_config.get('number_of_variables')}")
            st.write(f"**Percentages:** {indicator_config.get('percentages')}")
        with col_d2:
            st.write(f"**Weighted:** {indicator_config.get('weighted_by')}")
            st.write(f"**Adjust CPI:** {indicator_config.get('adjust_cpi')}")
    
    # Download Button
    st.markdown("---")
    
    if st.button("⬇️ DOWNLOAD DATA NOW", use_container_width=True, key="download_btn"):
        if not selected_geographies:
            st.error("❌ Please select at least one geography")
        else:
            try:
                if isinstance(years_to_import, list):
                    year_start = int(np.min(years_to_import))
                    year_end = int(np.max(years_to_import))
                    years_list = years_to_import
                else:
                    year_start = year_end = None
                    years_list = 'timeseries'
                
                import_tab = yaml_config['Import Geographies'].get(geography_level, geography_level)
                
                moe_bool = True if include_moe else False
                pct_bool = True if indicator_config.get('percentages') == 'Yes' else False
                cpi_bool = True if indicator_config.get('adjust_cpi') == 'Yes' else False
                
                params = {
                    'project': project,
                    'indicator': indicator,
                    'estimate': estimate,
                    'sample': sample_type,
                    'geo': geography_level,
                    'years_to_import': years_list,
                    'start_year': year_start,
                    'end_year': year_end,
                    'import_tab': import_tab,
                    'moe': moe_bool,
                    'moe_thresh': float(indicator_config.get('MOE_threshold', 0.05)),
                    'num_vars': int(indicator_config.get('number_of_variables')),
                    'metric': indicator_config.get('metric'),
                    'pct': pct_bool,
                    'weight': str(indicator_config.get('weighted_by', '')),
                    'adjust_cpi': cpi_bool,
                    'export_loc': indicator_config.get('sp_location', ''),
                    'folder': indicator_config.get('folder', ''),
                }
                
                # Save config log
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = runs_dir / f"{timestamp}_{indicator}.txt"
                with open(log_file, 'w') as f:
                    f.write(f"Project: {project}\n")
                    f.write(f"Indicator Name: {indicator}\n")
                    f.write(f"Sample: {sample_type}\n")
                    f.write(f"Estimate: {estimate}\n")
                    f.write(f"Geography Level: {geography_level}\n")
                    f.write(f"Selected Geographies: {', '.join(selected_geographies)}\n")
                    if isinstance(years_list, list):
                        f.write(f"Years Imported: {', '.join(map(str, years_list))}\n")
                    else:
                        f.write(f"Years Imported: {years_list}\n")
                    f.write(f"Import Tab: {import_tab}\n")
                    f.write(f"Margin of Error: {'Yes' if include_moe else 'No'}\n")
                
                st.success(f"✅ Configuration saved to: {log_file.name}")
                
                # Download data
                with st.spinner("🔄 Downloading data from Census API... This may take 1-5 minutes"):
                    df_census = get.get_data_any(api_key, params)
                
                # Store in session state
                st.session_state.df_raw = df_census
                st.session_state.params = params
                st.session_state.timestamp = timestamp
                st.session_state.step = 'downloaded'
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error downloading data: {str(e)}")

# ===============================================
# STEP 2: DATA DOWNLOADED - SHOW EXPORT OPTIONS
# ===============================================

elif st.session_state.step == 'downloaded':
    
    st.success("✅ Data downloaded successfully!")
    
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        st.metric("Rows", len(st.session_state.df_raw))
    with col_i2:
        st.metric("Columns", len(st.session_state.df_raw.columns))
    with col_i3:
        if 'Year' in st.session_state.df_raw.columns:
            st.metric("Years", len(st.session_state.df_raw['Year'].unique()))
    
    st.subheader("Raw Data Preview")
    st.dataframe(st.session_state.df_raw.head(10), use_container_width=True)
    
    st.markdown("---")
    st.subheader("📥 Export Options")
    
    col_export1, col_export2 = st.columns(2)
    
    # Option 1: Download Raw
    with col_export1:
        csv_raw = st.session_state.df_raw.to_csv(index=False)
        st.download_button(
            label="💾 Download Raw CSV",
            data=csv_raw,
            file_name=f"{st.session_state.params['indicator']}_{st.session_state.params['geo']}_{st.session_state.params['estimate']}_raw_{st.session_state.timestamp}.csv",
            mime="text/csv",
            key="download_raw_btn"
        )
        st.caption("Direct from Census API")
    
    # Option 2: Process
    with col_export2:
        if st.button("⚙️ Process & Download", use_container_width=True, key="process_btn"):
            st.session_state.step = 'processing'
            st.rerun()
    
    # Reset button
    st.markdown("---")
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.step = 'configure'
        st.session_state.df_raw = None
        st.session_state.df_processed = None
        st.session_state.params = None
        st.rerun()

# ===============================================
# STEP 3: PROCESSING
# ===============================================

elif st.session_state.step == 'processing':
    
    st.info("⚙️ Processing data through 2__process_census.py pipeline...")
    
    try:
        df_census = st.session_state.df_raw
        params = st.session_state.params
        timestamp = st.session_state.timestamp
        
        with st.spinner("🔄 This may take 1-5 minutes depending on data size..."):
            
            # Read variables
            df_vars = get.read_vars_file(params)
            
            # Process based on sample type
            if params['sample'] in ['ACS', 'DP', 'SUBJECT', 'DEC']:
                
                df_processed = post.acs_main(df_census, params, df_vars)
                st.session_state.df_processed = df_processed
                st.session_state.step = 'processed'
                st.rerun()
            
            elif params['sample'] in ['PUMS', 'FOODSEC']:
                
                if params['sample'] == 'PUMS':
                    if 'H' in df_vars['Table Type'].unique():
                        weight = 'WGTP'
                    else:
                        weight = 'PWGTP'
                    
                    df_puma, df_counties, df_msa, df_mpo = post.pums_main(df_census, params, weight, df_vars)
                    
                    st.session_state.df_puma = df_puma
                    st.session_state.df_counties = df_counties
                    st.session_state.df_msa = df_msa
                    st.session_state.step = 'processed_pums'
                    st.rerun()
            
            else:
                st.warning(f"Processing not implemented for {params['sample']}")
    
    except Exception as e:
        st.error(f"❌ Processing error: {str(e)}")
        st.error("Traceback:")
        import traceback
        st.error(traceback.format_exc())
        
        st.markdown("---")
        if st.button("⬅️ Back to Download Options"):
            st.session_state.step = 'downloaded'
            st.rerun()

# ===============================================
# STEP 4: PROCESSED DATA - SHOW DOWNLOAD
# ===============================================

elif st.session_state.step == 'processed':
    
    st.success("✅ Processing complete!")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.metric("Processed Rows", len(st.session_state.df_processed))
    with col_i2:
        st.metric("Processed Columns", len(st.session_state.df_processed.columns))
    
    st.subheader("Processed Data Preview")
    st.dataframe(st.session_state.df_processed.head(10), use_container_width=True)
    
    st.markdown("---")
    
    csv_processed = st.session_state.df_processed.to_csv(index=False)
    st.download_button(
        label="💾 Download Processed CSV",
        data=csv_processed,
        file_name=f"{st.session_state.params['indicator']}_{st.session_state.params['geo']}_{st.session_state.params['estimate']}_processed_{st.session_state.timestamp}.csv",
        mime="text/csv",
        key="download_processed_btn"
    )
    
    st.markdown('<div class="success-box"><strong>✅ Processed data ready to download!</strong></div>', unsafe_allow_html=True)
    
    if st.button("🔄 Start Over"):
        st.session_state.step = 'configure'
        st.session_state.df_raw = None
        st.session_state.df_processed = None
        st.session_state.params = None
        st.rerun()

# ===============================================
# STEP 5: PROCESSED PUMS DATA
# ===============================================

elif st.session_state.step == 'processed_pums':
    
    st.success("✅ PUMS Processing complete!")
    
    st.subheader("Select Geography Level to Download")
    
    geo_option = st.radio(
        "Which geography?",
        options=['Counties', 'MSA', 'PUMA'],
        horizontal=True,
        key="pums_geo_select"
    )
    
    if geo_option == 'Counties':
        df_to_download = st.session_state.df_counties
    elif geo_option == 'MSA':
        df_to_download = st.session_state.df_msa
    else:
        df_to_download = st.session_state.df_puma
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.metric("Rows", len(df_to_download))
    with col_i2:
        st.metric("Columns", len(df_to_download.columns))
    
    st.subheader(f"{geo_option} Data Preview")
    st.dataframe(df_to_download.head(10), use_container_width=True)
    
    st.markdown("---")
    
    csv_pums = df_to_download.to_csv(index=False)
    st.download_button(
        label="💾 Download Processed CSV",
        data=csv_pums,
        file_name=f"{st.session_state.params['indicator']}_{geo_option}_{st.session_state.params['estimate']}_processed_{st.session_state.timestamp}.csv",
        mime="text/csv",
        key="download_pums_btn"
    )
    
    st.markdown('<div class="success-box"><strong>✅ Processed PUMS data ready to download!</strong></div>', unsafe_allow_html=True)
    
    if st.button("🔄 Start Over"):
        st.session_state.step = 'configure'
        st.session_state.df_raw = None
        st.rerun()

# ===============================================
# SIDEBAR
# ===============================================

with st.sidebar:
    st.header("ℹ️ Status")
    if st.session_state.step == 'configure':
        st.write("**Current Step:** Configuration")
    elif st.session_state.step == 'downloaded':
        st.write("**Current Step:** Data Downloaded")
        st.write("Choose export option")
    elif st.session_state.step == 'processing':
        st.write("**Current Step:** Processing...")
    elif st.session_state.step == 'processed':
        st.write("**Current Step:** Ready to Download")
    elif st.session_state.step == 'processed_pums':
        st.write("**Current Step:** PUMS Ready to Download")

st.markdown("---")
st.markdown('<div style="text-align: center; color: gray; font-size: 12px;">Census Data Pipeline | Complete Download & Processing</div>', unsafe_allow_html=True)
