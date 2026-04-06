import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import math
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Polygon, box

st.set_page_config(page_title="GeoFlood — Uttarakhand", page_icon="🌊", layout="wide")

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
    border-radius: 20px; font-size: 0.82rem; font-weight: 700; margin: 4px 2px;
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
.loc-card {
    background: #1a1a2e; border-radius: 10px; padding: 14px;
    color: white; border: 1px solid #0f3460; margin-bottom: 8px;
    font-size: 0.85rem; border-left: 3px solid #1a6bff;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🌊 GeoFlood — Uttarakhand</h1>
    <p>Real-time Flood Detection and Building Impact Assessment</p>
    <p style="font-size:0.8rem;opacity:0.55;margin-top:2px">
        Live OpenStreetMap Data &bull; River Flood Zones &bull; Risk Classification
    </p>
</div>
""", unsafe_allow_html=True)

# ── Districts ─────────────────────────────────────────────────────
LOCATIONS = {
    "Haridwar": {
        "place": "Haridwar, Uttarakhand, India",
        "center": [29.9457, 78.1642], "zoom": 14,
        "river": "Ganga", "risk": "Extreme",
        "description": "Ganga river flooding near Har Ki Pauri ghats",
        "flood_bbox": [78.130, 29.920, 78.210, 29.975],
    },
    "Rishikesh": {
        "place": "Rishikesh, Uttarakhand, India",
        "center": [30.0869, 78.2676], "zoom": 14,
        "river": "Ganga", "risk": "High",
        "description": "Ganga river overflow near Laxman Jhula",
        "flood_bbox": [78.240, 30.060, 78.310, 30.120],
    },
    "Dehradun": {
        "place": "Dehradun, Uttarakhand, India",
        "center": [30.3165, 78.0322], "zoom": 13,
        "river": "Rispana & Bindal", "risk": "High",
        "description": "Seasonal flooding in Rispana and Bindal river basins",
        "flood_bbox": [77.990, 30.285, 78.080, 30.350],
    },
    "Nainital": {
        "place": "Nainital, Uttarakhand, India",
        "center": [29.3919, 79.4542], "zoom": 14,
        "river": "Naini Lake", "risk": "Moderate",
        "description": "Lake overflow and landslide-induced flooding",
        "flood_bbox": [79.430, 29.375, 79.480, 29.415],
    },
    "Rudraprayag": {
        "place": "Rudraprayag, Uttarakhand, India",
        "center": [30.2847, 78.9812], "zoom": 14,
        "river": "Alaknanda & Mandakini", "risk": "Extreme",
        "description": "Alaknanda and Mandakini river confluence flooding",
        "flood_bbox": [78.960, 30.265, 79.005, 30.305],
    },
    "Uttarkashi": {
        "place": "Uttarkashi, Uttarakhand, India",
        "center": [30.7268, 78.4354], "zoom": 14,
        "river": "Bhagirathi", "risk": "High",
        "description": "Bhagirathi river flooding in narrow valley",
        "flood_bbox": [78.415, 30.710, 78.460, 30.748],
    },
    "Chamoli": {
        "place": "Chamoli, Uttarakhand, India",
        "center": [30.3993, 79.3253], "zoom": 14,
        "river": "Alaknanda", "risk": "Extreme",
        "description": "Alaknanda river — glacial outburst flood risk",
        "flood_bbox": [79.300, 30.380, 79.355, 30.422],
    },
    "Pithoragarh": {
        "place": "Pithoragarh, Uttarakhand, India",
        "center": [29.5830, 80.2181], "zoom": 14,
        "river": "Kali & Saryu", "risk": "High",
        "description": "Kali and Saryu river flooding in border region",
        "flood_bbox": [80.195, 29.565, 80.240, 29.605],
    },
    "Tehri": {
        "place": "Tehri Garhwal, Uttarakhand, India",
        "center": [30.3784, 78.4800], "zoom": 13,
        "river": "Bhilangana", "risk": "Moderate",
        "description": "Bhilangana river and Tehri dam downstream risk",
        "flood_bbox": [78.455, 30.355, 78.510, 30.405],
    },
    "Roorkee": {
        "place": "Roorkee, Uttarakhand, India",
        "center": [29.8543, 77.8880], "zoom": 14,
        "river": "Ganga Canal", "risk": "Moderate",
        "description": "Upper Ganga canal overflow during heavy rainfall",
        "flood_bbox": [77.865, 29.835, 77.912, 29.875],
    },
}


# ── Fetch buildings ───────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_buildings(place_name, bbox):
    minx, miny, maxx, maxy = bbox
    for expand in [0, 0.01, 0.025, 0.05]:
        try:
            x1 = minx - expand
            y1 = miny - expand
            x2 = maxx + expand
            y2 = maxy + expand
            query = (
                "[out:json][timeout:60];"
                "(way[\"building\"]({y1},{x1},{y2},{x2});"
                "way[\"building:part\"]({y1},{x1},{y2},{x2});"
                "relation[\"building\"]({y1},{x1},{y2},{x2}););"
                "out geom;"
            ).format(y1=y1, x1=x1, y2=y2, x2=x2)
            resp = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query}, timeout=60
            )
            data = resp.json()
            polys = []
            for el in data.get("elements", []):
                if el.get("type") == "way":
                    coords = [(n["lon"], n["lat"]) for n in el.get("geometry", [])]
                    if len(coords) >= 3:
                        try:
                            p = Polygon(coords)
                            if p.is_valid and not p.is_empty:
                                polys.append(p)
                        except Exception:
                            pass
            if polys:
                return gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326"), True
        except Exception:
            pass
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326"), False


# ── Fetch flood zones ─────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_flood_zones(place_name, bbox):
    minx, miny, maxx, maxy = bbox
    try:
        query = (
            "[out:json][timeout:60];"
            "(way[\"waterway\"=\"river\"]({miny},{minx},{maxy},{maxx});"
            "way[\"waterway\"=\"stream\"]({miny},{minx},{maxy},{maxx});"
            "way[\"waterway\"=\"canal\"]({miny},{minx},{maxy},{maxx});"
            "way[\"natural\"=\"water\"]({miny},{minx},{maxy},{maxx});"
            "way[\"natural\"=\"wetland\"]({miny},{minx},{maxy},{maxx});"
            "relation[\"natural\"=\"water\"]({miny},{minx},{maxy},{maxx});"
            "relation[\"waterway\"=\"river\"]({miny},{minx},{maxy},{maxx}););"
            "out geom;"
        ).format(miny=miny, minx=minx, maxy=maxy, maxx=maxx)
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}, timeout=60
        )
        data = resp.json()
        polys = []
        for el in data.get("elements", []):
            if el.get("type") == "way":
                coords = [(n["lon"], n["lat"]) for n in el.get("geometry", [])]
                if len(coords) >= 2:
                    try:
                        geom = Polygon(coords) if len(coords) >= 3 else None
                        if geom is None:
                            from shapely.geometry import LineString
                            geom = LineString(coords)
                        if geom.is_valid and not geom.is_empty:
                            polys.append(geom.buffer(0.006))
                    except Exception:
                        pass
        if polys:
            return gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326")
    except Exception:
        pass
    return fallback_flood(bbox)


def fallback_flood(bbox):
    minx, miny, maxx, maxy = bbox
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    w  = (maxx - minx) * 0.35
    h  = (maxy - miny) * 0.55
    pts = []
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        ox = math.sin(t * math.pi * 2) * w * 0.25
        pts.append((cx - w/2 + t*w + ox, cy + h/2 - t*h*0.1))
    for i in range(steps, -1, -1):
        t = i / steps
        ox = math.sin(t * math.pi * 2) * w * 0.25
        pts.append((cx - w/2 + t*w + ox, cy - h/2 + t*h*0.1))
    try:
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
    except Exception:
        poly = box(cx - w/2, cy - h/2, cx + w/2, cy + h/2)
    return gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")


# ── Spatial join ──────────────────────────────────────────────────
def find_flooded(buildings_gdf, flood_gdf):
    try:
        if buildings_gdf.crs != flood_gdf.crs:
            flood_gdf = flood_gdf.to_crs(buildings_gdf.crs)
        result = gpd.sjoin(buildings_gdf, flood_gdf, how="inner", predicate="intersects")
        result = result[~result.index.duplicated(keep="first")]
        return result.reset_index(drop=True)
    except Exception:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


# ── Risk level ────────────────────────────────────────────────────
def get_risk(geom, flood_gdf):
    try:
        total = geom.area
        if total == 0:
            return "low"
        inter = sum(
            geom.intersection(row.geometry).area
            for _, row in flood_gdf.iterrows()
            if geom.intersects(row.geometry)
        )
        pct = (inter / total) * 100
        if pct >= 70:   return "high"
        elif pct >= 30: return "moderate"
        elif pct > 0:   return "low"
        else:           return "none"
    except Exception:
        return "low"


# ── Chart ─────────────────────────────────────────────────────────
def make_chart(total, flooded):
    safe = total - flooded
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")
    ax1.pie(
        [flooded, safe], colors=["#E24B4A", "#9FE1CB"],
        startangle=90, wedgeprops={"width": 0.5, "edgecolor": "white", "linewidth": 2}
    )
    ax1.set_title("Building Impact", fontsize=13, fontweight="bold", pad=15)
    ax1.legend(
        handles=[
            mpatches.Patch(color="#E24B4A", label="Flooded ({})".format(flooded)),
            mpatches.Patch(color="#9FE1CB", label="Safe ({})".format(safe))
        ],
        loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=10
    )
    bars = ax2.bar(
        ["Total", "Flooded", "Safe"], [total, flooded, safe],
        color=["#3B8BD4", "#E24B4A", "#1D9E75"],
        edgecolor="white", linewidth=1.5, width=0.5
    )
    for bar, val in zip(bars, [total, flooded, safe]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3, str(val),
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )
    ax2.set_title("Building Count", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Number of buildings")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.set_ylim(0, max(total * 1.2, 10))
    plt.tight_layout()
    return fig


# ── Build map ─────────────────────────────────────────────────────
def build_map(flood_gdf, buildings_gdf, flooded_gdf, loc_key):
    loc = LOCATIONS[loc_key]
    m = folium.Map(location=loc["center"], zoom_start=loc["zoom"], tiles="OpenStreetMap")

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite"
    ).add_to(m)

    # Flood zone
    flood_fg = folium.FeatureGroup(name="Flood Zone", show=True)
    for _, row in flood_gdf.iterrows():
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x: {"fillColor": "#0055ff", "color": "#0033aa", "weight": 2.5, "fillOpacity": 0.4},
            tooltip="Flood Zone — {} River".format(loc["river"])
        ).add_to(flood_fg)
    flood_fg.add_to(m)

    # High risk zone
    high_fg = folium.FeatureGroup(name="High Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            core = row.geometry.buffer(-0.0002)
            if not core.is_empty:
                folium.GeoJson(
                    core.__geo_interface__,
                    style_function=lambda x: {"fillColor": "#ff0000", "color": "#cc0000", "weight": 1.5, "fillOpacity": 0.4},
                    tooltip="HIGH RISK — Core flood area"
                ).add_to(high_fg)
        except Exception:
            pass
    high_fg.add_to(m)

    # Moderate risk zone
    mod_fg = folium.FeatureGroup(name="Moderate Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            ring = row.geometry.buffer(0.0008).difference(row.geometry)
            if not ring.is_empty:
                folium.GeoJson(
                    ring.__geo_interface__,
                    style_function=lambda x: {"fillColor": "#ffcc00", "color": "#cc9900", "weight": 1.5, "fillOpacity": 0.25},
                    tooltip="MODERATE RISK — Buffer zone"
                ).add_to(mod_fg)
        except Exception:
            pass
    mod_fg.add_to(m)

    # Low risk zone
    low_fg = folium.FeatureGroup(name="Low Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            ring = row.geometry.buffer(0.0016).difference(row.geometry.buffer(0.0008))
            if not ring.is_empty:
                folium.GeoJson(
                    ring.__geo_interface__,
                    style_function=lambda x: {"fillColor": "#ff8800", "color": "#cc6600", "weight": 1, "fillOpacity": 0.15},
                    tooltip="LOW RISK — Watch zone"
                ).add_to(low_fg)
        except Exception:
            pass
    low_fg.add_to(m)

    # Safe buildings
    flooded_idx = set(flooded_gdf.index.tolist())
    safe_fg = folium.FeatureGroup(name="Safe Buildings", show=True)
    count = 0
    for idx, row in buildings_gdf.iterrows():
        if idx not in flooded_idx:
            count += 1
            if count <= 100:
                c = row.geometry.centroid
                folium.GeoJson(
                    row.geometry.__geo_interface__,
                    style_function=lambda x: {"fillColor": "#00dd77", "color": "#009944", "weight": 1.5, "fillOpacity": 0.7},
                    tooltip="Safe Building",
                    popup=folium.Popup(
                        "<b style='color:green'>Safe Building</b><br>Lat: {:.5f}<br>Lon: {:.5f}".format(c.y, c.x),
                        max_width=180
                    )
                ).add_to(safe_fg)
    safe_fg.add_to(m)

    # Flooded buildings
    risk_cfg = {
        "high":     ("#ff2222", "#aa0000", "HIGH RISK",     "red",        "Immediate evacuation required!"),
        "moderate": ("#ffbb00", "#cc8800", "MODERATE RISK", "orange",     "Monitor closely, prepare to evacuate"),
        "low":      ("#ff7700", "#cc5500", "LOW RISK",      "darkorange", "Stay alert, follow local updates"),
    }
    high_bfg = folium.FeatureGroup(name="High Risk Buildings", show=True)
    mod_bfg  = folium.FeatureGroup(name="Moderate Risk Buildings", show=True)
    low_bfg  = folium.FeatureGroup(name="Low Risk Buildings", show=True)
    fg_map   = {"high": high_bfg, "moderate": mod_bfg, "low": low_bfg}

    for i, (_, row) in enumerate(flooded_gdf.iterrows()):
        if i > 150:
            break
        c    = row.geometry.centroid
        risk = get_risk(row.geometry, flood_gdf)
        cfg  = risk_cfg.get(risk, risk_cfg["low"])
        fill, border, label, color, action = cfg
        target = fg_map.get(risk, low_bfg)

        popup_html = (
            "<div style='font-family:Arial;width:200px'>"
            "<b style='color:{color}'>{label}</b><hr>"
            "Building #: {num}<br>District: {dist}<br>River: {river}<br>"
            "Lat: {lat:.5f} | Lon: {lon:.5f}<hr>"
            "<b>Action:</b> {action}</div>"
        ).format(color=color, label=label, num=i+1, dist=loc_key,
                 river=loc["river"], lat=c.y, lon=c.x, action=action)

        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, f=fill, b=border: {"fillColor": f, "color": b, "weight": 2.5, "fillOpacity": 0.85},
            tooltip="{} — Building #{}".format(label, i+1),
            popup=folium.Popup(popup_html, max_width=220)
        ).add_to(target)

        folium.CircleMarker(
            location=[c.y, c.x], radius=7,
            color=border, fill=True, fill_color=fill, fill_opacity=0.95,
            tooltip="{} #{}".format(label, i+1),
            popup=folium.Popup(popup_html, max_width=220)
        ).add_to(target)

    high_bfg.add_to(m)
    mod_bfg.add_to(m)
    low_bfg.add_to(m)

    # Water flow arrows
    flow_fg = folium.FeatureGroup(name="Water Flow", show=True)
    mnx, mny, mxx, mxy = flood_gdf.total_bounds
    sx = (mxx - mnx) / 4
    sy = (mxy - mny) / 3
    for i in range(4):
        for j in range(3):
            lat1 = mny + (j + 0.8) * sy
            lon1 = mnx + (i + 0.5) * sx
            lat2 = lat1 - sy * 0.45
            lon2 = lon1 + sx * 0.1
            folium.PolyLine(
                [[lat1, lon1], [lat2, lon2]],
                color="#00eeff", weight=3, opacity=0.9, tooltip="Water flow direction"
            ).add_to(flow_fg)
            folium.Marker(
                [lat2, lon2],
                icon=folium.DivIcon(
                    html='<div style="font-size:16px;color:#00eeff">&#9660;</div>',
                    icon_size=(18, 18), icon_anchor=(9, 9)
                )
            ).add_to(flow_fg)
    flow_fg.add_to(m)

    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(toggle_display=True, position="bottomleft", width=120, height=120, zoom_level_offset=-5).add_to(m)
    plugins.MousePosition(position="bottomright", prefix="Coords: ").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m


# ── Rainfall analysis ─────────────────────────────────────────────
def analyse_rainfall(mm, hours):
    intensity = mm / hours if hours > 0 else 0
    if mm < 25:
        return {"risk": "Low",     "emoji": "🟢", "color": "#2ecc71",
                "advice": "Light rainfall. Minimal flood risk.",
                "expected": "< 5%", "intensity": round(intensity, 2)}
    elif mm < 65:
        return {"risk": "Moderate","emoji": "🟡", "color": "#f39c12",
                "advice": "Low-lying areas may experience waterlogging.",
                "expected": "5-20%", "intensity": round(intensity, 2)}
    elif mm < 115:
        return {"risk": "High",    "emoji": "🔴", "color": "#e74c3c",
                "advice": "Heavy rainfall! Significant flood risk.",
                "expected": "20-50%", "intensity": round(intensity, 2)}
    else:
        return {"risk": "Extreme", "emoji": "🚨", "color": "#c0392b",
                "advice": "Extreme rainfall! Immediate evacuation advised.",
                "expected": "> 50%", "intensity": round(intensity, 2)}


# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Uttarakhand Districts")
    st.markdown("---")
    selected = st.selectbox("Select District", list(LOCATIONS.keys()), index=0)
    loc = LOCATIONS[selected]
    risk_color = {"Extreme": "#ff2222", "High": "#ffaa00", "Moderate": "#ffcc00", "Low": "#00cc66"}
    rc = risk_color.get(loc["risk"], "#ffffff")
    st.markdown(
        "<div class='loc-card'>"
        "<b>📍 {name}</b><br>"
        "<small style='opacity:0.7'>{desc}</small><br><br>"
        "<b>River:</b> {river}<br>"
        "<b>Risk:</b> <span style='color:{rc};font-weight:700'>{risk}</span>"
        "</div>".format(name=selected, desc=loc["description"], river=loc["river"], rc=rc, risk=loc["risk"]),
        unsafe_allow_html=True
    )
    st.markdown("---")
    with st.expander("🌧️ Rainfall Analysis", expanded=True):
        rainfall_mm    = st.number_input("Rainfall amount (mm)", min_value=0.0, max_value=1000.0, value=0.0, step=10.0)
        rainfall_hours = st.slider("Duration (hours)", 1, 72, 24)
    st.markdown("---")
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown(
        "<div style='color:gray;font-size:0.72rem;text-align:center'>"
        "GeoFlood v1.0 — Uttarakhand<br>"
        "Dinesh &bull; Likhitha &bull; Gayatri<br>"
        "<small>Data: OpenStreetMap</small></div>",
        unsafe_allow_html=True
    )


# ── Rainfall section ──────────────────────────────────────────────
if rainfall_mm > 0:
    r = analyse_rainfall(rainfall_mm, rainfall_hours)
    st.markdown("### 🌧️ Rainfall Risk Assessment")
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.markdown(
        "<div class='metric-card rain-card'><div class='label'>Rainfall</div>"
        "<div class='value'>{mm}mm</div><div class='sub'>Total</div></div>".format(mm=rainfall_mm),
        unsafe_allow_html=True
    )
    rc2.markdown(
        "<div class='metric-card rain-card'><div class='label'>Duration</div>"
        "<div class='value'>{h}h</div><div class='sub'>Hours</div></div>".format(h=rainfall_hours),
        unsafe_allow_html=True
    )
    rc3.markdown(
        "<div class='metric-card rain-card'><div class='label'>Intensity</div>"
        "<div class='value'>{i}</div><div class='sub'>mm/hour</div></div>".format(i=r["intensity"]),
        unsafe_allow_html=True
    )
    rc4.markdown(
        "<div class='metric-card rain-card'><div class='label'>Risk Level</div>"
        "<div class='value'>{e}</div><div class='sub' style='color:{c}'>{risk}</div></div>".format(
            e=r["emoji"], c=r["color"], risk=r["risk"]
        ),
        unsafe_allow_html=True
    )
    st.markdown(
        "<div class='rain-result'>"
        "<b>Risk:</b> <span style='color:{c};font-weight:700'>{e} {risk}</span>"
        " &nbsp;|&nbsp; <b>Expected affected:</b> {exp}<br><br>"
        "📋 <b>Advisory:</b> {adv}</div>".format(
            c=r["color"], e=r["emoji"], risk=r["risk"],
            exp=r["expected"], adv=r["advice"]
        ),
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────
if "done" not in st.session_state:
    st.session_state.done = False


# ── Run Analysis ──────────────────────────────────────────────────
if run_btn:
    fetch_flood_zones.clear()
    fetch_buildings.clear()

    loc  = LOCATIONS[selected]
    bbox = loc["flood_bbox"]

    with st.spinner("Fetching flood zones for {}...".format(selected)):
        flood_gdf = fetch_flood_zones(loc["place"], bbox)

    with st.spinner("Fetching buildings from OpenStreetMap..."):
        buildings_gdf, is_real = fetch_buildings(loc["place"], bbox)

    if not is_real or len(buildings_gdf) == 0:
        st.warning("No building data found for this area. Flood zones will still be shown.")
        buildings_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        is_real = False

    with st.spinner("Running spatial intersection analysis..."):
        flooded_gdf = find_flooded(buildings_gdf, flood_gdf)

    with st.spinner("Building interactive map..."):
        map_obj = build_map(flood_gdf, buildings_gdf, flooded_gdf, selected)

    total   = len(buildings_gdf)
    flooded = len(flooded_gdf)
    pct     = round((flooded / total) * 100, 1) if total else 0
    safe    = total - flooded

    st.session_state.done      = True
    st.session_state.total     = total
    st.session_state.flooded   = flooded
    st.session_state.pct       = pct
    st.session_state.safe      = safe
    st.session_state.map_obj   = map_obj
    st.session_state.place     = selected
    st.session_state.river     = loc["river"]
    st.session_state.is_real   = is_real


# ── Results ───────────────────────────────────────────────────────
if st.session_state.done:
    total   = st.session_state.total
    flooded = st.session_state.flooded
    pct     = st.session_state.pct
    safe    = st.session_state.safe

    st.markdown("### 📊 Impact Metrics")
    m1, m2, m3 = st.columns(3)
    m1.markdown(
        "<div class='metric-card total-card'><div class='label'>Total Buildings</div>"
        "<div class='value'>{t}</div><div class='sub'>Found in area</div></div>".format(t=total),
        unsafe_allow_html=True
    )
    m2.markdown(
        "<div class='metric-card flood-card'><div class='label'>Flooded Buildings</div>"
        "<div class='value'>{f}</div>"
        "<div class='sub' style='color:#e74c3c'>{p}% affected</div></div>".format(f=flooded, p=pct),
        unsafe_allow_html=True
    )
    m3.markdown(
        "<div class='metric-card safe-card'><div class='label'>Safe Buildings</div>"
        "<div class='value'>{s}</div>"
        "<div class='sub' style='color:#2ecc71'>{sp}% safe</div></div>".format(s=safe, sp=100 - pct),
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### ⚠️ Risk Classification")
    st.markdown(
        "<div style='background:#111827;border-radius:12px;padding:16px;border:1px solid #1f2937'>"
        "<span class='risk-badge badge-high'>High Risk</span> Over 70% inside flood zone — Immediate evacuation<br>"
        "<span class='risk-badge badge-moderate'>Moderate Risk</span> 30-70% inside flood zone — Monitor closely<br>"
        "<span class='risk-badge badge-low'>Low Risk</span> Under 30% inside flood zone — Stay alert<br>"
        "<span class='risk-badge badge-safe'>Safe</span> Outside flood zone — No immediate action"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Map rendered with st_folium (fixes the iframe trust error) ──
    st.markdown("### 🗺️ Interactive Flood Map")
    st_folium(
        st.session_state.map_obj,
        width=None,
        height=560,
        returned_objects=[]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📈 Impact Summary Chart")
    fig = make_chart(total, flooded)
    st.pyplot(fig)

    is_real  = st.session_state.get("is_real", True)
    data_tag = (
        "<span style='color:#2ecc71'>Real OSM building data</span>"
        if is_real and total > 0
        else "<span style='color:#e74c3c'>No OSM buildings found — flood zones only</span>"
    )
    st.markdown(
        "<div class='info-banner'>"
        "<b>{place}</b> &nbsp;|&nbsp; River: {river} &nbsp;|&nbsp; "
        "{total} buildings &nbsp;|&nbsp; {flooded} flooded ({pct}%) &nbsp;|&nbsp; {safe} safe ({sp}%)<br>"
        "<small style='opacity:0.8'>{tag} &bull; Source: OpenStreetMap (live)</small>"
        "</div>".format(
            place=st.session_state.place,
            river=st.session_state.river,
            total=total, flooded=flooded, pct=pct,
            safe=safe, sp=100 - pct, tag=data_tag
        ),
        unsafe_allow_html=True
    )
