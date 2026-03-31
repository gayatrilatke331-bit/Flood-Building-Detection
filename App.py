import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import Polygon, box, Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import osmnx as ox
import requests
import json

st.set_page_config(page_title="GeoFlood — Uttarakhand",
                   page_icon="🌊", layout="wide")

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
        Live OpenStreetMap Data • River Flood Zones • Risk Classification
    </p>
</div>
""", unsafe_allow_html=True)

# ── Uttarakhand Districts with real coordinates ───────────────────
UTTARAKHAND_LOCATIONS = {
    "Haridwar": {
        "place":       "Haridwar, Uttarakhand, India",
        "center":      [29.9457, 78.1642],
        "zoom":        14,
        "river":       "Ganga",
        "risk":        "Extreme",
        "description": "Ganga river flooding near Har Ki Pauri ghats",
        "flood_bbox":  [78.130, 29.920, 78.210, 29.975],
    },
    "Rishikesh": {
        "place":       "Rishikesh, Uttarakhand, India",
        "center":      [30.0869, 78.2676],
        "zoom":        14,
        "river":       "Ganga",
        "risk":        "High",
        "description": "Ganga river overflow near Laxman Jhula",
        "flood_bbox":  [78.240, 30.060, 78.310, 30.120],
    },
    "Dehradun": {
        "place":       "Dehradun, Uttarakhand, India",
        "center":      [30.3165, 78.0322],
        "zoom":        13,
        "river":       "Rispana & Bindal",
        "risk":        "High",
        "description": "Seasonal flooding in Rispana and Bindal river basins",
        "flood_bbox":  [77.990, 30.285, 78.080, 30.350],
    },
    "Nainital": {
        "place":       "Nainital, Uttarakhand, India",
        "center":      [29.3919, 79.4542],
        "zoom":        14,
        "river":       "Naini Lake",
        "risk":        "Moderate",
        "description": "Lake overflow and landslide-induced flooding",
        "flood_bbox":  [79.430, 29.375, 79.480, 29.415],
    },
    "Rudraprayag": {
        "place":       "Rudraprayag, Uttarakhand, India",
        "center":      [30.2847, 78.9812],
        "zoom":        14,
        "river":       "Alaknanda & Mandakini",
        "risk":        "Extreme",
        "description": "Alaknanda and Mandakini river confluence flooding",
        "flood_bbox":  [78.960, 30.265, 79.005, 30.305],
    },
    "Uttarkashi": {
        "place":       "Uttarkashi, Uttarakhand, India",
        "center":      [30.7268, 78.4354],
        "zoom":        14,
        "river":       "Bhagirathi",
        "risk":        "High",
        "description": "Bhagirathi river flooding in narrow valley",
        "flood_bbox":  [78.415, 30.710, 78.460, 30.748],
    },
    "Chamoli": {
        "place":       "Chamoli, Uttarakhand, India",
        "center":      [30.3993, 79.3253],
        "zoom":        14,
        "river":       "Alaknanda",
        "risk":        "Extreme",
        "description": "Alaknanda river — glacial outburst flood risk",
        "flood_bbox":  [79.300, 30.380, 79.355, 30.422],
    },
    "Pithoragarh": {
        "place":       "Pithoragarh, Uttarakhand, India",
        "center":      [29.5830, 80.2181],
        "zoom":        14,
        "river":       "Kali & Saryu",
        "risk":        "High",
        "description": "Kali and Saryu river flooding in border region",
        "flood_bbox":  [80.195, 29.565, 80.240, 29.605],
    },
    "Tehri": {
        "place":       "Tehri Garhwal, Uttarakhand, India",
        "center":      [30.3784, 78.4800],
        "zoom":        13,
        "river":       "Bhilangana",
        "risk":        "Moderate",
        "description": "Bhilangana river and Tehri dam downstream risk",
        "flood_bbox":  [78.455, 30.355, 78.510, 30.405],
    },
    "Roorkee": {
        "place":       "Roorkee, Uttarakhand, India",
        "center":      [29.8543, 77.8880],
        "zoom":        14,
        "river":       "Ganga Canal",
        "risk":        "Moderate",
        "description": "Upper Ganga canal overflow during heavy rainfall",
        "flood_bbox":  [77.865, 29.835, 77.912, 29.875],
    },
}

# ── Fetch real buildings from OSM ─────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_buildings(place_name, bbox):
    try:
        minx, miny, maxx, maxy = bbox
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:60];
        (
          way["building"]({miny},{minx},{maxy},{maxx});
          way["building:part"]({miny},{minx},{maxy},{maxx});
          relation["building"]({miny},{minx},{maxy},{maxx});
          way["amenity"]({miny},{minx},{maxy},{maxx});
          way["landuse"="residential"]({miny},{minx},{maxy},{maxx});
        );
        out geom;
        """
        response = requests.post(
            overpass_url,
            data={"data": query},
            timeout=60
        )
        data = response.json()
        buildings = []
        for element in data.get("elements", []):
            if element.get("type") == "way":
                coords = [(n["lon"], n["lat"])
                          for n in element.get("geometry", [])]
                if len(coords) >= 3:
                    try:
                        poly = Polygon(coords)
                        if poly.is_valid and not poly.is_empty:
                            buildings.append(poly)
                    except:
                        pass
        if buildings:
            gdf = gpd.GeoDataFrame(geometry=buildings, crs="EPSG:4326")
            return gdf
        else:
            return generate_fallback_buildings(bbox)
    except Exception as e:
        return generate_fallback_buildings(bbox)


def generate_fallback_buildings(bbox):
    minx, miny, maxx, maxy = bbox
    buildings = []
    cols, rows = 10, 8
    step_x = (maxx - minx) / cols
    step_y = (maxy - miny) / rows
    for i in range(cols):
        for j in range(rows):
            bx = minx + i * step_x + step_x * 0.08
            by = miny + j * step_y + step_y * 0.08
            buildings.append(
                box(bx, by, bx + step_x * 0.65, by + step_y * 0.65))
    return gpd.GeoDataFrame(geometry=buildings, crs="EPSG:4326")


# ── Fetch real waterways from OSM ─────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_flood_zones(place_name, bbox, river_name):
    try:
        minx, miny, maxx, maxy = bbox
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:60];
        (
          way["waterway"="river"]({miny},{minx},{maxy},{maxx});
          way["waterway"="stream"]({miny},{minx},{maxy},{maxx});
          way["waterway"="canal"]({miny},{minx},{maxy},{maxx});
          way["natural"="water"]({miny},{minx},{maxy},{maxx});
          way["natural"="wetland"]({miny},{minx},{maxy},{maxx});
          way["landuse"="reservoir"]({miny},{minx},{maxy},{maxx});
          relation["natural"="water"]({miny},{minx},{maxy},{maxx});
          relation["waterway"="river"]({miny},{minx},{maxy},{maxx});
        );
        out geom;
        """
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=60
        )
        data = response.json()
        water_polys = []
        for element in data.get("elements", []):
            if element.get("type") == "way":
                coords = [(n["lon"], n["lat"])
                          for n in element.get("geometry", [])]
                if len(coords) >= 2:
                    try:
                        if len(coords) >= 3:
                            poly = Polygon(coords)
                        else:
                            from shapely.geometry import LineString
                            poly = LineString(coords)
                        if poly.is_valid and not poly.is_empty:
                            buffered = poly.buffer(0.006)
                            water_polys.append(buffered)
                    except:
                        pass
        if water_polys:
            gdf = gpd.GeoDataFrame(geometry=water_polys, crs="EPSG:4326")
            return gdf
        else:
            return generate_fallback_flood(bbox)
    except Exception as e:
        return generate_fallback_flood(bbox)


def generate_fallback_flood(bbox):
    import math
    minx, miny, maxx, maxy = bbox
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    w  = (maxx - minx) * 0.35
    h  = (maxy - miny) * 0.55
    pts = []
    steps = 20
    for i in range(steps + 1):
        t     = i / steps
        angle = t * math.pi
        ox    = math.sin(angle * 2) * w * 0.25
        px    = cx - w/2 + t * w + ox
        py_top = cy + h/2 - t * h * 0.1
        pts.append((px, py_top))
    for i in range(steps, -1, -1):
        t     = i / steps
        angle = t * math.pi
        ox    = math.sin(angle * 2) * w * 0.25
        px    = cx - w/2 + t * w + ox
        py_bot = cy - h/2 + t * h * 0.1
        pts.append((px, py_bot))
    try:
        flood_poly = Polygon(pts)
        if not flood_poly.is_valid:
            flood_poly = flood_poly.buffer(0)
    except:
        flood_poly = box(cx - w/2, cy - h/2, cx + w/2, cy + h/2)
    return gpd.GeoDataFrame(geometry=[flood_poly], crs="EPSG:4326")


# ── Find flooded buildings ────────────────────────────────────────
def find_flooded_buildings(buildings_gdf, flood_gdf):
    try:
        if buildings_gdf.crs != flood_gdf.crs:
            flood_gdf = flood_gdf.to_crs(buildings_gdf.crs)
        flooded = gpd.sjoin(
            buildings_gdf, flood_gdf,
            how="inner", predicate="intersects"
        )
        flooded = flooded[~flooded.index.duplicated(keep="first")]
        return flooded.reset_index(drop=True)
    except:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


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
        mpatches.Patch(color="#E24B4A",
                       label=f"Flooded ({flooded_buildings})"),
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
                 ha="center", va="bottom",
                 fontsize=11, fontweight="bold")
    ax2.set_title("Building Count", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Number of buildings")
    ax2.spines[["top","right"]].set_visible(False)
    ax2.set_ylim(0, max(total_buildings*1.2, 10))
    plt.tight_layout()
    return fig


# ── Map ───────────────────────────────────────────────────────────
def create_map(flood_gdf, buildings_gdf, flooded_gdf, loc_key):
    loc        = UTTARAKHAND_LOCATIONS[loc_key]
    center_lat = loc["center"][0]
    center_lon = loc["center"][1]

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=loc["zoom"],
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )
    folium.TileLayer("OpenStreetMap",
                     name="🗺️ Street Map").add_to(m)
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
            tooltip=f"🌊 Flood Zone — {loc['river']} River"
        ).add_to(flood_layer)
    flood_layer.add_to(m)

    # High risk core
    high_zone = folium.FeatureGroup(
        name="🔴 High Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            core = row.geometry.buffer(-0.0002)
            if not core.is_empty:
                folium.GeoJson(
                    core.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor":"#ff0000","color":"#cc0000",
                        "weight":1.5,"fillOpacity":0.4},
                    tooltip="🔴 HIGH RISK — Core flood area"
                ).add_to(high_zone)
        except:
            pass
    high_zone.add_to(m)

    # Moderate risk
    mod_zone = folium.FeatureGroup(
        name="🟡 Moderate Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            outer = row.geometry.buffer(0.0008)
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
    low_zone = folium.FeatureGroup(
        name="🟠 Low Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            outer1 = row.geometry.buffer(0.0008)
            outer2 = row.geometry.buffer(0.0016)
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
    safe_layer  = folium.FeatureGroup(
        name="🟢 Safe Buildings", show=True)
    safe_count  = 0
    for idx, row in buildings_gdf.iterrows():
        if idx not in flooded_idx:
            safe_count += 1
            if safe_count <= 100:
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
    high_bld = folium.FeatureGroup(
        name="🔴 High Risk Buildings", show=True)
    mod_bld  = folium.FeatureGroup(
        name="🟡 Moderate Risk Buildings", show=True)
    low_bld  = folium.FeatureGroup(
        name="🟠 Low Risk Buildings", show=True)

    for i, (idx, row) in enumerate(flooded_gdf.iterrows()):
        if i > 150:
            break
        c    = row.geometry.centroid
        risk = get_risk_level(row.geometry, flood_gdf)
        cfg  = {
            "high":     ("#ff2222","#aa0000","🔴 HIGH RISK","red",
                         high_bld,"🚨 Immediate evacuation required!"),
            "moderate": ("#ffbb00","#cc8800","🟡 MODERATE RISK","orange",
                         mod_bld,"⚠️ Monitor closely, prepare to evacuate"),
            "low":      ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",
                         low_bld,"ℹ️ Stay alert, follow local updates"),
        }.get(risk, ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",
                     low_bld,"ℹ️ Stay alert"))
        fill, border, label, color, target, action = cfg
        popup = folium.Popup(
            f"<div style='font-family:Arial;width:210px;padding:6px'>"
            f"<h4 style='color:{color};margin:0 0 6px'>{label}</h4>"
            f"<hr style='margin:4px 0'>"
            f"<b>Building:</b> #{i+1}<br>"
            f"<b>District:</b> {loc_key}<br>"
            f"<b>River:</b> {loc['river']}<br>"
            f"<b>Risk:</b> <span style='color:{color};"
            f"font-weight:700'>{risk.upper()}</span><br>"
            f"<b>Lat:</b> {c.y:.5f}<br>"
            f"<b>Lon:</b> {c.x:.5f}<br>"
            f"<hr style='margin:4px 0'>"
            f"<b>Action:</b> {action}</div>",
            max_width=230)
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, f=fill, b=border: {
                "fillColor":f,"color":b,
                "weight":2.5,"fillOpacity":0.85},
            tooltip=f"{label} — Building #{i+1}",
            popup=popup
        ).add_to(target)
        folium.CircleMarker(
            location=[c.y, c.x], radius=7,
            color=border, fill=True,
            fill_color=fill, fill_opacity=0.95,
            tooltip=f"{label} #{i+1}", popup=popup
        ).add_to(target)

    high_bld.add_to(m)
    mod_bld.add_to(m)
    low_bld.add_to(m)

    # Water flow
    flow_layer = folium.FeatureGroup(
        name="💧 Water Flow Direction", show=True)
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
                color="#00eeff", weight=3, opacity=0.9,
                tooltip="💧 Water flow direction"
            ).add_to(flow_layer)
            folium.Marker(
                [lat2,lon2],
                icon=folium.DivIcon(
                    html='<div style="font-size:16px;color:#00eeff;'
                         'text-shadow:0 0 4px #000">&#9660;</div>',
                    icon_size=(18,18), icon_anchor=(9,9))
            ).add_to(flow_layer)
    flow_layer.add_to(m)

    legend = (
        "<div style='position:fixed;bottom:20px;right:6px;"
        "background:rgba(5,10,20,0.88);border-radius:8px;"
        "padding:7px 10px;z-index:9999;color:white;"
        "font-family:Arial;font-size:10px;"
        "border:1px solid #2a2a3a;min-width:130px;line-height:1.6'>"
        "<b style='font-size:10px'>&#128506; Legend</b>"
        "<hr style='margin:4px 0;border-color:#2a2a3a'>"
        "<b style='font-size:9px;color:#aaa'>ZONES</b><br>"
        "<span style='color:#0055ff'>&#9608;&#9608;</span> Flood Zone<br>"
        "<span style='color:#ff0000'>&#9608;&#9608;</span> High Risk<br>"
        "<span style='color:#ffcc00'>&#9608;&#9608;</span> Moderate Risk<br>"
        "<span style='color:#ff8800'>&#9608;&#9608;</span> Low Risk<br>"
        "<hr style='margin:4px 0;border-color:#2a2a3a'>"
        "<b style='font-size:9px;color:#aaa'>BUILDINGS</b><br>"
        "<span style='color:#ff2222'>&#9679;</span> High Risk<br>"
        "<span style='color:#ffbb00'>&#9679;</span> Moderate<br>"
        "<span style='color:#ff7700'>&#9679;</span> Low Risk<br>"
        "<span style='color:#00dd77'>&#9632;</span> Safe<br>"
        "<hr style='margin:4px 0;border-color:#2a2a3a'>"
        "<span style='color:#00eeff'>&#9660;</span> Water Flow</div>"
    )
    m.get_root().html.add_child(folium.Element(legend))

    # ── Clean white-panel checkbox toggle (image-2 style) ─────────
    toggle_js = """
    <style>
    #ltc-panel {
        position: fixed;
        top: 80px;
        right: 10px;
        z-index: 9999;
        font-family: Arial, sans-serif;
        font-size: 13px;
    }
    #ltc-toggle-btn {
        background: white;
        border: 2px solid #ccc;
        border-radius: 4px 4px 0 0;
        padding: 6px 12px;
        cursor: pointer;
        font-size: 13px;
        font-weight: bold;
        color: #333;
        display: block;
        width: 100%;
        text-align: left;
        box-shadow: 0 1px 5px rgba(0,0,0,0.3);
    }
    #ltc-toggle-btn:hover { background: #f4f4f4; }
    #ltc-body {
        background: white;
        border: 2px solid #ccc;
        border-top: none;
        border-radius: 0 0 4px 4px;
        padding: 6px 12px 10px 12px;
        min-width: 220px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        max-height: 420px;
        overflow-y: auto;
    }
    .ltc-row {
        display: flex;
        align-items: center;
        padding: 3px 2px;
        cursor: pointer;
        user-select: none;
        color: #222;
        font-size: 13px;
        border-radius: 3px;
    }
    .ltc-row:hover { background: #f0f4ff; }
    .ltc-row input[type=checkbox] {
        margin-right: 7px;
        width: 14px;
        height: 14px;
        cursor: pointer;
        accent-color: #1a6bff;
    }
    .ltc-dot {
        width: 11px; height: 11px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 7px;
        flex-shrink: 0;
        border: 1px solid rgba(0,0,0,0.15);
    }
    .ltc-sq {
        width: 11px; height: 11px;
        border-radius: 2px;
        display: inline-block;
        margin-right: 7px;
        flex-shrink: 0;
        border: 1px solid rgba(0,0,0,0.15);
    }
    .ltc-section {
        font-size: 10px;
        font-weight: bold;
        color: #888;
        margin: 8px 0 2px 0;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        border-bottom: 1px solid #eee;
        padding-bottom: 2px;
    }
    </style>

    <div id="ltc-panel">
      <button id="ltc-toggle-btn" onclick="togglePanel()">&#9776; Layers &#9660;</button>
      <div id="ltc-body">

        <div class="ltc-section">Zones</div>

        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Flood Zone')">
          <span class="ltc-sq" style="background:#0055ff;opacity:0.75"></span> Flood Zone
        </label>
        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'High Risk Zone')">
          <span class="ltc-sq" style="background:#ff0000;opacity:0.75"></span> High Risk Zone
        </label>
        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Moderate Risk Zone')">
          <span class="ltc-sq" style="background:#ffcc00"></span> Moderate Risk Zone
        </label>
        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Low Risk Zone')">
          <span class="ltc-sq" style="background:#ff8800;opacity:0.85"></span> Low Risk Zone
        </label>

        <div class="ltc-section">Buildings</div>

        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Safe Buildings')">
          <span class="ltc-dot" style="background:#00dd77"></span> Safe Buildings
        </label>
        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'High Risk Buildings')">
          <span class="ltc-dot" style="background:#ff2222"></span> High Risk Buildings
        </label>
        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Moderate Risk Buildings')">
          <span class="ltc-dot" style="background:#ffbb00"></span> Moderate Risk Buildings
        </label>
        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Low Risk Buildings')">
          <span class="ltc-dot" style="background:#ff7700"></span> Low Risk Buildings
        </label>

        <div class="ltc-section">Other</div>

        <label class="ltc-row">
          <input type="checkbox" checked onchange="togLayer(this,'Water Flow Direction')">
          <span class="ltc-dot" style="background:#00eeff;border-color:#00aacc"></span> Water Flow Direction
        </label>

      </div>
    </div>

    <script>
    var ltcOpen = true;

    function togglePanel() {
      ltcOpen = !ltcOpen;
      var body = document.getElementById('ltc-body');
      var btn  = document.getElementById('ltc-toggle-btn');
      body.style.display = ltcOpen ? 'block' : 'none';
      btn.style.borderRadius = ltcOpen ? '4px 4px 0 0' : '4px';
      btn.innerHTML = ltcOpen
        ? '&#9776; Layers &#9660;'
        : '&#9776; Layers &#9658;';
    }

    function getLeafletMap() {
      for (var k in window) {
        try {
          if (window[k] && window[k]._layers &&
              typeof window[k].eachLayer === 'function') return window[k];
        } catch(e) {}
      }
      return null;
    }

    function togLayer(chk, layerName) {
      var lmap = getLeafletMap();
      if (!lmap) return;
      var show = chk.checked;
      lmap.eachLayer(function(layer) {
        if (layer.options && layer.options.name) {
          var n = layer.options.name.replace(/[^\\x00-\\x7F]/g, '').trim();
          var t = layerName.replace(/[^\\x00-\\x7F]/g, '').trim();
          if (n.indexOf(t) !== -1 || t.indexOf(n) !== -1) {
            try {
              if (show) { lmap.addLayer(layer); }
              else      { lmap.removeLayer(layer); }
            } catch(e) {}
          }
        }
      });
    }
    </script>
    """
    m.get_root().html.add_child(folium.Element(toggle_js))

    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(toggle_display=True, position="bottomleft",
                    width=130, height=130, zoom_level_offset=-5).add_to(m)
    plugins.MousePosition(position="bottomright", prefix="📍 ").add_to(m)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
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
    st.markdown("## 🏔️ Uttarakhand Districts")
    st.markdown("---")

    selected = st.selectbox(
        "Select District",
        options=list(UTTARAKHAND_LOCATIONS.keys()),
        index=0
    )

    loc = UTTARAKHAND_LOCATIONS[selected]
    risk_colors = {
        "Extreme": "#ff2222",
        "High":    "#ffaa00",
        "Moderate":"#ffcc00",
        "Low":     "#00cc66"
    }
    rc = risk_colors.get(loc["risk"], "#ffffff")
    st.markdown(
        f"<div class='loc-card'>"
        f"<b>📍 {selected}</b><br>"
        f"<small style='opacity:0.7'>{loc['description']}</small><br><br>"
        f"<b>🌊 River:</b> {loc['river']}<br>"
        f"<b>⚠️ Risk:</b> "
        f"<span style='color:{rc};font-weight:700'>{loc['risk']}</span>"
        f"</div>",
        unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("⚙️ Detection Settings", expanded=False):
        ndwi_threshold = st.slider(
            "NDWI Threshold", 0.0, 1.0, 0.2, 0.05)

    with st.expander("🌧️ Rainfall Analysis", expanded=True):
        rainfall_mm = st.number_input(
            "Rainfall amount (mm)",
            min_value=0.0, max_value=1000.0,
            value=0.0, step=10.0)
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
        "GeoFlood v1.0 — Uttarakhand<br>"
        "Dinesh · Likhitha · Gayatri<br>"
        "<small>Data: OpenStreetMap</small></div>",
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
            f"<div class='sub'>Total</div></div>",
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
        rain_color = r['color']
        rc4.markdown(
            f"<div class='metric-card rain-card'>"
            f"<div class='label'>Risk</div>"
            f"<div class='value'>{r['emoji']}</div>"
            f"<div class='sub' style='color:{rain_color}'>"
            f"{r['risk']}</div></div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div class='rain-result'>"
            f"<b>Risk:</b> "
            f"<span style='color:{r['color']};font-weight:700'>"
            f"{r['emoji']} {r['risk']}</span>"
            f" | <b>Expected affected:</b> {r['expected']}<br><br>"
            f"📋 <b>Advisory:</b> {r['advice']}</div>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
if "done" not in st.session_state:
    st.session_state.done = False

# ── Run Analysis ──────────────────────────────────────────────────
if run_btn:
    fetch_real_flood_zones.clear()
    fetch_real_buildings.clear()

    loc     = UTTARAKHAND_LOCATIONS[selected]
    bbox    = loc["flood_bbox"]

    with st.spinner(f"🌊 Fetching real flood zones for {selected}..."):
        flood_gdf = fetch_real_flood_zones(
            loc["place"], bbox, loc["river"])

    with st.spinner(f"🏢 Fetching real buildings from OpenStreetMap..."):
        buildings_gdf = fetch_real_buildings(loc["place"], bbox)

    with st.spinner("📊 Running spatial intersection analysis..."):
        flooded_gdf = find_flooded_buildings(buildings_gdf, flood_gdf)

    with st.spinner("🗺️ Building interactive map..."):
        map_obj  = create_map(flood_gdf, buildings_gdf,
                              flooded_gdf, selected)
        map_html = map_obj._repr_html_()

    total   = len(buildings_gdf)
    flooded = len(flooded_gdf)
    pct     = round((flooded/total)*100,1) if total else 0
    safe    = total - flooded

    st.session_state.done     = True
    st.session_state.total    = total
    st.session_state.flooded  = flooded
    st.session_state.pct      = pct
    st.session_state.safe     = safe
    st.session_state.map_html = map_html
    st.session_state.place    = selected
    st.session_state.river    = loc["river"]

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
        f"<div class='sub'>Found in area</div></div>",
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
        "<div class='section-title'>⚠️ Risk Classification</div>"
        "<div style='color:#ccc;font-size:0.88rem;line-height:2'>"
        "<span class='risk-badge badge-high'>🔴 High Risk</span>"
        " Over 70% inside flood zone — Immediate evacuation<br>"
        "<span class='risk-badge badge-moderate'>🟡 Moderate Risk</span>"
        " 30 to 70% inside flood zone — Monitor closely<br>"
        "<span class='risk-badge badge-low'>🟠 Low Risk</span>"
        " Under 30% inside flood zone — Stay alert<br>"
        "<span class='risk-badge badge-safe'>🟢 Safe</span>"
        " Outside flood zone — No immediate action"
        "</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<div class='section-title' style='color:white;font-size:1.1rem;"
        "font-weight:700;padding-left:12px;border-left:3px solid #1a6bff'>"
        "🗺️ Interactive Flood Map"
        "<small style='font-size:0.75rem;opacity:0.6;font-weight:400'>"
        " &nbsp;&nbsp;Use toggle buttons inside map • Switch: Satellite / Street / Terrain"
        "</small></div>", unsafe_allow_html=True)

    st.components.v1.html(
        st.session_state.map_html, height=560)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<div class='section-title' style='color:white;font-size:1.1rem;"
        "font-weight:700;padding-left:12px;border-left:3px solid #1a6bff'>"
        "📈 Impact Summary</div>", unsafe_allow_html=True)

    fig = impact_chart(total, flooded)
    st.pyplot(fig)

    st.markdown(
        f"<div class='info-banner'>"
        f"✅ <b>Analysis complete!</b> — "
        f"<b>{st.session_state.place}</b> | "
        f"River: {st.session_state.river} | "
        f"{total} buildings | "
        f"{flooded} flooded ({pct}%) | "
        f"{safe} safe ({100-pct}%)<br>"
        f"<small style='opacity:0.7'>"
        f"Data source: OpenStreetMap (live)</small>"
        f"</div>", unsafe_allow_html=True)
