import streamlit as st

st.set_page_config(
    page_title="Regional Monitoring Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0b0e17 !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(56,189,248,.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(99,102,241,.07) 0%, transparent 55%),
        #0b0e17 !important;
}

[data-testid="stHeader"]          { background: transparent !important; }
[data-testid="stSidebar"]         { background: #0f1220 !important; border-right: 1px solid rgba(255,255,255,.06); }
[data-testid="stSidebar"] *       { color: #94a3b8 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; }
section.main > div                { padding: 2rem 3rem 4rem !important; }

/* ── Typography ── */
h1, h2, h3, h4, p, span, div, label { font-family: 'DM Sans', sans-serif !important; }

/* ── Force Streamlit blocks to be full width so centering works ── */
[data-testid="stMarkdownContainer"] {
    width: 100% !important;
}

/* ── Hero ── */
.hero {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 4.5rem 1rem 3.5rem;
    position: relative;
}

.hero-eyebrow {
    font-family: 'Syne', sans-serif !important;
    font-size: .75rem;
    font-weight: 600;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: #38bdf8;
    margin-bottom: 1rem;
    width: 100%;
    text-align: center;
}

.hero-title {
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(2.4rem, 5vw, 4rem);
    font-weight: 800;
    line-height: 1.1;
    color: #f1f5f9;
    margin: 0 0 1rem;
    width: 100%;
    text-align: center;
}

.hero-title span {
    font-family: 'Syne', sans-serif !important;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 1.05rem;
    color: #64748b;
    max-width: 520px;
    width: 100%;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
    font-weight: 300;
    text-align: center;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(56,189,248,.3), rgba(129,140,248,.3), transparent);
    margin: 0 auto 3.5rem;
    max-width: 600px;
}

/* ── Section label ── */
.section-label {
    font-family: 'Syne', sans-serif !important;
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: #475569;
    text-align: center;
    margin-bottom: 1.8rem;
}

/* ── Pipeline cards ── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.25rem;
    max-width: 780px;
    margin: 0 auto 4rem;
}

.pipeline-card {
    background: linear-gradient(145deg, rgba(255,255,255,.04) 0%, rgba(255,255,255,.02) 100%);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 16px;
    padding: 2rem 1.75rem;
    position: relative;
    overflow: hidden;
    transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
    cursor: default;
}

.pipeline-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 16px;
    opacity: 0;
    transition: opacity .3s ease;
}

.pipeline-card.bls::before {
    background: radial-gradient(ellipse at top left, rgba(56,189,248,.12) 0%, transparent 65%);
}
.pipeline-card.census::before {
    background: radial-gradient(ellipse at top left, rgba(129,140,248,.12) 0%, transparent 65%);
}

.pipeline-card:hover { transform: translateY(-4px); }
.pipeline-card.bls:hover   { border-color: rgba(56,189,248,.35);  box-shadow: 0 12px 40px rgba(56,189,248,.1);  }
.pipeline-card.census:hover{ border-color: rgba(129,140,248,.35); box-shadow: 0 12px 40px rgba(129,140,248,.1); }
.pipeline-card:hover::before { opacity: 1; }

.card-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
    display: block;
}

.card-title {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.25rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0 0 .5rem;
}

.card-source {
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    margin-bottom: .85rem;
}
.bls   .card-source { color: #38bdf8; }
.census .card-source { color: #818cf8; }

.card-desc {
    font-size: .88rem;
    color: #64748b;
    line-height: 1.65;
    margin: 0 0 1.5rem;
}

.card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: .4rem;
    margin-bottom: 1.5rem;
}

.tag {
    font-size: .7rem;
    font-weight: 500;
    padding: .25rem .65rem;
    border-radius: 99px;
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.08);
    color: #94a3b8;
}

/* ── Streamlit button override ── */
div[data-testid="stButton"] > button {
    width: 100% !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-size: .85rem !important;
    font-weight: 600 !important;
    letter-spacing: .04em !important;
    padding: .65rem 1.25rem !important;
    transition: all .2s ease !important;
    border: none !important;
}

/* BLS button */
.bls-btn div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%) !important;
    color: #0b0e17 !important;
}
.bls-btn div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(56,189,248,.35) !important;
}

/* Census button */
.census-btn div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
    color: #fff !important;
}
.census-btn div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #818cf8 0%, #a5b4fc 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(129,140,248,.35) !important;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 3rem;
    max-width: 680px;
    margin: 0 auto 3.5rem;
    flex-wrap: wrap;
}

.stat-item {
    text-align: center;
}

.stat-num {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.75rem;
    font-weight: 800;
    color: #e2e8f0;
    display: block;
}

.stat-label {
    font-size: .75rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: .1em;
    font-weight: 500;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 2rem 0 .5rem;
    font-size: .75rem;
    color: #334155;
    border-top: 1px solid rgba(255,255,255,.04);
}

/* ── Sidebar polish ── */
[data-testid="stSidebarNavItems"] { margin-top: 1rem; }

/* hide default Streamlit nav header clutter */
[data-testid="stSidebarNavSeparator"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <p class="hero-eyebrow">Sacramento Area Council of Governments</p>
    <h1 class="hero-title">Regional Monitoring<br><span>Data Pipeline</span></h1>
    <p class="hero-sub">
        Automated data collection, processing, and export for regional economic
        and demographic indicators.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ─── Stats ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="stats-bar">
    <div class="stat-item">
        <span class="stat-num">4</span>
        <span class="stat-label">BLS Surveys</span>
    </div>
    <div class="stat-item">
        <span class="stat-num">25+</span>
        <span class="stat-label">Years of Data</span>
    </div>
    <div class="stat-item">
        <span class="stat-num">6</span>
        <span class="stat-label">Indicators</span>
    </div>
    <div class="stat-item">
        <span class="stat-num">2</span>
        <span class="stat-label">Pipelines</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Pipeline cards ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Choose a Pipeline</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class="pipeline-card bls">
        <span class="card-icon">📊</span>
        <p class="card-source">Bureau of Labor Statistics</p>
        <h2 class="card-title">BLS Pipeline</h2>
        <p class="card-desc">
            Pull employment, wages, and unemployment data from CES, QCEW,
            and LAUS surveys across counties, MSAs, and national geographies.
        </p>
        <div class="card-tags">
            <span class="tag">CES · SM / CE</span>
            <span class="tag">QCEW · EN</span>
            <span class="tag">LAUS · LA</span>
            <span class="tag">Jobs &amp; Labor Force</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="bls-btn">', unsafe_allow_html=True)
    if st.button("Open BLS Pipeline →", key="bls_btn", use_container_width=True):
        st.switch_page("pages/bls_wrapper.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="pipeline-card census">
        <span class="card-icon">🗂️</span>
        <p class="card-source">U.S. Census Bureau</p>
        <h2 class="card-title">Census Pipeline</h2>
        <p class="card-desc">
            Access ACS, PUMS, Decennial, and LEHD data at state, county,
            tract, block group, MSA, and place geographies with MOE support.
        </p>
        <div class="card-tags">
            <span class="tag">ACS 1yr / 5yr</span>
            <span class="tag">PUMS</span>
            <span class="tag">Decennial</span>
            <span class="tag">LEHD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="census-btn">', unsafe_allow_html=True)
    if st.button("Open Census Pipeline →", key="census_btn", use_container_width=True):
        st.switch_page("pages/census_wrapper.py")
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Regional Monitoring &amp; Reporting · SACOG Data Team
</div>
""", unsafe_allow_html=True)