import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
import tempfile

st.set_page_config(page_title="GeoFlood", page_icon="🌊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.hero {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 16px;
    padding: 36px 32px;
    margin-bottom: 20px;
    text-align: center;
    color: white;
}
.hero h1 { font-size: 2.4rem; font-weight: 700; margin: 0; }
.hero p  { font-size: 1rem; opacity: 0.85; margin-top: 6px; }
.section-box {
    background: #111827;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #1f2937;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid #1a6bff;
}
.metric-card {
    background: #1a1a2e;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    color: white;
    border: 1px solid #0f3460;
    height: 100%;
}
.metric-card .label { font-size: 0.8rem; opacity: 0.65; margin-bottom: 6px; }
.metric-card .value { font-size: 1.9rem; font-weight: 700; }
.metric-card .sub   { font-size: 0.78rem; margin-top: 4px; }
.flood-card  { border-top: 3px solid #e74c3c !important; }
.total-card  { border-top: 3px solid #3498db !important; }
.safe-card   { border-top: 3px solid #2ecc71 !important; }
.rain-card   { border-top: 3px solid #9b59b6 !important; }
.risk-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 700;
    margin: 4px 2px;
}
.badge-high     { background:#ff000033; color:#ff4444; border:1px solid #ff4444; }
.badge-moderate { background:#ffaa0033; color:#ffaa00; border:1px solid #ffaa00; }
.badge-low      { background:#ff660033; color:#ff6600; border:1px solid #ff6600; }
.badge-safe     { background:#00cc6633; color:#00cc66; border:1px solid #00cc66; }
.rain-result {
    background: #111827;
    border-radius: 10px;
    padding: 16px;
    color: white;
    border-left: 4px solid #9b59b6;
    margin-top: 10px;
}
.info-banner {
    background: linear-gradient(90deg, #0f2027, #203a43);
    border-radius: 10px;
    padding: 14px 18px;
    color: white;
    border-left: 4px solid #2ecc71;
    margin-top: 16px;
}
.step-box {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    color: white;
    border-left: 3px solid #1a6bff;
    font-size: 0.88rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🌊 GeoFlood</h1>
    <p>Flood Detection & Building Impact Assessment using Satellite Imagery</p>
    <p style="font-size:0.8rem;opacity:0.55;margin-top:2px">
        Sentinel-2 • OpenStreetMap • NDWI Analysis • Risk Classification
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛰️ Analysis Controls")
    st.markdown("---")
    with st.expander("📁 Satellite Image", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload Sentinel GeoTIFF",
            type=["tif", "tiff"]
        )
    with st.expander("📍 Location", expanded=True):
        place_name = st.text_input(
            "City / Region",
            placeholder="e.g. Haridwar, India"
        )
    with st.expander("⚙️ Detection Settings", expanded=False):
        ndwi_threshold = st.slider(
            "NDWI Threshold", 0.0, 1.0, 0.2, 0.05
        )
    with st.expander("🌧️ Rainfall Analysis", expanded=True):
        rainfall_mm = st.number_input(
            "Rainfall amount (mm)",
            min_value=0.0, max_value=1000.0,
            value=0.0, step=10.0
        )
        rainfall_hours = st.slider("Duration (hours)", 1, 72, 24)
    st.markdown("---")
    run_btn = st.button(
        "🚀 Run Full Analysis",
        type="primary",
        use_container_width=True
    )
    st.markdown("---")
    st.markdown("""
    <div style='color:gray;font-size:0.72rem;text-align:center'>
        GeoFlood v1.0<br>Dinesh · Likhitha · Gayatri
    </div>""", unsafe_allow_html=True)

# ── Rainfall function ─────────────────────────────────────────────
def analyse_rainfall(mm, hours):
    intensity = mm / hours if hours > 0 else 0
    if mm == 0:
        return None
    if mm < 25:
        return {"risk":"Low","emoji":"🟢","color":"#2ecc71",
                "advice":"Light rainfall. Minimal flood risk.",
                "expected":"< 5%","intensity":round(intensity,2)}
    elif mm < 65:
        return {"risk":"Moderate","emoji":"🟡","color":"#f39c12",
                "advice":"Some low-lying areas may experience waterlogging.",
                "expected":"5%–20%","intensity":round(intensity,2)}
    elif mm < 115:
        return {"risk":"High","emoji":"🔴","color":"#e74c3c",
                "advice":"Heavy rainfall! Significant flood risk.",
                "expected":"20%–50%","intensity":round(intensity,2)}
    else:
        return {"risk":"Extreme","emoji":"🚨","color":"#c0392b",
                "advice":"Extreme rainfall! Immediate evacuation advised.",
                "expected":"> 50%","intensity":round(intensity,2)}

# ── Rainfall Section ──────────────────────────────────────────────
if rainfall_mm > 0:
    r = analyse_rainfall(rainfall_mm, rainfall_hours)
    if r:
        st.markdown("""
        <div class="section-box">
            <div class="section-title">🌧️ Rainfall Risk Assessment</div>
        </div>""", unsafe_allow_html=True)

        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.markdown(f"""
        <div class="metric-card rain-card">
            <div class="label">Rainfall</div>
            <div class="value">{rainfall_mm}mm</div>
            <div class="sub">Total amount</div>
        </div>""", unsafe_allow_html=True)
        rc2.markdown(f"""
        <div class="metric-card rain-card">
            <div class="label">Duration</div>
            <div class="value">{rainfall_hours}h</div>
            <div class="sub">Hours</div>
        </div>""", unsafe_allow_html=True)
        rc3.markdown(f"""
        <div class="metric-card rain-card">
            <div class="label">Intensity</div>
            <div class="value">{r['intensity']}</div>
            <div class="sub">mm/hour</div>
        </div>""", unsafe_allow_html=True)
        rc4.markdown(f"""
        <div class="metric-card rain-card">
            <div class="label">Risk Level</div>
            <div class="value">{r['emoji']}</div>
            <div class="sub" style="color:{r['color']}">{r['risk']}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="rain-result">
            <b>Risk:</b>
            <span style="color:{r['color']};font-weight:700">
                {r['emoji']} {r['risk']}
            </span>
            &nbsp;|&nbsp;
            <b>Expected buildings affected:</b> {r['expected']}<br><br>
            📋 <b>Advisory:</b> {r['advice']}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
if "done" not in st.session_state:
    st.session_state.done = False

# ── Run Analysis ──────────────────────────────────────────────────
if run_btn:
    if not uploaded_file or not place_name:
        st.warning("⚠️ Upload a GeoTIFF and enter a location name.")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        from src.utils.dummy_data import (
            dummy_flood_polygons,
            dummy_buildings,
            dummy_flooded_buildings
        )
        with st.spinner("🛰️ Processing satellite image..."):
            flood_gdf     = dummy_flood_polygons()
        with st.spinner("🗺️ Fetching buildings from OpenStreetMap..."):
            buildings_gdf = dummy_buildings()
            flooded_gdf   = dummy_flooded_buildings()

        total   = len(buildings_gdf)
        flooded = len(flooded_gdf)
        pct     = round((flooded / total) * 100, 1) if total else 0
        safe    = total - flooded

        from src.utils.map_utils import create_map
        m        = create_map(flood_gdf, buildings_gdf, flooded_gdf)
        map_html = m._repr_html_()

        st.session_state.done     = True
        st.session_state.total    = total
        st.session_state.flooded  = flooded
        st.session_state.pct      = pct
        st.session_state.safe     = safe
        st.session_state.map_html = map_html
        st.session_state.place    = place_name

    finally:
        os.unlink(tmp_path)

# ── Results ───────────────────────────────────────────────────────
if st.session_state.done:
    total   = st.session_state.total
    flooded = st.session_state.flooded
    pct     = st.session_state.pct
    safe    = st.session_state.safe

    # Metrics
    st.markdown("""
    <div class="section-box">
        <div class="section-title">📊 Impact Metrics</div>
    </div>""", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.markdown(f"""
    <div class="metric-card total-card">
        <div class="label">Total Buildings</div>
        <div class="value">{total}</div>
        <div class="sub">In selected area</div>
    </div>""", unsafe_allow_html=True)
    m2.markdown(f"""
    <div class="metric-card flood-card">
        <div class="label">Flooded Buildings</div>
        <div class="value">{flooded}</div>
        <div class="sub" style="color:#e74c3c">{pct}% affected</div>
    </div>""", unsafe_allow_html=True)
    m3.markdown(f"""
    <div class="metric-card safe-card">
        <div class="label">Safe Buildings</div>
        <div class="value">{safe}</div>
        <div class="sub" style="color:#2ecc71">{100-pct}% safe</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Risk summary
    st.markdown("""
    <div class="section-box">
        <div class="section-title">⚠️ Risk Classification Summary</div>
        <div style="color:#ccc;font-size:0.88rem;line-height:2">
            <span class="risk-badge badge-high">🔴 High Risk</span>
            Buildings &gt;70% inside flood zone — Immediate evacuation<br>
            <span class="risk-badge badge-moderate">🟡 Moderate Risk</span>
            Buildings 30–70% inside flood zone — Monitor closely<br>
            <span class="risk-badge badge-low">🟠 Low Risk</span>
            Buildings &lt;30% inside flood zone — Stay alert<br>
            <span class="risk-badge badge-safe">🟢 Safe</span>
            Buildings outside flood zone — No immediate action
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Map + Chart
    st.markdown("""
    <div class="section-title" style="color:white;font-size:1.1rem;
    font-weight:700;padding-left:12px;border-left:3px solid #1a6bff">
        🗺️ Interactive Flood Map
        <small style="font-size:0.75rem;opacity:0.6;font-weight:400">
        &nbsp;&nbsp;Switch layers: Satellite / Street / Terrain
        </small>
    </div>""", unsafe_allow_html=True)

    map_col, info_col = st.columns([3, 2])

    with map_col:
        st.components.v1.html(
            st.session_state.map_html, height=480)

    with info_col:
        st.markdown("""
        <div class="section-title" style="color:white;
        font-size:1rem;font-weight:700">
            📈 Impact Summary
        </div>""", unsafe_allow_html=True)

        from src.utils.chart_utils import impact_chart
        fig = impact_chart(total, flooded)
        st.pyplot(fig)                      # ← fixed line

        st.markdown("""
        <div class="section-box" style="margin-top:12px">
            <div style="color:#ccc;font-size:0.83rem">
                <b style="color:white">📋 How to use the map:</b><br>
                <div class="step-box">
                    1️⃣ Top-right panel: switch Satellite / Street / Terrain
                </div>
                <div class="step-box">
                    2️⃣ Click red/orange buildings for risk details
                </div>
                <div class="step-box">
                    3️⃣ Toggle layers on/off with checkboxes
                </div>
                <div class="step-box">
                    4️⃣ Fullscreen button (top-left) for better view
                </div>
                <div class="step-box">
                    5️⃣ Mini-map (bottom-left) shows your position
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    # Completion banner
    st.markdown(f"""
    <div class="info-banner">
        ✅ <b>Analysis complete!</b> —
        Location: <b>{st.session_state.place}</b> |
        {total} buildings scanned |
        {flooded} flooded ({pct}%) |
        {safe} safe ({100-pct}%)<br>
        <small style="opacity:0.7">
            Currently using dummy data.
            Connect real Sentinel-2 image for production results.
        </small>
    </div>
    """, unsafe_allow_html=True)
