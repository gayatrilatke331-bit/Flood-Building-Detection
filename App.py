import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.hero {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 16px; padding: 36px 32px;
    margin-bottom: 20px; text-align: center; color: white;
}
.hero h1 { font-size: 2.4rem; font-weight: 700; margin: 0; }
.hero p  { font-size: 1rem; opacity: 0.85; margin-top: 6px; }
.section-box {
    background: #111827; border-radius: 12px;
    padding: 20px; margin-bottom: 16px; border: 1px solid #1f2937;
}
.section-title {
    font-size: 1.1rem; font-weight: 700; color: white;
    margin-bottom: 14px; padding-bottom: 8px;
    border-bottom: 2px solid #1a6bff;
}
.metric-card {
    background: #1a1a2e; border-radius: 10px; padding: 16px;
    text-align: center; color: white;
    border: 1px solid #0f3460; height: 100%;
}
.metric-card .label { font-size: 0.8rem; opacity: 0.65; margin-bottom: 6px; }
.metric-card .value { font-size: 1.9rem; font-weight: 700; }
.metric-card .sub   { font-size: 0.78rem; margin-top: 4px; }
.flood-card  { border-top: 3px solid #e74c3c !important; }
.total-card  { border-top: 3px solid #3498db !important; }
.safe-card   { border-top: 3px solid #2ecc71 !important; }
.rain-card   { border-top: 3px solid #9b59b6 !important; }
.risk-badge {
    display: inline-block; padding: 4px 12px;
    border-radius: 20px; font-size: 0.82rem;
    font-weight: 700; margin: 4px 2px;
}
.badge-high     { background:#ff000033; color:#ff4444; border:1px solid #ff4444; }
.badge-moderate { background:#ffaa0033; color:#ffaa00; border:1px solid #ffaa00; }
.badge-low      { background:#ff660033; color:#ff6600; border:1px solid #ff6600; }
.badge-safe     { background:#00cc6633; color:#00cc66; border:1px solid #00cc66; }
.rain-result {
    background: #111827; border-radius: 10px; padding: 16px;
    color: white; border-left: 4px solid #9b59b6; margin-top: 10px;
}
.info-banner {
    background: linear-gradient(90deg, #0f2027, #203a43);
    border-radius: 10px; padding: 14px 18px; color: white;
    border-left: 4px solid #2ecc71; margin-top: 16px;
}
.step-box {
    background: #1a1a2e; border-radius: 8px;
    padding: 12px 16px; margin: 6px 0; color: white;
    border-left: 3px solid #1a6bff; font-size: 0.88rem;
}
.location-card {
    background: #1a1a2e; border-radius: 10px; padding: 14px;
    color: white; border: 1px solid #0f3460; margin-bottom: 8px;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🌊 GeoFlood</h1>
    <p>Flood Detection and Building Impact Assessment</p>
    <p style="font-size:0.8rem;opacity:0.55;margin-top:2px">
        Select any location — instant flood analysis — no image upload needed
    </p>
</div>
""", unsafe_allow_html=True)

# ── Location Dataset ──────────────────────────────────────────────
# Each location has pre-defined flood zones and building data
LOCATIONS = {
    "Haridwar, Uttarakhand": {
        "center": [29.9457, 78.1642],
        "zoom": 14,
        "flood_polys": [
            [(78.155,29.940),(78.175,29.940),(78.175,29.955),(78.155,29.955)],
            [(78.170,29.935),(78.185,29.935),(78.185,29.948),(78.170,29.948)],
        ],
        "flood_count": 5,
        "total_count": 20,
        "description": "Ganges river flooding near Har Ki Pauri",
        "risk_level": "High",
        "state": "Uttarakhand"
    },
    "Rishikesh, Uttarakhand": {
        "center": [30.0869, 78.2676],
        "zoom": 14,
        "flood_polys": [
            [(78.260,30.080),(78.275,30.080),(78.275,30.092),(78.260,30.092)],
        ],
        "flood_count": 3,
        "total_count": 15,
        "description": "Ganges river overflow near Laxman Jhula",
        "risk_level": "Moderate",
        "state": "Uttarakhand"
    },
    "Dehradun, Uttarakhand": {
        "center": [30.3165, 78.0322],
        "zoom": 13,
        "flood_polys": [
            [(78.020,30.308),(78.040,30.308),(78.040,30.322),(78.020,30.322)],
            [(78.038,30.315),(78.050,30.315),(78.050,30.325),(78.038,30.325)],
        ],
        "flood_count": 7,
        "total_count": 25,
        "description": "Seasonal flooding in Rispana River basin",
        "risk_level": "High",
        "state": "Uttarakhand"
    },
    "Varanasi, Uttar Pradesh": {
        "center": [25.3176, 82.9739],
        "zoom": 14,
        "flood_polys": [
            [(82.965,25.310),(82.980,25.310),(82.980,25.325),(82.965,25.325)],
        ],
        "flood_count": 8,
        "total_count": 30,
        "description": "Ganges river flooding near ghats",
        "risk_level": "Extreme",
        "state": "Uttar Pradesh"
    },
    "Patna, Bihar": {
        "center": [25.5941, 85.1376],
        "zoom": 13,
        "flood_polys": [
            [(85.125,25.585),(85.148,25.585),(85.148,25.600),(85.125,25.600)],
            [(85.140,25.578),(85.155,25.578),(85.155,25.590),(85.140,25.590)],
        ],
        "flood_count": 12,
        "total_count": 40,
        "description": "Ganga river flooding in low-lying areas",
        "risk_level": "Extreme",
        "state": "Bihar"
    },
    "Guwahati, Assam": {
        "center": [26.1445, 91.7362],
        "zoom": 13,
        "flood_polys": [
            [(91.720,26.135),(91.745,26.135),(91.745,26.152),(91.720,26.152)],
        ],
        "flood_count": 9,
        "total_count": 28,
        "description": "Brahmaputra river flooding",
        "risk_level": "High",
        "state": "Assam"
    },
    "Srinagar, Jammu & Kashmir": {
        "center": [34.0837, 74.7973],
        "zoom": 13,
        "flood_polys": [
            [(74.785,34.075),(74.805,34.075),(74.805,34.090),(74.785,34.090)],
        ],
        "flood_count": 6,
        "total_count": 22,
        "description": "Jhelum river flooding in valley",
        "risk_level": "High",
        "state": "J&K"
    },
    "Mumbai, Maharashtra": {
        "center": [19.0760, 72.8777],
        "zoom": 13,
        "flood_polys": [
            [(72.868,19.068),(72.882,19.068),(72.882,19.082),(72.868,19.082)],
        ],
        "flood_count": 4,
        "total_count": 18,
        "description": "Coastal and urban flooding during monsoon",
        "risk_level": "Moderate",
        "state": "Maharashtra"
    },
}

# ── Data generation per location ──────────────────────────────────
def get_flood_data(location_key):
    loc = LOCATIONS[location_key]
    center_lat, center_lon = loc["center"]

    # Generate flood polygons
    polys = []
    for coords in loc["flood_polys"]:
        polys.append(Polygon(coords))
    flood_gdf = gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326")

    # Generate buildings based on total count
    total   = loc["total_count"]
    flooded = loc["flood_count"]
    safe_n  = total - flooded

    flood_blds = []
    for i in range(flooded):
        base_lon = loc["flood_polys"][0][0][0]
        base_lat = loc["flood_polys"][0][0][1]
        flood_blds.append(
            box(base_lon+i*0.002, base_lat+0.001,
                base_lon+i*0.002+0.0015, base_lat+0.003))

    safe_blds = []
    for i in range(safe_n):
        safe_blds.append(
            box(center_lon-0.02+i*0.003,
                center_lat+0.015,
                center_lon-0.02+i*0.003+0.002,
                center_lat+0.018))

    buildings_gdf = gpd.GeoDataFrame(
        geometry=flood_blds+safe_blds, crs="EPSG:4326")
    flooded_gdf = gpd.GeoDataFrame(
        geometry=flood_blds, crs="EPSG:4326")

    return flood_gdf, buildings_gdf, flooded_gdf


# ── Chart ─────────────────────────────────────────────────────────
def impact_chart(total_buildings, flooded_buildings):
    safe = total_buildings - flooded_buildings
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")
    sizes  = [flooded_buildings, safe]
    colors = ["#E24B4A", "#9FE1CB"]
    ax1.pie(sizes, colors=colors, startangle=90,
            wedgeprops={"width":0.5,"edgecolor":"white","linewidth":2})
    ax1.set_title("Building Impact", fontsize=13, fontweight="bold", pad=15)
    patches = [
        mpatches.Patch(color="#E24B4A", label=f"Flooded ({flooded_buildings})"),
        mpatches.Patch(color="#9FE1CB", label=f"Safe ({safe})")
    ]
    ax1.legend(handles=patches, loc="lower center",
               bbox_to_anchor=(0.5,-0.15), ncol=2, fontsize=10)
    categories = ["Total","Flooded","Safe"]
    values     = [total_buildings, flooded_buildings, safe]
    bar_colors = ["#3B8BD4","#E24B4A","#1D9E75"]
    bars = ax2.bar(categories, values, color=bar_colors,
                   edgecolor="white", linewidth=1.5, width=0.5)
    for bar, val in zip(bars, values):
        ax2.text(bar.get_x()+bar.get_width()/2,
                 bar.get_height()+0.3, str(val),
                 ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax2.set_title("Building Count", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Number of buildings")
    ax2.spines[["top","right"]].set_visible(False)
    ax2.set_ylim(0, total_buildings*1.2)
    plt.tight_layout()
    return fig


# ── Risk level ────────────────────────────────────────────────────
def get_risk_level(building_geom, flood_gdf):
    try:
        total_area = building_geom.area
        if total_area == 0:
            return "low"
        intersection_area = 0
        for _, flood_row in flood_gdf.iterrows():
            if building_geom.intersects(flood_row.geometry):
                intersection_area += building_geom.intersection(
                    flood_row.geometry).area
        pct = (intersection_area / total_area) * 100
        if pct >= 70:   return "high"
        elif pct >= 30: return "moderate"
        elif pct > 0:   return "low"
        else:           return "none"
    except:
        return "low"


# ── Map ───────────────────────────────────────────────────────────
def create_map(flood_gdf, buildings_gdf, flooded_gdf, location_key):
    loc        = LOCATIONS[location_key]
    center_lat = loc["center"][0]
    center_lon = loc["center"][1]
    zoom       = loc["zoom"]

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )
    folium.TileLayer("OpenStreetMap", name="🗺️ Street Map").add_to(m)
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
            style_function=lambda x: {
                "fillColor":"#0055ff","color":"#0033aa",
                "weight":2.5,"fillOpacity":0.4},
            tooltip=f"🌊 Flood Zone {idx+1} — {loc['description']}"
        ).add_to(flood_layer)
    flood_layer.add_to(m)

    # High risk core
    high_zone = folium.FeatureGroup(name="🔴 High Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            core = row.geometry.buffer(-0.0002)
            if not core.is_empty:
                folium.GeoJson(
                    core.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor":"#ff0000","color":"#cc0000",
                        "weight":1.5,"fillOpacity":0.35},
                    tooltip="🔴 HIGH RISK — Core flood area"
                ).add_to(high_zone)
        except:
            pass
    high_zone.add_to(m)

    # Moderate risk
    mod_zone = folium.FeatureGroup(name="🟡 Moderate Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            outer = row.geometry.buffer(0.0006)
            ring  = outer.difference(row.geometry)
            if not ring.is_empty:
                folium.GeoJson(
                    ring.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor":"#ffcc00","color":"#cc9900",
                        "weight":1.5,"fillOpacity":0.25},
                    tooltip="🟡 MODERATE RISK — Buffer zone"
                ).add_to(mod_zone)
        except:
            pass
    mod_zone.add_to(m)

    # Low risk
    low_zone = folium.FeatureGroup(name="🟠 Low Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            outer1 = row.geometry.buffer(0.0006)
            outer2 = row.geometry.buffer(0.0012)
            ring   = outer2.difference(outer1)
            if not ring.is_empty:
                folium.GeoJson(
                    ring.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor":"#ff8800","color":"#cc6600",
                        "weight":1,"fillOpacity":0.15},
                    tooltip="🟠 LOW RISK — Watch zone"
                ).add_to(low_zone)
        except:
            pass
    low_zone.add_to(m)

    # Safe buildings
    flooded_idx = set(flooded_gdf.index.tolist())
    safe_layer  = folium.FeatureGroup(name="🟢 Safe Buildings", show=True)
    for idx, row in buildings_gdf.iterrows():
        if idx not in flooded_idx:
            c = row.geometry.centroid
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda x: {
                    "fillColor":"#00dd77","color":"#009944",
                    "weight":1.5,"fillOpacity":0.7},
                tooltip="🟢 Safe Building",
                popup=folium.Popup(
                    f"<div style='font-family:Arial;width:180px'>"
                    f"<b style='color:green'>🟢 Safe Building</b><hr>"
                    f"Status: Outside flood zone<br>"
                    f"Lat: {c.y:.5f}<br>Lon: {c.x:.5f}</div>",
                    max_width=200)
            ).add_to(safe_layer)
    safe_layer.add_to(m)

    # Flooded buildings
    high_bld = folium.FeatureGroup(name="🔴 High Risk Buildings", show=True)
    mod_bld  = folium.FeatureGroup(name="🟡 Moderate Risk Buildings", show=True)
    low_bld  = folium.FeatureGroup(name="🟠 Low Risk Buildings", show=True)

    for i, (idx, row) in enumerate(flooded_gdf.iterrows()):
        c    = row.geometry.centroid
        risk = get_risk_level(row.geometry, flood_gdf)
        cfg  = {
            "high":     ("#ff2222","#aa0000","🔴 HIGH RISK","red",
                         high_bld,"🚨 Immediate evacuation required!"),
            "moderate": ("#ffbb00","#cc8800","🟡 MODERATE RISK","orange",
                         mod_bld,"⚠️ Monitor closely"),
            "low":      ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",
                         low_bld,"ℹ️ Stay alert"),
        }.get(risk, ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",
                     low_bld,"ℹ️ Stay alert"))
        fill, border, label, color, target, action = cfg
        popup = folium.Popup(
            f"<div style='font-family:Arial;width:210px;padding:6px'>"
            f"<h4 style='color:{color};margin:0 0 6px'>{label}</h4>"
            f"<hr style='margin:4px 0'>"
            f"<b>Building:</b> #{i+1}<br>"
            f"<b>Location:</b> {location_key}<br>"
            f"<b>Risk:</b> <span style='color:{color};font-weight:700'>"
            f"{risk.upper()}</span><br>"
            f"<b>Lat:</b> {c.y:.5f}<br>"
            f"<b>Lon:</b> {c.x:.5f}<br>"
            f"<hr style='margin:4px 0'>"
            f"<b>Action:</b> {action}</div>",
            max_width=230)
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, f=fill, b=border: {
                "fillColor":f,"color":b,"weight":2.5,"fillOpacity":0.85},
            tooltip=f"{label} — Building #{i+1}",
            popup=popup
        ).add_to(target)
        folium.CircleMarker(
            location=[c.y, c.x], radius=8,
            color=border, fill=True,
            fill_color=fill, fill_opacity=0.95,
            tooltip=f"{label} #{i+1}", popup=popup
        ).add_to(target)

    high_bld.add_to(m)
    mod_bld.add_to(m)
    low_bld.add_to(m)

    # Water flow
    flow_layer = folium.FeatureGroup(name="💧 Water Flow", show=True)
    bounds = flood_gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    sx = (maxx-minx)/4
    sy = (maxy-miny)/3
    for i in range(4):
        for j in range(3):
            lat1 = miny+(j+0.8)*sy
            lon1 = minx+(i+0.5)*sx
            lat2 = lat1-sy*0.45
            lon2 = lon1+sx*0.1
            folium.PolyLine(
                [[lat1,lon1],[lat2,lon2]],
                color="#00eeff", weight=3, opacity=0.9
            ).add_to(flow_layer)
            folium.Marker(
                [lat2,lon2],
                icon=folium.DivIcon(
                    html='<div style="font-size:16px;color:#00eeff;'
                         'text-shadow:0 0 4px #000">▼</div>',
                    icon_size=(18,18), icon_anchor=(9,9))
            ).add_to(flow_layer)
    flow_layer.add_to(m)

    legend = (
        "<div style='position:fixed;bottom:30px;right:8px;"
        "background:rgba(5,10,20,0.93);border-radius:12px;"
        "padding:14px 18px;z-index:9999;color:white;"
        "font-family:Arial;font-size:12px;"
        "border:1px solid #2a2a3a;min-width:195px;'>"
        "<b style='font-size:13px'>🗺️ Map Legend</b>"
        "<hr style='margin:7px 0;border-color:#2a2a3a'>"
        "<b style='font-size:11px;color:#aaa'>ZONES</b><br>"
        "<span style='color:#0055ff'>██</span> Flood Zone<br>"
        "<span style='color:#ff0000'>██</span> High Risk Core<br>"
        "<span style='color:#ffcc00'>██</span> Moderate Risk<br>"
        "<span style='color:#ff8800'>██</span> Low Risk Zone<br>"
        "<hr style='margin:7px 0;border-color:#2a2a3a'>"
        "<b style='font-size:11px;color:#aaa'>BUILDINGS</b><br>"
        "<span style='color:#ff2222'>●</span> High Risk<br>"
        "<span style='color:#ffbb00'>●</span> Moderate Risk<br>"
        "<span style='color:#ff7700'>●</span> Low Risk<br>"
        "<span style='color:#00dd77'>■</span> Safe<br>"
        "<hr style='margin:7px 0;border-color:#2a2a3a'>"
        "<span style='color:#00eeff'>▼</span> Water Flow<br>"
        "<hr style='margin:7px 0;border-color:#2a2a3a'>"
        "<small style='color:#888'>Click buildings for details</small>"
        "</div>"
    )
    m.get_root().html.add_child(folium.Element(legend))
    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(toggle_display=True, position="bottomleft",
                    width=130, height=130, zoom_level_offset=-5).add_to(m)
    plugins.MousePosition(position="bottomright", prefix="📍 ").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m


# ── Rainfall ──────────────────────────────────────────────────────
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


# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛰️ Analysis Controls")
    st.markdown("---")

    st.markdown("### 📍 Select Location")
    selected_location = st.selectbox(
        "Choose a flood-prone area",
        options=list(LOCATIONS.keys()),
        index=0
    )

    loc_info = LOCATIONS[selected_location]
    st.markdown(
        f"<div class='location-card'>"
        f"<b>📌 {selected_location}</b><br>"
        f"<small style='opacity:0.7'>{loc_info['description']}</small><br><br>"
        f"<b>Risk Level:</b> "
        f"<span style='color:#e74c3c'>{loc_info['risk_level']}</span><br>"
        f"<b>State:</b> {loc_info['state']}<br>"
        f"<b>Buildings:</b> {loc_info['total_count']} total | "
        f"{loc_info['flood_count']} at risk"
        f"</div>",
        unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("⚙️ Detection Settings", expanded=False):
        ndwi_threshold = st.slider("NDWI Threshold", 0.0, 1.0, 0.2, 0.05)

    with st.expander("🌧️ Rainfall Analysis", expanded=True):
        rainfall_mm = st.number_input(
            "Rainfall amount (mm)",
            min_value=0.0, max_value=1000.0, value=0.0, step=10.0)
        rainfall_hours = st.slider("Duration (hours)", 1, 72, 24)

    st.markdown("---")
    run_btn = st.button(
        "🚀 Run Analysis",
        type="primary",
        use_container_width=True
    )
    st.markdown("---")
    st.markdown(
        "<div style='color:gray;font-size:0.72rem;text-align:center'>"
        "GeoFlood v1.0<br>Dinesh · Likhitha · Gayatri</div>",
        unsafe_allow_html=True)

# ── Rainfall section ──────────────────────────────────────────────
if rainfall_mm > 0:
    r = analyse_rainfall(rainfall_mm, rainfall_hours)
    if r:
        st.markdown(
            "<div class='section-box'>"
            "<div class='section-title'>🌧️ Rainfall Risk Assessment</div>"
            "</div>", unsafe_allow_html=True)
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Rainfall</div>"
            f"<div class='value'>{rainfall_mm}mm</div>"
            f"<div class='sub'>Total amount</div></div>",
            unsafe_allow_html=True)
        rc2.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Duration</div>"
            f"<div class='value'>{rainfall_hours}h</div>"
            f"<div class='sub'>Hours</div></div>",
            unsafe_allow_html=True)
        rc3.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Intensity</div>"
            f"<div class='value'>{r['intensity']}</div>"
            f"<div class='sub'>mm/hour</div></div>",
            unsafe_allow_html=True)
        rc4.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Risk Level</div>"
            f"<div class='value'>{r['emoji']}</div>"
            f"<div class='sub' style='color:{r[chr(99)+chr(111)+chr(108)+chr(111)+chr(114)]}'>{r['risk']}</div>"
            f"</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='rain-result'>"
            f"<b>Risk:</b> "
            f"<span style='color:{r['color']};font-weight:700'>"
            f"{r['emoji']} {r['risk']}</span>"
            f" &nbsp;|&nbsp; "
            f"<b>Expected buildings affected:</b> {r['expected']}<br><br>"
            f"📋 <b>Advisory:</b> {r['advice']}</div>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
if "done" not in st.session_state:
    st.session_state.done = False
if "last_location" not in st.session_state:
    st.session_state.last_location = None

# ── Run Analysis ──────────────────────────────────────────────────
if run_btn:
    with st.spinner("🛰️ Loading flood data for " + selected_location + "..."):
        flood_gdf, buildings_gdf, flooded_gdf = get_flood_data(
            selected_location)

    with st.spinner("🗺️ Building interactive map..."):
        m        = create_map(flood_gdf, buildings_gdf,
                              flooded_gdf, selected_location)
        map_html = m._repr_html_()

    total   = len(buildings_gdf)
    flooded = len(flooded_gdf)
    pct     = round((flooded/total)*100,1) if total else 0
    safe    = total - flooded

    st.session_state.done          = True
    st.session_state.total         = total
    st.session_state.flooded       = flooded
    st.session_state.pct           = pct
    st.session_state.safe          = safe
    st.session_state.map_html      = map_html
    st.session_state.place         = selected_location
    st.session_state.last_location = selected_location

# ── Results ───────────────────────────────────────────────────────
if st.session_state.done:
    total   = st.session_state.total
    flooded = st.session_state.flooded
    pct     = st.session_state.pct
    safe    = st.session_state.safe

    st.markdown(
        "<div class='section-box'>"
        "<div class='section-title'>📊 Impact Metrics</div>"
        "</div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.markdown(
        f"<div class='metric-card total-card'>"
        f"<div class='label'>Total Buildings</div>"
        f"<div class='value'>{total}</div>"
        f"<div class='sub'>In selected area</div></div>",
        unsafe_allow_html=True)
    m2.markdown(
        f"<div class='metric-card flood-card'>"
        f"<div class='label'>Flooded Buildings</div>"
        f"<div class='value'>{flooded}</div>"
        f"<div class='sub' style='color:#e74c3c'>{pct}% affected</div>"
        f"</div>", unsafe_allow_html=True)
    m3.markdown(
        f"<div class='metric-card safe-card'>"
        f"<div class='label'>Safe Buildings</div>"
        f"<div class='value'>{safe}</div>"
        f"<div class='sub' style='color:#2ecc71'>{100-pct}% safe</div>"
        f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<div class='section-box'>"
        "<div class='section-title'>⚠️ Risk Classification Summary</div>"
        "<div style='color:#ccc;font-size:0.88rem;line-height:2'>"
        "<span class='risk-badge badge-high'>🔴 High Risk</span>"
        " Buildings over 70% inside flood zone — Immediate evacuation<br>"
        "<span class='risk-badge badge-moderate'>🟡 Moderate Risk</span>"
        " Buildings 30 to 70% inside flood zone — Monitor closely<br>"
        "<span class='risk-badge badge-low'>🟠 Low Risk</span>"
        " Buildings under 30% inside flood zone — Stay alert<br>"
        "<span class='risk-badge badge-safe'>🟢 Safe</span>"
        " Buildings outside flood zone — No immediate action"
        "</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<div class='section-title' style='color:white;font-size:1.1rem;"
        "font-weight:700;padding-left:12px;border-left:3px solid #1a6bff'>"
        "🗺️ Interactive Flood Map"
        "<small style='font-size:0.75rem;opacity:0.6;font-weight:400'>"
        " &nbsp;&nbsp;Switch: Satellite / Street / Terrain"
        "</small></div>", unsafe_allow_html=True)

    map_col, info_col = st.columns([3,2])
    with map_col:
        st.components.v1.html(st.session_state.map_html, height=480)
    with info_col:
        st.markdown(
            "<div class='section-title' style='color:white;"
            "font-size:1rem;font-weight:700'>📈 Impact Summary</div>",
            unsafe_allow_html=True)
        fig = impact_chart(total, flooded)
        st.pyplot(fig)
        st.markdown(
            "<div class='section-box' style='margin-top:12px'>"
            "<div style='color:#ccc;font-size:0.83rem'>"
            "<b style='color:white'>📋 How to use the map:</b><br>"
            "<div class='step-box'>1️⃣ Top-right: switch Satellite / Street / Terrain</div>"
            "<div class='step-box'>2️⃣ Click red/orange buildings for risk details</div>"
            "<div class='step-box'>3️⃣ Toggle layers on/off with checkboxes</div>"
            "<div class='step-box'>4️⃣ Fullscreen button (top-left) for better view</div>"
            "<div class='step-box'>5️⃣ Mini-map (bottom-left) shows your position</div>"
            "</div></div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='info-banner'>"
        f"✅ <b>Analysis complete!</b> — "
        f"Location: <b>{st.session_state.place}</b> | "
        f"{total} buildings scanned | "
        f"{flooded} flooded ({pct}%) | "
        f"{safe} safe ({100-pct}%)"
        f"</div>", unsafe_allow_html=True)
