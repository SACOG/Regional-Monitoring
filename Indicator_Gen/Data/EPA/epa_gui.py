"""

EPA Data Request Pipeline - Streamlit GUI

This is a web-based GUI for the EPA data request pipeline.
Much more user-friendly than command-line prompts!

Installation:
    pip install streamlit pyyaml pandas

Usage:
    streamlit run epa_gui.py

"""

import streamlit as st
import yaml
from pathlib import Path
import pandas as pd
import sys
from datetime import datetime
import urllib.request
import json
import time
from tqdm import tqdm

# ===============================================
# PAGE CONFIGURATION
# ===============================================

st.set_page_config(
    page_title="EPA Data Request",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================================
# STYLING
# ===============================================

st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        height: 50px;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ===============================================
# FILE PATHS & CONFIG
# ===============================================

try:
    # Get the config path (adjust based on your structure)
    path_config = Path(__file__).parent / 'config'
    path_yaml = path_config / 'epa_indicators.yaml'
    
    if not path_yaml.exists():
        st.error(f"❌ Config file not found: {path_yaml}")
        st.stop()
    
    # Load YAML configuration
    with open(path_yaml, 'r') as f:
        yaml_config = yaml.load(f, Loader=yaml.SafeLoader)
    
except Exception as e:
    st.error(f"❌ Error loading configuration: {str(e)}")
    st.stop()

# ===============================================
# HELPER FUNCTIONS
# ===============================================

def load_api_key():
    """Load API key from config"""
    try:
        api_key_file = path_config / 'api_key.txt'
        exec(open(api_key_file).read(), globals())
        return dict_api
    except:
        return None

def get_available_options(api_source, indicator):
    """Get available options for selected indicator"""
    try:
        config = yaml_config['Indicators'][api_source][indicator]
        return config
    except:
        return None

def save_run_log(selections):
    """Save run selections to audit log"""
    try:
        runs_dir = path_config / 'runs'
        runs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = runs_dir / f"{timestamp}_epa_run.csv"
        
        # Create DataFrame from selections
        df_log = pd.DataFrame({
            'Parameter': list(selections.keys()),
            'Input': list(selections.values())
        })
        
        # Save with ': ' delimiter
        with open(log_file, 'w') as f:
            for idx, row in df_log.iterrows():
                f.write(f"{row['Parameter']}: {row['Input']}\n")
        
        return log_file
    except Exception as e:
        st.error(f"Error saving run log: {str(e)}")
        return None

def build_epa_request(api_source, indicator, geography, years, pollutants, api_key_dict):
    """Build and execute EPA API request"""
    try:
        # Get configuration
        config = get_available_options(api_source, indicator)
        
        if not config:
            st.error("Invalid configuration selected")
            return None
        
        # Extract config values
        root_url = config['root_url']
        email = config['email']
        data_endpoint = config['data_endpoint']
        geo_type = config['geo_type']
        
        # Get API key
        api_key = api_key_dict.get(api_source)
        if not api_key:
            st.error(f"API key not found for {api_source}")
            return None
        
        # Parse geography and pollutant selections
        geo_list = geography.split(', ')
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        data_container = st.empty()
        
        all_data = []
        total_requests = len(geo_list) * len(pollutants) * len(years)
        current_request = 0
        
        # Make API requests
        for geo in geo_list:
            for pollutant in pollutants:
                for year in years:
                    current_request += 1
                    progress = current_request / total_requests
                    progress_bar.progress(progress)
                    status_text.text(f"Downloading... {geo} | {pollutant} | {year} ({current_request}/{total_requests})")
                    
                    try:
                        # Build URL
                        url = (
                            f"{root_url}{data_endpoint}/by{geo_type}?"
                            f"email={email}&key={api_key}&param={pollutant}&"
                            f"bdate={year}0101&edate={year}1231&{geo_type.lower()}={geo}"
                        )
                        
                        # Make request
                        with urllib.request.urlopen(url) as response:
                            data = json.load(response)
                        
                        if 'Data' in data and data['Data']:
                            df = pd.DataFrame(data['Data'])
                            df['Year_Imported'] = year
                            df['Pollutant_Code'] = pollutant
                            all_data.append(df)
                        
                        # Respect EPA rate limit
                        time.sleep(6)
                    
                    except Exception as e:
                        st.warning(f"⚠️ Error for {geo} | {pollutant} | {year}: {str(e)[:50]}")
                        continue
        
        progress_bar.empty()
        status_text.empty()
        
        # Combine all data
        if all_data:
            df_result = pd.concat(all_data, ignore_index=True)
            return df_result
        else:
            st.error("❌ No data downloaded")
            return None
    
    except Exception as e:
        st.error(f"Error during request: {str(e)}")
        return None

# ===============================================
# PAGE LAYOUT
# ===============================================

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🌍 EPA Data Request Pipeline")
    st.markdown("Interactive GUI for downloading EPA air quality data")

st.markdown("---")

# ===============================================
# MAIN CONTENT
# ===============================================

# Create two columns: settings and preview
col_settings, col_preview = st.columns([1, 1])

with col_settings:
    st.header("📋 Configure Request")
    
    # Step 1: Select API Source
    st.subheader("Step 1: API Source")
    api_sources = list(yaml_config['Indicators'].keys())
    api_source = st.selectbox(
        "Which EPA API source?",
        options=api_sources,
        help="Choose the EPA data source"
    )
    
    # Step 2: Select Indicator
    st.subheader("Step 2: Indicator")
    indicators = list(yaml_config['Indicators'][api_source].keys())
    indicator = st.selectbox(
        "Which indicator?",
        options=indicators,
        help="Select the specific indicator to download"
    )
    
    # Get selected indicator config
    indicator_config = get_available_options(api_source, indicator)
    
    if indicator_config:
        # Step 3: Select Geographies
        st.subheader("Step 3: Geographies")
        available_geos = indicator_config.get('available_geographies', [])
        geo_options = {f"{g['name']} ({g['code']})": g['code'] for g in available_geos}
        
        selected_geos = st.multiselect(
            "Which geographies? (select one or more)",
            options=list(geo_options.keys()),
            default=list(geo_options.keys())[0] if geo_options else None,
            help="You can select multiple geographies"
        )
        
        geography = ', '.join([geo_options[g] for g in selected_geos])
        
        # Step 4: Select Years
        st.subheader("Step 4: Years")
        year_range = indicator_config.get('year_range', {})
        year_min = year_range.get('min', 1999)
        year_max = year_range.get('max', 2024)
        
        year_selection = st.radio(
            "Select year range:",
            options=['Custom range', 'Single year', 'Last 3 years', 'All available'],
            horizontal=True
        )
        
        if year_selection == 'Custom range':
            col_y1, col_y2 = st.columns(2)
            with col_y1:
                start_year = st.number_input("Start year:", min_value=year_min, max_value=year_max, value=year_max-2)
            with col_y2:
                end_year = st.number_input("End year:", min_value=year_min, max_value=year_max, value=year_max)
            years = list(range(start_year, end_year + 1))
        
        elif year_selection == 'Single year':
            year = st.number_input("Which year?", min_value=year_min, max_value=year_max, value=year_max)
            years = [year]
        
        elif year_selection == 'Last 3 years':
            years = [year_max-2, year_max-1, year_max]
        
        else:  # All available
            years = list(range(year_min, year_max + 1))
        
        # Step 5: Select Pollutants
        st.subheader("Step 5: Pollutants")
        available_pollutants = indicator_config.get('available_pollutants', [])
        pollutant_options = {p['name']: p['code'] for p in available_pollutants}
        
        selected_pollutants = st.multiselect(
            "Which pollutants? (select one or more)",
            options=list(pollutant_options.keys()),
            default=list(pollutant_options.keys()) if pollutant_options else None,
            help="You can select multiple pollutants"
        )
        
        pollutants = [pollutant_options[p] for p in selected_pollutants]

with col_preview:
    st.header("📊 Preview")
    
    # Show configuration summary
    if indicator_config:
        st.markdown("""
        <div class="info-box">
        <strong>Configuration Summary</strong><br>
        </div>
        """, unsafe_allow_html=True)
        
        summary_data = {
            'Setting': [
                'API Source',
                'Indicator',
                'Display Name',
                'Geographies Selected',
                'Years Selected',
                'Pollutants Selected',
                'Total Requests'
            ],
            'Value': [
                api_source,
                indicator,
                indicator_config.get('display_name', 'N/A'),
                len(selected_geos) if selected_geos else 0,
                f"{min(years)} to {max(years)}" if years else "None",
                len(selected_pollutants) if selected_pollutants else 0,
                len(selected_geos) * len(selected_pollutants) * len(years) if (selected_geos and selected_pollutants and years) else 0
            ]
        }
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
        # Show note about time
        if years and selected_pollutants and selected_geos:
            total_requests = len(selected_geos) * len(selected_pollutants) * len(years)
            estimated_time = (total_requests * 6) / 60  # 6 seconds per request
            st.info(f"⏱️ Estimated download time: ~{estimated_time:.1f} minutes ({total_requests} API requests)")

# ===============================================
# ACTION BUTTONS
# ===============================================

st.markdown("---")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn1:
    if st.button("📥 Download Data", key="download_btn"):
        if not selected_geos or not selected_pollutants or not years:
            st.error("❌ Please select at least one option in each category")
        else:
            # Load API key
            api_key_dict = load_api_key()
            if not api_key_dict:
                st.error("❌ Could not load API keys. Check config/api_key.txt")
            else:
                # Show download progress
                with st.spinner("Downloading data from EPA..."):
                    df_data = build_epa_request(
                        api_source, indicator, geography, years, 
                        pollutants, api_key_dict
                    )
                
                if df_data is not None and len(df_data) > 0:
                    st.success(f"✅ Downloaded {len(df_data)} rows successfully!")
                    
                    # Save selections to audit log
                    selections = {
                        'API Source': api_source,
                        'Indicator': indicator,
                        'Geographies': geography,
                        'Years': ', '.join(map(str, years)),
                        'Pollutants': ', '.join(pollutants),
                        'Downloaded Rows': len(df_data)
                    }
                    log_file = save_run_log(selections)
                    if log_file:
                        st.success(f"✅ Run logged to: {log_file}")
                    
                    # Show data preview
                    st.subheader("Data Preview")
                    st.dataframe(df_data.head(10), use_container_width=True)
                    
                    # Download button
                    csv = df_data.to_csv(index=False)
                    st.download_button(
                        label="💾 Download as CSV",
                        data=csv,
                        file_name=f"{indicator}_{api_source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Store in session for later processing
                    st.session_state.downloaded_data = df_data

with col_btn2:
    if st.button("🔄 Reset Form", key="reset_btn"):
        st.rerun()

with col_btn3:
    st.button("ℹ️ Help", key="help_btn", disabled=True)

# ===============================================
# SIDEBAR - INFORMATION
# ===============================================

with st.sidebar:
    st.header("ℹ️ Information")
    
    st.markdown("""
    ### About This Tool
    This GUI helps you download air quality data from the EPA APIs.
    
    ### How It Works
    1. Select your API source (AQI, CAM)
    2. Choose an indicator
    3. Pick geographies (cities/regions)
    4. Select years
    5. Choose pollutants
    6. Click "Download Data"
    
    ### API Rate Limiting
    EPA requires 6 seconds between requests. The estimated time shown accounts for this.
    
    ### Data Quality
    - All selections are logged for reproducibility
    - Data is validated before download
    - Check the preview for data quality
    
    ### Need Help?
    - 📖 Check documentation
    - 🔍 Review configuration in YAML
    - 📧 Contact EPA support
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### Configuration Files
    - `epa_indicators.yaml` - Indicator definitions
    - `api_key.txt` - API credentials
    - `runs/` - Audit trail of downloads
    """)
    
    st.markdown("---")
    
    # Show available indicators
    st.subheader("Available Indicators")
    for source, indicators in yaml_config['Indicators'].items():
        with st.expander(f"📊 {source}"):
            for ind, config in indicators.items():
                display_name = config.get('display_name', ind)
                st.write(f"• **{ind}** - {display_name}")

# ===============================================
# FOOTER
# ===============================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    EPA Data Request Pipeline v2.0 | Powered by Streamlit<br>
    Last updated: 2024 | Data source: EPA APIs
</div>
""", unsafe_allow_html=True)

