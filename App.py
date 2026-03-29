import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import tempfile
import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import Polygon, box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(page_title="GeoFlood", page_icon="🌊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Exo+2:wght@300;400;600;700&display=swap');

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
}

/* ── FLOOD BACKGROUND ─────────────────────────────────────────── */
.stApp {
    background-color: #020c18;
    background-image:
        url("https://images.unsplash.com/photo-1547683905-f686c993aae4?w=1800&q=80"),
        linear-gradient(180deg, rgba(2,12,24,0.92) 0%, rgba(5,20,40,0.88) 100%);
    background-blend-mode: multiply;
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

/* dark overlay so content stays readable */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background: linear-gradient(
        160deg,
        rgba(0,10,30,0.80) 0%,
        rgba(0,30,60,0.65) 50%,
        rgba(0,10,25,0.85) 100%
    );
    pointer-events: none;
    z-index: 0;
}

/* ── HERO ─────────────────────────────────────────────────────── */
.hero {
    position: relative;
    background: linear-gradient(135deg,
        rgba(0,40,80,0.85) 0%,
        rgba(0,80,160,0.60) 50%,
        rgba(0,40,80,0.85) 100%);
    border: 1px solid rgba(0,180,255,0.25);
    border-radius: 20px;
    padding: 48px 40px 40px;
    margin-bottom: 28px;
    text-align: center;
    color: white;
    overflow: hidden;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 48px rgba(0,120,255,0.18), 0 2px 0 rgba(0,180,255,0.3) inset;
}

.hero::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #00c8ff, #0055ff, #00c8ff, transparent);
    animation: shimmer 3s infinite linear;
}

@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}

.hero-icon {
    font-size: 3.6rem;
    display: block;
    margin-bottom: 10px;
    filter: drop-shadow(0 0 20px rgba(0,200,255,0.7));
    animation: float 4s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-8px); }
}

.hero h1 {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3.2rem;
    font-weight: 700;
    margin: 0 0 8px;
    letter-spacing: 4px;
    text-transform: uppercase;
    background: linear-gradient(90deg, #ffffff, #00c8ff, #ffffff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero p {
    font-size: 1.05rem;
    opacity: 0.80;
    margin: 4px 0;
    letter-spacing: 0.5px;
}

.hero-tags {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}

.hero-tag {
    background: rgba(0,150,255,0.15);
    border: 1px solid rgba(0,150,255,0.35);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    color: #7dd3fc;
    letter-spacing: 0.5px;
}

/* ── SECTION BOX ─────────────────────────────────────────────── */
.section-box {
    background: rgba(5,15,35,0.75);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
    border: 1px solid rgba(0,100,200,0.22);
    backdrop-filter: blur(10px);
}

.section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: white;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,150,255,0.30);
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── METRIC CARDS ─────────────────────────────────────────────── */
.metric-card {
    background: rgba(5,15,35,0.80);
    border-radius: 14px;
    padding: 22px 16px;
    text-align: center;
    color: white;
    border: 1px solid rgba(0,100,200,0.20);
    height: 100%;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(8px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0,100,255,0.20);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}

.flood-card::before  { background: linear-gradient(90deg, #e74c3c, #ff6b6b); }
.total-card::before  { background: linear-gradient(90deg, #2980b9, #5dade2); }
.safe-card::before   { background: linear-gradient(90deg, #27ae60, #58d68d); }
.rain-card::before   { background: linear-gradient(90deg, #8e44ad, #c39bd3); }

.metric-card .label {
    font-size: 0.75rem;
    opacity: 0.60;
    margin-bottom: 8px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.metric-card .value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1.1;
}

.metric-card .sub {
    font-size: 0.78rem;
    margin-top: 6px;
    opacity: 0.70;
}

/* ── RISK BADGES ─────────────────────────────────────────────── */
.risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 4px 4px;
    letter-spacing: 0.3px;
}

.badge-high     { background: rgba(255,0,0,0.12);   color: #ff5555; border: 1px solid rgba(255,60,60,0.40); }
.badge-moderate { background: rgba(255,170,0,0.12); color: #ffbb33; border: 1px solid rgba(255,170,0,0.40); }
.badge-low      { background: rgba(255,100,0,0.12); color: #ff8844; border: 1px solid rgba(255,100,0,0.40); }
.badge-safe     { background: rgba(0,200,100,0.12); color: #33dd88; border: 1px solid rgba(0,200,100,0.40); }

/* ── RAIN RESULT ─────────────────────────────────────────────── */
.rain-result {
    background: rgba(80,30,120,0.25);
    border-radius: 12px;
    padding: 16px 20px;
    color: white;
    border-left: 4px solid #9b59b6;
    margin-top: 14px;
    backdrop-filter: blur(8px);
    font-size: 0.92rem;
    line-height: 1.8;
}

/* ── INFO BANNER ─────────────────────────────────────────────── */
.info-banner {
    background: rgba(0,60,20,0.40);
    border-radius: 12px;
    padding: 16px 20px;
    color: white;
    border-left: 4px solid #2ecc71;
    margin-top: 18px;
    backdrop-filter: blur(8px);
    font-size: 0.90rem;
    line-height: 1.7;
}

/* ── SIDEBAR ─────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(2,10,25,0.90) !important;
    border-right: 1px solid rgba(0,100,200,0.20) !important;
    backdrop-filter: blur(16px);
}

section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #0050c8, #0088ff) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 12px 0 !important;
    box-shadow: 0 4px 20px rgba(0,100,255,0.35) !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    box-shadow: 0 6px 28px rgba(0,150,255,0.55) !important;
    transform: translateY(-2px) !important;
}

/* ── MAP CONTAINER ──────────────────────────────────────────── */
.map-container {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(0,150,255,0.25);
    box-shadow: 0 8px 40px rgba(0,50,150,0.30);
}

.map-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0 0 14px 0;
    border-bottom: 1px solid rgba(0,150,255,0.20);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.map-subtitle {
    font-size: 0.73rem;
    opacity: 0.50;
    font-weight: 400;
    letter-spacing: 0.5px;
    font-family: 'Exo 2', sans-serif;
    text-transform: none;
}
</style>
""", unsafe_allow_html=True)

# ── HERO ────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <span class="hero-icon">🌊</span>
    <h1>GeoFlood</h1>
    <p>Flood Detection &amp; Building Impact Assessment using Satellite Imagery</p>
    <div class="hero-tags">
        <span class="hero-tag">📡 Sentinel-2</span>
        <span class="hero-tag">🗺️ OpenStreetMap</span>
        <span class="hero-tag">📊 NDWI Analysis</span>
        <span class="hero-tag">⚠️ Risk Classification</span>
        <span class="hero-tag">🏢 Building Detection</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── HELPERS ─────────────────────────────────────────────────────
def dummy_flood_polygons():
    polys = [
        Polygon([(78.155,29.940),(78.175,29.940),(78.175,29.955),(78.155,29.955)]),
        Polygon([(78.170,29.935),(78.185,29.935),(78.185,29.948),(78.170,29.948)]),
    ]
    return gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326")


def dummy_buildings():
    flood_blds = [box(78.156+i*0.003, 29.941, 78.158+i*0.003, 29.943) for i in range(5)]
    safe_blds  = [box(78.140+i*0.004, 29.960, 78.142+i*0.004, 29.962) for i in range(15)]
    return gpd.GeoDataFrame(geometry=flood_blds+safe_blds, crs="EPSG:4326")


def dummy_flooded_buildings():
    blds = [box(78.156+i*0.003, 29.941, 78.158+i*0.003, 29.943) for i in range(5)]
    return gpd.GeoDataFrame(geometry=blds, crs="EPSG:4326")


def impact_chart(total_buildings, flooded_buildings):
    safe = total_buildings - flooded_buildings
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))
    fig.patch.set_facecolor("#05111f")
    for ax in (ax1, ax2):
        ax.set_facecolor("#05111f")

    sizes  = [flooded_buildings, safe]
    colors = ["#E24B4A", "#1D9E75"]
    wedges, _ = ax1.pie(sizes, colors=colors, startangle=90,
                        wedgeprops={"width": 0.55, "edgecolor": "#05111f", "linewidth": 3})
    ax1.set_title("Building Impact", fontsize=12, fontweight="bold",
                  pad=15, color="white")
    patches = [
        mpatches.Patch(color="#E24B4A", label=f"Flooded  ({flooded_buildings})"),
        mpatches.Patch(color="#1D9E75", label=f"Safe  ({safe})")
    ]
    ax1.legend(handles=patches, loc="lower center",
               bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9,
               facecolor="#0a1a30", edgecolor="none", labelcolor="white")

    categories = ["Total", "Flooded", "Safe"]
    values     = [total_buildings, flooded_buildings, safe]
    bar_colors = ["#2980b9", "#E24B4A", "#1D9E75"]
    bars = ax2.bar(categories, values, color=bar_colors,
                   edgecolor="#05111f", linewidth=2, width=0.5)
    for bar, val in zip(bars, values):
        ax2.text(bar.get_x()+bar.get_width()/2,
                 bar.get_height()+0.3, str(val),
                 ha="center", va="bottom", fontsize=11,
                 fontweight="bold", color="white")
    ax2.set_title("Building Count", fontsize=12, fontweight="bold", color="white")
    ax2.set_ylabel("Number of buildings", color="#aaa", fontsize=9)
    ax2.tick_params(colors="white")
    ax2.spines[["top","right","left","bottom"]].set_color("#1a2a3a")
    ax2.set_ylim(0, total_buildings*1.25)
    ax2.yaxis.grid(True, color="#1a2a3a", linestyle="--", alpha=0.6)
    ax2.set_axisbelow(True)
    plt.tight_layout()
    return fig


def get_risk_level(building_geom, flood_gdf):
    try:
        total_area = building_geom.area
        if total_area == 0:
            return "low"
        intersection_area = 0
        for _, flood_row in flood_gdf.iterrows():
            if building_geom.intersects(flood_row.geometry):
                intersection_area += building_geom.intersection(flood_row.geometry).area
        pct = (intersection_area / total_area) * 100
        if pct >= 70:   return "high"
        elif pct >= 30: return "moderate"
        elif pct > 0:   return "low"
        else:           return "none"
    except:
        return "low"


def create_map(flood_gdf, buildings_gdf, flooded_gdf):
    center_lat, center_lon = 29.9457, 78.1642
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )
    folium.TileLayer("OpenStreetMap", name="🗺️ OpenStreetMap").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="🏔️ Terrain Map"
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="🛰️ Satellite Map"
    ).add_to(m)

    # Flood zones
    flood_layer = folium.FeatureGroup(name="🌊 Flood Zone", show=True)
    for idx, row in flood_gdf.iterrows():
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x: {"fillColor":"#0055ff","color":"#0033aa","weight":2.5,"fillOpacity":0.4},
            tooltip=f"🌊 Flood Zone {idx+1}"
        ).add_to(flood_layer)
    flood_layer.add_to(m)

    high_zone = folium.FeatureGroup(name="🔴 High Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            core = row.geometry.buffer(-0.0002)
            if not core.is_empty:
                folium.GeoJson(core.__geo_interface__,
                    style_function=lambda x: {"fillColor":"#ff0000","color":"#cc0000","weight":1.5,"fillOpacity":0.35},
                    tooltip="🔴 HIGH RISK — Core flood area").add_to(high_zone)
        except: pass
    high_zone.add_to(m)

    mod_zone = folium.FeatureGroup(name="🟡 Moderate Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            ring = row.geometry.buffer(0.0006).difference(row.geometry)
            if not ring.is_empty:
                folium.GeoJson(ring.__geo_interface__,
                    style_function=lambda x: {"fillColor":"#ffcc00","color":"#cc9900","weight":1.5,"fillOpacity":0.25},
                    tooltip="🟡 MODERATE RISK — Buffer zone").add_to(mod_zone)
        except: pass
    mod_zone.add_to(m)

    low_zone = folium.FeatureGroup(name="🟠 Low Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            ring = row.geometry.buffer(0.0012).difference(row.geometry.buffer(0.0006))
            if not ring.is_empty:
                folium.GeoJson(ring.__geo_interface__,
                    style_function=lambda x: {"fillColor":"#ff8800","color":"#cc6600","weight":1,"fillOpacity":0.15},
                    tooltip="🟠 LOW RISK — Watch zone").add_to(low_zone)
        except: pass
    low_zone.add_to(m)

    flooded_idx = set(flooded_gdf.index.tolist())
    safe_layer  = folium.FeatureGroup(name="🟢 Safe Buildings", show=True)
    for idx, row in buildings_gdf.iterrows():
        if idx not in flooded_idx:
            c = row.geometry.centroid
            folium.GeoJson(row.geometry.__geo_interface__,
                style_function=lambda x: {"fillColor":"#00dd77","color":"#009944","weight":1.5,"fillOpacity":0.7},
                tooltip="🟢 Safe Building",
                popup=folium.Popup(
                    f"<div style='font-family:Arial;width:180px'>"
                    f"<b style='color:green'>🟢 Safe Building</b><hr>"
                    f"Status: Outside flood zone<br>Lat: {c.y:.5f}<br>Lon: {c.x:.5f}</div>",
                    max_width=200)
            ).add_to(safe_layer)
    safe_layer.add_to(m)

    high_bld = folium.FeatureGroup(name="🔴 High Risk Buildings", show=True)
    mod_bld  = folium.FeatureGroup(name="🟡 Moderate Risk Buildings", show=True)
    low_bld  = folium.FeatureGroup(name="🟠 Low Risk Buildings", show=True)

    for i, (idx, row) in enumerate(flooded_gdf.iterrows()):
        c    = row.geometry.centroid
        risk = get_risk_level(row.geometry, flood_gdf)
        cfg  = {
            "high":     ("#ff2222","#aa0000","🔴 HIGH RISK","red",high_bld,"🚨 Immediate evacuation required!"),
            "moderate": ("#ffbb00","#cc8800","🟡 MODERATE RISK","orange",mod_bld,"⚠️ Monitor closely, prepare to evacuate"),
            "low":      ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",low_bld,"ℹ️ Stay alert, follow local updates"),
        }.get(risk, ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",low_bld,"ℹ️ Stay alert"))
        fill, border, label, color, target, action = cfg
        popup = folium.Popup(
            f"<div style='font-family:Arial;width:210px;padding:6px'>"
            f"<h4 style='color:{color};margin:0 0 6px'>{label}</h4>"
            f"<hr style='margin:4px 0'>"
            f"<b>Building:</b> #{i+1}<br>"
            f"<b>Risk:</b> <span style='color:{color};font-weight:700'>{risk.upper()}</span><br>"
            f"<b>Lat:</b> {c.y:.5f}<br><b>Lon:</b> {c.x:.5f}<br>"
            f"<hr style='margin:4px 0'><b>Action:</b> {action}</div>",
            max_width=230)
        folium.GeoJson(row.geometry.__geo_interface__,
            style_function=lambda x, f=fill, b=border: {"fillColor":f,"color":b,"weight":2.5,"fillOpacity":0.85},
            tooltip=f"{label} — Building #{i+1}", popup=popup
        ).add_to(target)
        folium.CircleMarker(
            location=[c.y, c.x], radius=8,
            color=border, fill=True, fill_color=fill, fill_opacity=0.95,
            tooltip=f"{label} #{i+1}", popup=popup
        ).add_to(target)

    high_bld.add_to(m)
    mod_bld.add_to(m)
    low_bld.add_to(m)

    flow_layer = folium.FeatureGroup(name="💧 Water Flow", show=True)
    bounds = flood_gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    sx, sy = (maxx-minx)/4, (maxy-miny)/3
    for i in range(4):
        for j in range(3):
            lat1, lon1 = miny+(j+0.8)*sy, minx+(i+0.5)*sx
            lat2, lon2 = lat1-sy*0.45, lon1+sx*0.1
            folium.PolyLine([[lat1,lon1],[lat2,lon2]], color="#00eeff", weight=3, opacity=0.9).add_to(flow_layer)
            folium.Marker([lat2,lon2],
                icon=folium.DivIcon(
                    html='<div style="font-size:16px;color:#00eeff;text-shadow:0 0 4px #000">▼</div>',
                    icon_size=(18,18), icon_anchor=(9,9))
            ).add_to(flow_layer)
    flow_layer.add_to(m)

    # ── LEGEND — bottom-left corner ──────────────────────────────
    legend_html = """
    <div style='
        position:fixed;
        bottom:28px; left:10px;
        background:rgba(2,8,20,0.93);
        border-radius:10px;
        padding:11px 14px;
        z-index:9999;
        color:white;
        font-family:Arial,sans-serif;
        font-size:11px;
        border:1px solid rgba(0,140,255,0.28);
        min-width:170px;
        max-width:185px;
        box-shadow:0 4px 20px rgba(0,60,200,0.30);
    '>
        <b style='font-size:11.5px;letter-spacing:0.8px;color:#7dd3fc'>🗺️ LEGEND</b>
        <hr style='margin:6px 0;border-color:rgba(0,100,200,0.25);border-top:1px solid'>
        <div style='color:#888;font-size:9.5px;letter-spacing:1px;margin-bottom:4px'>ZONES</div>
        <div style='margin:2px 0'><span style='color:#0055ff'>█</span> Flood Zone</div>
        <div style='margin:2px 0'><span style='color:#ff0000'>█</span> High Risk Core</div>
        <div style='margin:2px 0'><span style='color:#ffcc00'>█</span> Moderate Risk</div>
        <div style='margin:2px 0'><span style='color:#ff8800'>█</span> Low Risk</div>
        <hr style='margin:6px 0;border-color:rgba(0,100,200,0.25);border-top:1px solid'>
        <div style='color:#888;font-size:9.5px;letter-spacing:1px;margin-bottom:4px'>BUILDINGS</div>
        <div style='margin:2px 0'><span style='color:#ff2222'>●</span> High Risk</div>
        <div style='margin:2px 0'><span style='color:#ffbb00'>●</span> Moderate Risk</div>
        <div style='margin:2px 0'><span style='color:#ff7700'>●</span> Low Risk</div>
        <div style='margin:2px 0'><span style='color:#00dd77'>■</span> Safe</div>
        <hr style='margin:6px 0;border-color:rgba(0,100,200,0.25);border-top:1px solid'>
        <div style='margin:2px 0'><span style='color:#00eeff'>▼</span> Water Flow</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(toggle_display=True, position="bottomright",
                    width=120, height=120, zoom_level_offset=-5).add_to(m)
    plugins.MousePosition(position="topright", prefix="📍 ").add_to(m)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    return m


def analyse_rainfall(mm, hours):
    intensity = mm/hours if hours > 0 else 0
    if mm == 0:
        return None
    if mm < 25:
        return {"risk":"Low","emoji":"🟢","color":"#2ecc71",
                "advice":"Light rainfall. Minimal flood risk.",
                "expected":"< 5%","intensity":round(intensity,2)}
    elif mm < 65:
        return {"risk":"Moderate","emoji":"🟡","color":"#f39c12",
                "advice":"Some low-lying areas may experience waterlogging.",
                "expected":"5% to 20%","intensity":round(intensity,2)}
    elif mm < 115:
        return {"risk":"High","emoji":"🔴","color":"#e74c3c",
                "advice":"Heavy rainfall! Significant flood risk.",
                "expected":"20% to 50%","intensity":round(intensity,2)}
    else:
        return {"risk":"Extreme","emoji":"🚨","color":"#c0392b",
                "advice":"Extreme rainfall! Immediate evacuation advised.",
                "expected":"> 50%","intensity":round(intensity,2)}


# ── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:700;
    color:white;letter-spacing:2px;text-transform:uppercase;
    padding:8px 0 14px;border-bottom:1px solid rgba(0,150,255,0.25);
    margin-bottom:16px'>
    🛰️ Analysis Controls
    </div>""", unsafe_allow_html=True)

    with st.expander("📁 Satellite Image", expanded=True):
        uploaded_file = st.file_uploader("Upload Sentinel GeoTIFF", type=["tif","tiff"])

    with st.expander("📍 Location", expanded=True):
        place_name = st.text_input("City / Region", placeholder="e.g. Haridwar, India")

    with st.expander("⚙️ Detection Settings", expanded=False):
        ndwi_threshold = st.slider("NDWI Threshold", 0.0, 1.0, 0.2, 0.05)

    with st.expander("🌧️ Rainfall Analysis", expanded=True):
        rainfall_mm    = st.number_input("Rainfall amount (mm)", min_value=0.0, max_value=1000.0, value=0.0, step=10.0)
        rainfall_hours = st.slider("Duration (hours)", 1, 72, 24)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Run Full Analysis", type="primary", use_container_width=True)

    st.markdown("""
    <div style='color:rgba(255,255,255,0.30);font-size:0.70rem;text-align:center;
    margin-top:24px;letter-spacing:0.5px'>
    GeoFlood v1.0<br>Dinesh · Likhitha · Gayatri
    </div>""", unsafe_allow_html=True)


# ── RAINFALL SECTION ─────────────────────────────────────────────
if rainfall_mm > 0:
    r = analyse_rainfall(rainfall_mm, rainfall_hours)
    if r:
        st.markdown("""
        <div class='section-box'>
            <div class='section-title'>🌧️ Rainfall Risk Assessment</div>
        </div>""", unsafe_allow_html=True)

        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Rainfall</div>"
            f"<div class='value'>{rainfall_mm}<span style='font-size:1rem'>mm</span></div>"
            f"<div class='sub'>Total amount</div></div>", unsafe_allow_html=True)
        rc2.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Duration</div>"
            f"<div class='value'>{rainfall_hours}<span style='font-size:1rem'>h</span></div>"
            f"<div class='sub'>Hours</div></div>", unsafe_allow_html=True)
        rc3.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Intensity</div>"
            f"<div class='value'>{r['intensity']}<span style='font-size:1rem'>mm/h</span></div>"
            f"<div class='sub'>Rate</div></div>", unsafe_allow_html=True)
        risk_color = r['color']
        risk_emoji = r['emoji']
        risk_label = r['risk']
        rc4.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Risk Level</div>"
            f"<div class='value'>{risk_emoji}</div>"
            f"<div class='sub' style='color:{risk_color};font-weight:700'>{risk_label}</div>"
            f"</div>", unsafe_allow_html=True)

        rain_color  = r['color']
        rain_emoji  = r['emoji']
        rain_risk   = r['risk']
        rain_exp    = r['expected']
        rain_advice = r['advice']
        st.markdown(
            f"<div class='rain-result'>"
            f"<b>Risk Level:</b> <span style='color:{rain_color};font-weight:700'>{rain_emoji} {rain_risk}</span>"
            f" &nbsp;·&nbsp; "
            f"<b>Expected Buildings Affected:</b> {rain_exp}<br><br>"
            f"📋 <b>Advisory:</b> {rain_advice}</div>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


# ── SESSION STATE ─────────────────────────────────────────────────
if "done" not in st.session_state:
    st.session_state.done = False

if run_btn:
    if not uploaded_file or not place_name:
        st.warning("⚠️ Please upload a GeoTIFF and enter a location name to continue.")
        st.stop()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    try:
        with st.spinner("🛰️ Processing satellite image..."):
            flood_gdf     = dummy_flood_polygons()
        with st.spinner("🗺️ Fetching buildings from OpenStreetMap..."):
            buildings_gdf = dummy_buildings()
            flooded_gdf   = dummy_flooded_buildings()
        total   = len(buildings_gdf)
        flooded = len(flooded_gdf)
        pct     = round((flooded/total)*100, 1) if total else 0
        safe    = total - flooded
        m        = create_map(flood_gdf, buildings_gdf, flooded_gdf)
        map_html = m._repr_html_()
        st.session_state.update(
            done=True, total=total, flooded=flooded,
            pct=pct, safe=safe, map_html=map_html, place=place_name)
    finally:
        os.unlink(tmp_path)


# ── RESULTS ──────────────────────────────────────────────────────
if st.session_state.done:
    total   = st.session_state.total
    flooded = st.session_state.flooded
    pct     = st.session_state.pct
    safe    = st.session_state.safe

    # ── Metrics
    st.markdown("""
    <div class='section-box'>
        <div class='section-title'>📊 Impact Metrics</div>
    </div>""", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.markdown(
        f"<div class='metric-card total-card'>"
        f"<div class='label'>Total Buildings</div>"
        f"<div class='value'>{total}</div>"
        f"<div class='sub'>In selected area</div></div>", unsafe_allow_html=True)
    m2.markdown(
        f"<div class='metric-card flood-card'>"
        f"<div class='label'>Flooded Buildings</div>"
        f"<div class='value'>{flooded}</div>"
        f"<div class='sub' style='color:#e74c3c'>{pct}% affected</div></div>", unsafe_allow_html=True)
    m3.markdown(
        f"<div class='metric-card safe-card'>"
        f"<div class='label'>Safe Buildings</div>"
        f"<div class='value'>{safe}</div>"
        f"<div class='sub' style='color:#2ecc71'>{100-pct}% safe</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Risk classification
    st.markdown("""
    <div class='section-box'>
        <div class='section-title'>⚠️ Risk Classification</div>
        <div style='color:#ccc;font-size:0.88rem;line-height:2.2'>
            <span class='risk-badge badge-high'>🔴 High Risk</span>
            Buildings &gt;70% inside flood zone — Immediate evacuation required<br>
            <span class='risk-badge badge-moderate'>🟡 Moderate Risk</span>
            Buildings 30–70% inside flood zone — Monitor closely<br>
            <span class='risk-badge badge-low'>🟠 Low Risk</span>
            Buildings &lt;30% inside flood zone — Stay alert<br>
            <span class='risk-badge badge-safe'>🟢 Safe</span>
            Buildings outside flood zone — No immediate action needed
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Map full width
    st.markdown("""
    <div class='map-header'>
        🗺️ Interactive Flood Map
        <span class='map-subtitle'>Legend bottom-left · Switch layers top-right · Click buildings for risk details</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='map-container'>", unsafe_allow_html=True)
    st.components.v1.html(st.session_state.map_html, height=600)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chart full width below map (same width, stacked)
    st.markdown("""
    <div class='section-title' style='color:white;font-size:1rem;
    font-weight:700;letter-spacing:1px;text-transform:uppercase'>
    📈 Impact Summary
    </div>""", unsafe_allow_html=True)

    fig = impact_chart(total, flooded)
    st.pyplot(fig, use_container_width=True)

    # ── Info banner
    st.markdown(
        f"<div class='info-banner'>"
        f"✅ <b>Analysis Complete</b> — "
        f"Location: <b>{st.session_state.place}</b> &nbsp;|&nbsp; "
        f"{total} buildings scanned &nbsp;|&nbsp; "
        f"<span style='color:#e74c3c'>{flooded} flooded ({pct}%)</span> &nbsp;|&nbsp; "
        f"<span style='color:#2ecc71'>{safe} safe ({100-pct}%)</span><br>"
        f"<small style='opacity:0.55'>Currently using dummy data. "
        f"Connect real Sentinel-2 image for production results.</small>"
        f"</div>", unsafe_allow_html=True)
