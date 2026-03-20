"""
Census Data Request Pipeline - Complete Streamlit GUI
Fully replicates CLI - download data directly from the app
Run: streamlit run census_gui.py
"""

import streamlit as st
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

st.set_page_config(page_title="Census Data Request", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main { padding-top: 2rem; }
.stButton>button { width: 100%; height: 50px; border-radius: 10px; font-size: 16px; font-weight: bold; }
.success-box { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; }
.info-box { background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 15px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Load config
try:
    path_code = Path(__file__).parent
    path_config = path_code / 'config'
    path_yaml = path_config / 'census.yaml'
    
    with open(path_yaml, 'r') as f:
        yaml_config = yaml.load(f, Loader=yaml.SafeLoader)
    
    runs_dir = path_config / 'runs'
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    sys.path.append(str(path_config))
    import pre
    import get
    
    with open(path_config / 'api_key.txt', 'r') as f:
        api_key = f.read().strip()
    
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.stop()

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("📊 Census Data Pipeline")
    st.markdown("Download data directly - no CLI needed")

st.markdown("---")

# Main layout
col_settings, col_preview = st.columns([1, 1])

with col_settings:
    st.header("📋 Configure")
    
    # 1. Project
    st.subheader("1️⃣ Project")
    projects = yaml_config['Project']
    project = st.selectbox("Which project?", projects, key="proj")
    
    # 2. Indicator
    st.subheader("2️⃣ Indicator")
    indicators = list(yaml_config['Indicators'].get(project, {}).keys())
    indicator = st.selectbox("Which indicator?", indicators, key="ind")
    indicator_config = yaml_config['Indicators'][project][indicator]
    
    # 3. Sample
    st.subheader("3️⃣ Sample Type")
    sample_options = indicator_config.get('sample', 'ACS')
    if isinstance(sample_options, str):
        sample_options = [sample_options]
    
    if len(sample_options) == 1:
        sample_type = sample_options[0]
        st.info(f"**{sample_type}**")
    else:
        sample_type = st.selectbox("Which sample?", sample_options, key="samp")
    
    # 4. Estimate
    st.subheader("4️⃣ Estimate")
    available_estimates = list(yaml_config['Samples'][sample_type].keys())
    estimate = st.selectbox("Which estimate?", available_estimates, key="est")
    
    # 5. Geography
    st.subheader("5️⃣ Geography")
    available_geos = yaml_config['Samples'][sample_type][estimate].get('geographies_available', [])
    geography = st.selectbox("Which geography?", available_geos, key="geo")
    
    # 6. Years
    st.subheader("6️⃣ Years")
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
    
    # 7. MOE
    st.subheader("7️⃣ Margin of Error")
    if sample_type not in ['DEC', 'LEHD']:
        include_moe = st.checkbox("Include MOE?", True, key="moe")
    else:
        st.info(f"⚠️ {sample_type} has no MOE")
        include_moe = False

with col_preview:
    st.header("📊 Preview")
    st.markdown('<div class="info-box"><strong>Configuration</strong></div>', unsafe_allow_html=True)
    
    if isinstance(years_to_import, list):
        year_display = f"{min(years_to_import)} to {max(years_to_import)}" if len(years_to_import) > 1 else str(years_to_import[0])
    else:
        year_display = years_to_import
    
    summary_data = {
        'Parameter': ['Project', 'Indicator', 'Sample', 'Estimate', 'Geography', 'Years', 'MOE', 'Metric'],
        'Value': [project, indicator, sample_type, estimate, geography, year_display, 'Yes' if include_moe else 'No', indicator_config.get('metric')]
    }
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
    
    st.subheader("Details")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write(f"**Variables:** {indicator_config.get('number_of_variables')}")
        st.write(f"**Percentages:** {indicator_config.get('percentages')}")
    with col_d2:
        st.write(f"**Weighted:** {indicator_config.get('weighted_by')}")
        st.write(f"**Adjust CPI:** {indicator_config.get('adjust_cpi')}")

st.markdown("---")

col_btn1, col_btn2 = st.columns([1, 1])

with col_btn1:
    if st.button("⬇️ DOWNLOAD DATA NOW", use_container_width=True, key="download"):
        try:
            if isinstance(years_to_import, list):
                year_start = int(np.min(years_to_import))
                year_end = int(np.max(years_to_import))
                years_list = years_to_import
            else:
                year_start = year_end = None
                years_list = 'timeseries'
            
            import_tab = yaml_config['Import Geographies'].get(geography, geography)
            
            moe_bool = True if include_moe else False
            pct_bool = True if indicator_config.get('percentages') == 'Yes' else False
            cpi_bool = True if indicator_config.get('adjust_cpi') == 'Yes' else False
            
            params = {
                'project': project,
                'indicator': indicator,
                'estimate': estimate,
                'sample': sample_type,
                'geo': geography,
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
                'folder': indicator_config.get('folder', '')
            }
            
            # Save log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = runs_dir / f"{timestamp}_{indicator}.txt"
            with open(log_file, 'w') as f:
                f.write(f"Project: {project}\n")
                f.write(f"Indicator Name: {indicator}\n")
                f.write(f"Sample: {sample_type}\n")
                f.write(f"Estimate: {estimate}\n")
                f.write(f"Geography: {geography}\n")
                if isinstance(years_list, list):
                    f.write(f"Years Imported: {', '.join(map(str, years_list))}\n")
                else:
                    f.write(f"Years Imported: {years_list}\n")
                f.write(f"Import Tab: {import_tab}\n")
                f.write(f"Margin of Error: {'Yes' if include_moe else 'No'}\n")
            
            st.success(f"✅ Config: {log_file.name}")
            
            # Download
            status_placeholder = st.empty()
            status_placeholder.text("🔄 Downloading...")
            
            df_census = get.get_data_any(api_key, params)
            
            st.success("✅ Downloaded!")
            
            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1:
                st.metric("Rows", len(df_census))
            with col_i2:
                st.metric("Columns", len(df_census.columns))
            with col_i3:
                if 'Year' in df_census.columns:
                    st.metric("Years", len(df_census['Year'].unique()))
            
            st.subheader("Preview")
            st.dataframe(df_census.head(10), use_container_width=True)
            
            csv_data = df_census.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"{indicator}_{geography}_{estimate}_{timestamp}.csv",
                mime="text/csv"
            )
            
            st.markdown('<div class="success-box"><strong>Next:</strong> Download CSV, run <code>python 2__process_census.py</code></div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

with col_btn2:
    if st.button("🔄 Reset", use_container_width=True, key="reset"):
        st.rerun()

with st.sidebar:
    st.header("ℹ️ Info")
    st.markdown("""
    ### Workflow:
    1. Select parameters
    2. Click DOWNLOAD
    3. Data downloads
    4. Export CSV
    5. Run processing
    """)
    
    with st.expander("📊 Stats"):
        st.write(f"**Indicators:** {sum(len(p) for p in yaml_config['Indicators'].values())}")
        st.write(f"**Projects:** {len(projects)}")

st.markdown("---")
st.markdown('<div style="text-align: center; color: gray; font-size: 12px;">Census Data Pipeline | Direct Download</div>', unsafe_allow_html=True)

