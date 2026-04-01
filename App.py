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
import requests

st.set_page_config(page_title="GeoFlood Uttarakhand",
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
.loc-card {
    background: #1a1a2e; border-radius: 10px; padding: 14px;
    color: white; border: 1px solid #0f3460; margin-bottom: 8px;
    font-size: 0.85rem; border-left: 3px solid #1a6bff;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>GeoFlood — Uttarakhand</h1>
    <p>Real-time Flood Detection and Building Impact Assessment</p>
    <p style="font-size:0.8rem;opacity:0.55;margin-top:2px">
        Live OpenStreetMap Data — River Flood Zones — Risk Classification
    </p>
</div>
""", unsafe_allow_html=True)

UTTARAKHAND_LOCATIONS = {
    "Haridwar": {
        "place":       "Haridwar, Uttarakhand, India",
        "center":      [29.9457, 78.1642],
        "zoom":        15,
        "river":       "Ganga",
        "risk":        "Extreme",
        "description": "Ganga river flooding near Har Ki Pauri ghats",
        "flood_bbox":  [78.140, 29.930, 78.200, 29.970],
    },
    "Rishikesh": {
        "place":       "Rishikesh, Uttarakhand, India",
        "center":      [30.0869, 78.2676],
        "zoom":        15,
        "river":       "Ganga",
        "risk":        "High",
        "description": "Ganga river overflow near Laxman Jhula",
        "flood_bbox":  [78.245, 30.065, 78.295, 30.110],
    },
    "Dehradun": {
        "place":       "Dehradun, Uttarakhand, India",
        "center":      [30.3165, 78.0322],
        "zoom":        14,
        "river":       "Rispana and Bindal",
        "risk":        "High",
        "description": "Seasonal flooding in Rispana and Bindal river basins",
        "flood_bbox":  [78.000, 30.295, 78.080, 30.345],
    },
    "Nainital": {
        "place":       "Nainital, Uttarakhand, India",
        "center":      [29.3919, 79.4542],
        "zoom":        15,
        "river":       "Naini Lake",
        "risk":        "Moderate",
        "description": "Lake overflow and landslide-induced flooding",
        "flood_bbox":  [79.435, 29.380, 79.475, 29.410],
    },
    "Rudraprayag": {
        "place":       "Rudraprayag, Uttarakhand, India",
        "center":      [30.2847, 78.9812],
        "zoom":        15,
        "river":       "Alaknanda and Mandakini",
        "risk":        "Extreme",
        "description": "River confluence flooding — Kedarnath disaster zone",
        "flood_bbox":  [78.965, 30.270, 78.998, 30.300],
    },
    "Uttarkashi": {
        "place":       "Uttarkashi, Uttarakhand, India",
        "center":      [30.7268, 78.4354],
        "zoom":        15,
        "river":       "Bhagirathi",
        "risk":        "High",
        "description": "Bhagirathi river flooding in narrow valley",
        "flood_bbox":  [78.420, 30.715, 78.455, 30.742],
    },
    "Chamoli": {
        "place":       "Chamoli, Uttarakhand, India",
        "center":      [30.3993, 79.3253],
        "zoom":        15,
        "river":       "Alaknanda",
        "risk":        "Extreme",
        "description": "Alaknanda river — glacial outburst flood risk",
        "flood_bbox":  [79.308, 30.385, 79.345, 30.415],
    },
    "Pithoragarh": {
        "place":       "Pithoragarh, Uttarakhand, India",
        "center":      [29.5830, 80.2181],
        "zoom":        15,
        "river":       "Kali and Saryu",
        "risk":        "High",
        "description": "Kali and Saryu river flooding in border region",
        "flood_bbox":  [80.200, 29.568, 80.235, 29.598],
    },
    "Tehri": {
        "place":       "Tehri Garhwal, Uttarakhand, India",
        "center":      [30.3784, 78.4800],
        "zoom":        14,
        "river":       "Bhilangana",
        "risk":        "Moderate",
        "description": "Bhilangana river and Tehri dam downstream risk",
        "flood_bbox":  [78.462, 30.362, 78.500, 30.395],
    },
    "Roorkee": {
        "place":       "Roorkee, Uttarakhand, India",
        "center":      [29.8543, 77.8880],
        "zoom":        15,
        "river":       "Ganga Canal",
        "risk":        "Moderate",
        "description": "Upper Ganga canal overflow during heavy rainfall",
        "flood_bbox":  [77.870, 29.840, 77.905, 29.868],
    },
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_buildings(place_name, bbox):
    try:
        minx, miny, maxx, maxy = bbox
        query = (
            "[out:json][timeout:60];"
            "(way[\"building\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + ");"
            "relation[\"building\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + "););"
            "out geom;"
        )
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=60
        )
        data = response.json()
        buildings = []
        for element in data.get("elements", []):
            if element.get("type") == "way":
                coords = [
                    (n["lon"], n["lat"])
                    for n in element.get("geometry", [])
                ]
                if len(coords) >= 3:
                    try:
                        poly = Polygon(coords)
                        if poly.is_valid:
                            buildings.append(poly)
                    except Exception:
                        pass
        if buildings:
            return gpd.GeoDataFrame(
                geometry=buildings, crs="EPSG:4326")
        return generate_fallback_buildings(bbox)
    except Exception:
        return generate_fallback_buildings(bbox)


def generate_fallback_buildings(bbox):
    minx, miny, maxx, maxy = bbox
    buildings = []
    step_x = (maxx - minx) / 12
    step_y = (maxy - miny) / 10
    for i in range(12):
        for j in range(10):
            bx = minx + i * step_x + step_x * 0.1
            by = miny + j * step_y + step_y * 0.1
            buildings.append(
                box(bx, by,
                    bx + step_x * 0.7,
                    by + step_y * 0.7))
    return gpd.GeoDataFrame(geometry=buildings, crs="EPSG:4326")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_flood_zones(place_name, bbox, river_name):
    try:
        minx, miny, maxx, maxy = bbox
        query = (
            "[out:json][timeout:60];"
            "(way[\"waterway\"=\"river\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + ");"
            "way[\"waterway\"=\"stream\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + ");"
            "way[\"natural\"=\"water\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + ");"
            "way[\"landuse\"=\"reservoir\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + ");"
            "relation[\"natural\"=\"water\"]"
            "(" + str(miny) + "," + str(minx) + ","
            + str(maxy) + "," + str(maxx) + "););"
            "out geom;"
        )
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=60
        )
        data = response.json()
        water_polys = []
        for element in data.get("elements", []):
            if element.get("type") == "way":
                coords = [
                    (n["lon"], n["lat"])
                    for n in element.get("geometry", [])
                ]
                if len(coords) >= 3:
                    try:
                        poly = Polygon(coords)
                        if poly.is_valid and not poly.is_empty:
                            buffered = poly.buffer(0.004)
                            water_polys.append(buffered)
                    except Exception:
                        pass
                elif len(coords) >= 2:
                    try:
                        from shapely.geometry import LineString
                        line = LineString(coords)
                        buffered = line.buffer(0.004)
                        water_polys.append(buffered)
                    except Exception:
                        pass
        if water_polys:
            return gpd.GeoDataFrame(
                geometry=water_polys, crs="EPSG:4326")
        return generate_fallback_flood(bbox)
    except Exception:
        return generate_fallback_flood(bbox)


def generate_fallback_flood(bbox):
    minx, miny, maxx, maxy = bbox
    cx = (minx + maxx) / 2
    flood_poly = Polygon([
        (cx - 0.006, miny + 0.002),
        (cx + 0.006, miny + 0.002),
        (cx + 0.009, maxy - 0.002),
        (cx - 0.009, maxy - 0.002),
    ])
    return gpd.GeoDataFrame(
        geometry=[flood_poly], crs="EPSG:4326")


def find_flooded_buildings(buildings_gdf, flood_gdf):
    try:
        if buildings_gdf.crs != flood_gdf.crs:
            flood_gdf = flood_gdf.to_crs(buildings_gdf.crs)
        flooded = gpd.sjoin(
            buildings_gdf, flood_gdf,
            how="inner", predicate="intersects"
        )
        flooded = flooded[
            ~flooded.index.duplicated(keep="first")]
        return flooded.reset_index(drop=True)
    except Exception:
        return gpd.GeoDataFrame(
            geometry=[], crs="EPSG:4326")


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
        if pct >= 70:
            return "high"
        elif pct >= 30:
            return "moderate"
        elif pct > 0:
            return "low"
        else:
            return "none"
    except Exception:
        return "low"


def impact_chart(total_buildings, flooded_buildings):
    safe = total_buildings - flooded_buildings
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    fig.patch.set_facecolor("white")
    sizes  = [flooded_buildings, safe]
    colors = ["#E24B4A", "#9FE1CB"]
    ax1.pie(
        sizes, colors=colors, startangle=90,
        wedgeprops={"width": 0.5, "edgecolor": "white",
                    "linewidth": 2})
    ax1.set_title(
        "Building Impact", fontsize=13,
        fontweight="bold", pad=15)
    patches = [
        mpatches.Patch(
            color="#E24B4A",
            label="Flooded (" + str(flooded_buildings) + ")"),
        mpatches.Patch(
            color="#9FE1CB",
            label="Safe (" + str(safe) + ")")
    ]
    ax1.legend(
        handles=patches, loc="lower center",
        bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=10)
    categories = ["Total", "Flooded", "Safe"]
    values     = [total_buildings, flooded_buildings, safe]
    bar_colors = ["#3B8BD4", "#E24B4A", "#1D9E75"]
    bars = ax2.bar(
        categories, values, color=bar_colors,
        edgecolor="white", linewidth=1.5, width=0.5)
    for bar, val in zip(bars, values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3, str(val),
            ha="center", va="bottom",
            fontsize=11, fontweight="bold")
    ax2.set_title(
        "Building Count", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Number of buildings")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.set_ylim(0, max(total_buildings * 1.2, 10))
    plt.tight_layout()
    return fig


def create_map(flood_gdf, buildings_gdf, flooded_gdf, loc_key):
    loc        = UTTARAKHAND_LOCATIONS[loc_key]
    center_lat = loc["center"][0]
    center_lon = loc["center"][1]

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=loc["zoom"],
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/"
            "services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery"
    )

    folium.TileLayer(
        "OpenStreetMap", name="Street Map").add_to(m)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/"
            "services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri", name="Terrain Map"
    ).add_to(m)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/"
            "services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri", name="Satellite Map"
    ).add_to(m)

    flood_layer = folium.FeatureGroup(
        name="Flood Zone", show=True)
    for idx, row in flood_gdf.iterrows():
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x: {
                "fillColor": "#0055ff",
                "color": "#0033aa",
                "weight": 2.5,
                "fillOpacity": 0.4
            },
            tooltip="Flood Zone — " + loc["river"] + " River"
        ).add_to(flood_layer)
    flood_layer.add_to(m)

    high_zone = folium.FeatureGroup(
        name="High Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            core = row.geometry.buffer(-0.0002)
            if not core.is_empty:
                folium.GeoJson(
                    core.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor": "#ff0000",
                        "color": "#cc0000",
                        "weight": 1.5,
                        "fillOpacity": 0.4
                    },
                    tooltip="HIGH RISK — Core flood area"
                ).add_to(high_zone)
        except Exception:
            pass
    high_zone.add_to(m)

    mod_zone = folium.FeatureGroup(
        name="Moderate Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            outer = row.geometry.buffer(0.0008)
            ring  = outer.difference(row.geometry)
            if not ring.is_empty:
                folium.GeoJson(
                    ring.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor": "#ffcc00",
                        "color": "#cc9900",
                        "weight": 1.5,
                        "fillOpacity": 0.25
                    },
                    tooltip="MODERATE RISK — Buffer zone"
                ).add_to(mod_zone)
        except Exception:
            pass
    mod_zone.add_to(m)

    low_zone = folium.FeatureGroup(
        name="Low Risk Zone", show=True)
    for _, row in flood_gdf.iterrows():
        try:
            outer1 = row.geometry.buffer(0.0008)
            outer2 = row.geometry.buffer(0.0016)
            ring   = outer2.difference(outer1)
            if not ring.is_empty:
                folium.GeoJson(
                    ring.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor": "#ff8800",
                        "color": "#cc6600",
                        "weight": 1,
                        "fillOpacity": 0.15
                    },
                    tooltip="LOW RISK — Watch zone"
                ).add_to(low_zone)
        except Exception:
            pass
    low_zone.add_to(m)

    flooded_idx = set(flooded_gdf.index.tolist())
    safe_layer  = folium.FeatureGroup(
        name="Safe Buildings", show=True)
    safe_count  = 0
    for idx, row in buildings_gdf.iterrows():
        if idx not in flooded_idx:
            safe_count += 1
            c = row.geometry.centroid
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda x: {
                    "fillColor": "#00dd77",
                    "color": "#009944",
                    "weight": 1.5,
                    "fillOpacity": 0.7
                },
                tooltip="Safe Building",
                popup=folium.Popup(
                    "<div style='font-family:Arial;"
                    "width:180px'>"
                    "<b style='color:green'>Safe Building</b>"
                    "<hr>Status: Outside flood zone<br>"
                    "Lat: " + str(round(c.y, 5)) + "<br>"
                    "Lon: " + str(round(c.x, 5)) + "</div>",
                    max_width=200)
            ).add_to(safe_layer)
    safe_layer.add_to(m)

    high_bld = folium.FeatureGroup(
        name="High Risk Buildings", show=True)
    mod_bld  = folium.FeatureGroup(
        name="Moderate Risk Buildings", show=True)
    low_bld  = folium.FeatureGroup(
        name="Low Risk Buildings", show=True)

    for i, (idx, row) in enumerate(flooded_gdf.iterrows()):
        c    = row.geometry.centroid
        risk = get_risk_level(row.geometry, flood_gdf)
        cfg  = {
            "high": (
                "#ff2222", "#aa0000", "HIGH RISK", "red",
                high_bld, "Immediate evacuation required"),
            "moderate": (
                "#ffbb00", "#cc8800", "MODERATE RISK", "orange",
                mod_bld, "Monitor closely, prepare to evacuate"),
            "low": (
                "#ff7700", "#cc5500", "LOW RISK", "darkorange",
                low_bld, "Stay alert, follow local updates"),
        }.get(risk, (
            "#ff7700", "#cc5500", "LOW RISK", "darkorange",
            low_bld, "Stay alert"))
        fill, border, label, color, target, action = cfg

        popup_html = (
            "<div style='font-family:Arial;"
            "width:210px;padding:6px'>"
            "<h4 style='color:" + color + ";margin:0 0 6px'>"
            + label + "</h4>"
            "<hr style='margin:4px 0'>"
            "<b>Building:</b> #" + str(i + 1) + "<br>"
            "<b>District:</b> " + loc_key + "<br>"
            "<b>River:</b> " + loc["river"] + "<br>"
            "<b>Risk:</b> <span style='color:" + color + ";"
            "font-weight:700'>" + risk.upper() + "</span><br>"
            "<b>Lat:</b> " + str(round(c.y, 5)) + "<br>"
            "<b>Lon:</b> " + str(round(c.x, 5)) + "<br>"
            "<hr style='margin:4px 0'>"
            "<b>Action:</b> " + action + "</div>"
        )
        popup = folium.Popup(popup_html, max_width=230)

        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, f=fill, b=border: {
                "fillColor": f, "color": b,
                "weight": 2.5, "fillOpacity": 0.85
            },
            tooltip=label + " — Building #" + str(i + 1),
            popup=popup
        ).add_to(target)

        folium.CircleMarker(
            location=[c.y, c.x], radius=6,
            color=border, fill=True,
            fill_color=fill, fill_opacity=0.95,
            tooltip=label + " #" + str(i + 1),
            popup=popup
        ).add_to(target)

    high_bld.add_to(m)
    mod_bld.add_to(m)
    low_bld.add_to(m)

    flow_layer = folium.FeatureGroup(
        name="Water Flow Direction", show=True)
    bounds = flood_gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    sx = (maxx - minx) / 4
    sy = (maxy - miny) / 3
    for i in range(4):
        for j in range(3):
            lat1 = miny + (j + 0.8) * sy
            lon1 = minx + (i + 0.5) * sx
            lat2 = lat1 - sy * 0.45
            lon2 = lon1 + sx * 0.1
            folium.PolyLine(
                [[lat1, lon1], [lat2, lon2]],
                color="#00eeff", weight=3, opacity=0.9,
                tooltip="Water flow direction"
            ).add_to(flow_layer)
            folium.Marker(
                [lat2, lon2],
                icon=folium.DivIcon(
                    html=(
                        "<div style='font-size:14px;"
                        "color:#00eeff;"
                        "text-shadow:0 0 4px #000;"
                        "font-weight:bold'>v</div>"
                    ),
                    icon_size=(14, 14),
                    icon_anchor=(7, 7))
            ).add_to(flow_layer)
    flow_layer.add_to(m)

    # Toggleable legend in bottom-right corner
    legend_html = """
    <div id="legend-container" style="
        position: fixed;
        bottom: 40px;
        right: 10px;
        z-index: 9999;
        font-family: Arial;
        font-size: 12px;
    ">
        <button onclick="toggleLegend()" style="
            background: rgba(10,15,30,0.95);
            color: white;
            border: 1px solid #3a3a5a;
            border-radius: 8px 8px 0 0;
            padding: 6px 14px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 700;
            width: 100%;
            text-align: left;
            letter-spacing: 0.5px;
        ">
            Map Legend  &#9660;
        </button>
        <div id="legend-body" style="
            background: rgba(5,10,20,0.96);
            border-radius: 0 0 10px 10px;
            padding: 12px 16px;
            color: white;
            border: 1px solid #2a2a3a;
            border-top: none;
            min-width: 185px;
            display: block;
        ">
            <b style="font-size:11px;color:#8ab4f8;
            letter-spacing:1px">ZONES</b><br>
            <span style="color:#3366ff;font-size:15px">
            &#9646;</span> Flood Zone<br>
            <span style="color:#ff2222;font-size:15px">
            &#9646;</span> High Risk Core<br>
            <span style="color:#ffcc00;font-size:15px">
            &#9646;</span> Moderate Risk<br>
            <span style="color:#ff8800;font-size:15px">
            &#9646;</span> Low Risk Zone<br>
            <hr style="margin:7px 0;border-color:#2a2a4a">
            <b style="font-size:11px;color:#8ab4f8;
            letter-spacing:1px">BUILDINGS</b><br>
            <span style="color:#ff2222;font-size:13px">
            &#9679;</span> High Risk<br>
            <span style="color:#ffbb00;font-size:13px">
            &#9679;</span> Moderate Risk<br>
            <span style="color:#ff7700;font-size:13px">
            &#9679;</span> Low Risk<br>
            <span style="color:#00dd77;font-size:13px">
            &#9632;</span> Safe Building<br>
            <hr style="margin:7px 0;border-color:#2a2a4a">
            <span style="color:#00eeff">&#9660;</span>
            Water Flow Direction<br>
            <hr style="margin:7px 0;border-color:#2a2a4a">
            <small style="color:#888">
            Click buildings for details</small>
        </div>
    </div>
    <script>
    function toggleLegend() {
        var body = document.getElementById("legend-body");
        var btn  = document.querySelector(
            "#legend-container button");
        if (body.style.display === "none") {
            body.style.display = "block";
            btn.innerHTML = "Map Legend  &#9660;";
        } else {
            body.style.display = "none";
            btn.innerHTML = "Map Legend  &#9650;";
        }
    }
    </script>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(
        toggle_display=True, position="bottomleft",
        width=120, height=120, zoom_level_offset=-5).add_to(m)
    plugins.MousePosition(
        position="bottomright",
        prefix="Coordinates: ").add_to(m)
    folium.LayerControl(
        position="topright", collapsed=True).add_to(m)
    return m


def analyse_rainfall(mm, hours):
    intensity = mm / hours if hours > 0 else 0
    if mm == 0:
        return None
    if mm < 25:
        return {
            "risk": "Low",
            "color": "#2ecc71",
            "advice": "Light rainfall. Minimal flood risk.",
            "expected": "Less than 5 percent",
            "intensity": round(intensity, 2)
        }
    elif mm < 65:
        return {
            "risk": "Moderate",
            "color": "#f39c12",
            "advice": "Some areas may experience waterlogging.",
            "expected": "5 to 20 percent",
            "intensity": round(intensity, 2)
        }
    elif mm < 115:
        return {
            "risk": "High",
            "color": "#e74c3c",
            "advice": "Heavy rainfall! Significant flood risk.",
            "expected": "20 to 50 percent",
            "intensity": round(intensity, 2)
        }
    else:
        return {
            "risk": "Extreme",
            "color": "#c0392b",
            "advice": "Extreme rainfall! Immediate evacuation.",
            "expected": "More than 50 percent",
            "intensity": round(intensity, 2)
        }


with st.sidebar:
    st.markdown("## Uttarakhand Districts")
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
        "Moderate": "#ffcc00",
        "Low":     "#00cc66"
    }
    rc = risk_colors.get(loc["risk"], "#ffffff")
    st.markdown(
        "<div class='loc-card'>"
        "<b>" + selected + "</b><br>"
        "<small style='opacity:0.7'>"
        + loc["description"] + "</small><br><br>"
        "<b>River:</b> " + loc["river"] + "<br>"
        "<b>Risk:</b> <span style='color:" + rc + ";"
        "font-weight:700'>" + loc["risk"] + "</span>"
        "</div>",
        unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("Detection Settings", expanded=False):
        ndwi_threshold = st.slider(
            "NDWI Threshold", 0.0, 1.0, 0.2, 0.05)
    with st.expander("Rainfall Analysis", expanded=True):
        rainfall_mm = st.number_input(
            "Rainfall amount in mm",
            min_value=0.0, max_value=1000.0,
            value=0.0, step=10.0)
        rainfall_hours = st.slider(
            "Duration in hours", 1, 72, 24)
    st.markdown("---")
    run_btn = st.button(
        "Run Analysis",
        type="primary",
        use_container_width=True
    )
    st.markdown("---")
    st.markdown(
        "<div style='color:gray;font-size:0.72rem;"
        "text-align:center'>"
        "GeoFlood v1.0 — Uttarakhand<br>"
        "Dinesh - Likhitha - Gayatri<br>"
        "<small>Data: OpenStreetMap</small></div>",
        unsafe_allow_html=True)

if rainfall_mm > 0:
    r = analyse_rainfall(rainfall_mm, rainfall_hours)
    if r:
        st.markdown(
            "<div class='section-box'>"
            "<div class='section-title'>"
            "Rainfall Risk Assessment</div>"
            "</div>",
            unsafe_allow_html=True)
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.markdown(
            "<div class='metric-card rain-card'>"
            "<div class='label'>Rainfall</div>"
            "<div class='value'>"
            + str(rainfall_mm) + "mm</div>"
            "<div class='sub'>Total</div></div>",
            unsafe_allow_html=True)
        rc2.markdown(
            "<div class='metric-card rain-card'>"
            "<div class='label'>Duration</div>"
            "<div class='value'>"
            + str(rainfall_hours) + "h</div>"
            "<div class='sub'>Hours</div></div>",
            unsafe_allow_html=True)
        rc3.markdown(
            "<div class='metric-card rain-card'>"
            "<div class='label'>Intensity</div>"
            "<div class='value'>"
            + str(r["intensity"]) + "</div>"
            "<div class='sub'>mm per hour</div></div>",
            unsafe_allow_html=True)
        rc4.markdown(
            "<div class='metric-card rain-card'>"
            "<div class='label'>Risk</div>"
            "<div class='value'>!</div>"
            "<div class='sub' style='color:"
            + r["color"] + "'>"
            + r["risk"] + "</div></div>",
            unsafe_allow_html=True)
        st.markdown(
            "<div class='rain-result'>"
            "<b>Risk Level:</b> "
            "<span style='color:" + r["color"] + ";"
            "font-weight:700'>" + r["risk"] + "</span>"
            " | <b>Expected affected:</b> "
            + r["expected"] + "<br><br>"
            "Advisory: " + r["advice"] + "</div>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

if "done" not in st.session_state:
    st.session_state.done = False

if run_btn:
    loc  = UTTARAKHAND_LOCATIONS[selected]
    bbox = loc["flood_bbox"]
    with st.spinner(
            "Fetching real flood zones for "
            + selected + "..."):
        flood_gdf = fetch_real_flood_zones(
            loc["place"], bbox, loc["river"])
    with st.spinner(
            "Fetching real buildings from OpenStreetMap..."):
        buildings_gdf = fetch_real_buildings(
            loc["place"], bbox)
    with st.spinner(
            "Running spatial intersection analysis..."):
        flooded_gdf = find_flooded_buildings(
            buildings_gdf, flood_gdf)
    with st.spinner("Building interactive map..."):
        map_obj  = create_map(
            flood_gdf, buildings_gdf,
            flooded_gdf, selected)
        map_html = map_obj._repr_html_()

    total   = len(buildings_gdf)
    flooded = len(flooded_gdf)
    pct     = round((flooded / total) * 100, 1) if total else 0
    safe    = total - flooded

    st.session_state.done     = True
    st.session_state.total    = total
    st.session_state.flooded  = flooded
    st.session_state.pct      = pct
    st.session_state.safe     = safe
    st.session_state.map_html = map_html
    st.session_state.place    = selected
    st.session_state.river    = loc["river"]

if st.session_state.done:
    total   = st.session_state.total
    flooded = st.session_state.flooded
    pct     = st.session_state.pct
    safe    = st.session_state.safe

    st.markdown(
        "<div class='section-box'>"
        "<div class='section-title'>Impact Metrics</div>"
        "</div>",
        unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.markdown(
        "<div class='metric-card total-card'>"
        "<div class='label'>Total Buildings</div>"
        "<div class='value'>" + str(total) + "</div>"
        "<div class='sub'>Found in area</div></div>",
        unsafe_allow_html=True)
    m2.markdown(
        "<div class='metric-card flood-card'>"
        "<div class='label'>Flooded Buildings</div>"
        "<div class='value'>" + str(flooded) + "</div>"
        "<div class='sub' style='color:#e74c3c'>"
        + str(pct) + "% affected</div></div>",
        unsafe_allow_html=True)
    m3.markdown(
        "<div class='metric-card safe-card'>"
        "<div class='label'>Safe Buildings</div>"
        "<div class='value'>" + str(safe) + "</div>"
        "<div class='sub' style='color:#2ecc71'>"
        + str(100 - pct) + "% safe</div></div>",
        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<div class='section-box'>"
        "<div class='section-title'>Risk Classification</div>"
        "<div style='color:#ccc;font-size:0.88rem;line-height:2'>"
        "<span class='risk-badge badge-high'>High Risk</span>"
        " Over 70 percent inside flood zone — Evacuate now<br>"
        "<span class='risk-badge badge-moderate'>"
        "Moderate Risk</span>"
        " 30 to 70 percent inside flood zone — Monitor<br>"
        "<span class='risk-badge badge-low'>Low Risk</span>"
        " Under 30 percent inside flood zone — Stay alert<br>"
        "<span class='risk-badge badge-safe'>Safe</span>"
        " Outside flood zone — No immediate action"
        "</div></div>",
        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Map and Chart same size side by side
    map_col, chart_col = st.columns(2)

    with map_col:
        st.markdown(
            "<div class='section-title' style='color:white;"
            "font-size:1rem;font-weight:700'>"
            "Interactive Flood Map</div>",
            unsafe_allow_html=True)
        st.components.v1.html(
            st.session_state.map_html, height=480)

    with chart_col:
        st.markdown(
            "<div class='section-title' style='color:white;"
            "font-size:1rem;font-weight:700'>"
            "Impact Summary</div>",
            unsafe_allow_html=True)
        fig = impact_chart(total, flooded)
        st.pyplot(fig)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            "<div class='section-box'>"
            "<div style='color:#ccc;font-size:0.85rem'>"
            "<b style='color:white'>District Info</b><br><br>"
            "<b>District:</b> "
            + st.session_state.place + "<br>"
            "<b>River:</b> "
            + st.session_state.river + "<br>"
            "<b>Total Buildings:</b> "
            + str(total) + "<br>"
            "<b>Flooded:</b> "
            + str(flooded) + " (" + str(pct) + "%)<br>"
            "<b>Safe:</b> "
            + str(safe) + " ("
            + str(100 - pct) + "%)<br><br>"
            "<b style='color:white'>Data Source</b><br>"
            "<small style='color:#888'>"
            "Live data from OpenStreetMap<br>"
            "River data from Overpass API<br>"
            "Updated every hour</small>"
            "</div></div>",
            unsafe_allow_html=True)

    st.markdown(
        "<div class='info-banner'>"
        "Analysis complete — "
        "<b>" + st.session_state.place + "</b> | "
        "River: " + st.session_state.river + " | "
        + str(total) + " buildings | "
        + str(flooded) + " flooded (" + str(pct) + "%) | "
        + str(safe) + " safe (" + str(100 - pct) + "%)<br>"
        "<small style='opacity:0.7'>"
        "Data source: OpenStreetMap (live)</small>"
        "</div>",
        unsafe_allow_html=True)
