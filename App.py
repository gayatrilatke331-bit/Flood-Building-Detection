import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point, Polygon
import numpy as np

# ------------------ PAGE SETTINGS ------------------
st.set_page_config(layout="wide", page_title="GeoFlood - Uttarakhand")

st.title("🌊 GeoFlood: Flood Prediction and Building Risk System")
st.markdown("AI-Based Geospatial Flood Risk Prediction for Uttarakhand")

# ------------------ LOAD DATA ------------------
@st.cache_data
def load_data():
    flood = gpd.read_file("data/flood_zone.geojson")
    buildings = gpd.read_file("data/buildings.geojson")
    return flood, buildings

flood_gdf, buildings_gdf = load_data()

# ------------------ SIDEBAR ------------------
st.sidebar.header("🌧 Flood Prediction Settings")
rainfall = st.sidebar.slider("Select Rainfall Level (mm)", 0, 300, 50)

if rainfall < 50:
    flood_buffer = flood_gdf.buffer(0.0004)
    rain_level = "Low Rainfall"
elif rainfall < 120:
    flood_buffer = flood_gdf.buffer(0.001)
    rain_level = "Moderate Rainfall"
else:
    flood_buffer = flood_gdf.buffer(0.002)
    rain_level = "Heavy Rainfall"

st.sidebar.success(f"Prediction Mode: {rain_level}")

# ------------------ CREATE RISK ZONES ------------------
high_risk   = flood_gdf.buffer(0.0005)
moderate_risk = flood_gdf.buffer(0.001)
low_risk    = flood_gdf.buffer(0.002)

high_union     = high_risk.union_all()
moderate_union = moderate_risk.union_all()
low_union      = low_risk.union_all()

# ------------------ CLASSIFY BUILDINGS ------------------
def classify_building(row):
    geom = row.geometry
    if geom.intersects(high_union):
        return "High Risk"
    elif geom.intersects(moderate_union):
        return "Moderate Risk"
    elif geom.intersects(low_union):
        return "Low Risk"
    else:
        return "Safe"

buildings_gdf["Risk"] = buildings_gdf.apply(classify_building, axis=1)

# ------------------ CREATE MAP ------------------
m = folium.Map(location=[30.3165, 78.0322], zoom_start=12, tiles="cartodb dark_matter")

# Flood Zone
folium.GeoJson(
    flood_buffer.__geo_interface__,
    name="Predicted Flood Zone",
    style_function=lambda x: {"color": "#0055ff", "weight": 2, "fillOpacity": 0.4},
).add_to(m)

# Risk Zones
folium.GeoJson(
    high_risk.__geo_interface__,
    name="High Risk Zone",
    style_function=lambda x: {"color": "#ff0000", "weight": 2, "fillOpacity": 0.3},
).add_to(m)

folium.GeoJson(
    moderate_risk.__geo_interface__,
    name="Moderate Risk Zone",
    style_function=lambda x: {"color": "#ffcc00", "weight": 2, "fillOpacity": 0.3},
).add_to(m)

folium.GeoJson(
    low_risk.__geo_interface__,
    name="Low Risk Zone",
    style_function=lambda x: {"color": "#ff8800", "weight": 2, "fillOpacity": 0.3},
).add_to(m)

# Buildings
color_map = {
    "High Risk": "red",
    "Moderate Risk": "yellow",
    "Low Risk": "orange",
    "Safe": "green",
}

for _, row in buildings_gdf.iterrows():
    color = color_map[row["Risk"]]
    folium.GeoJson(
        row["geometry"].__geo_interface__,
        style_function=lambda x, col=color: {
            "color": col, "weight": 1, "fillOpacity": 0.6
        },
        tooltip=f"Risk: {row['Risk']}",
    ).add_to(m)

folium.LayerControl().add_to(m)

# ------------------ DISPLAY MAP ------------------
st_folium(m, width=1200, height=650)

# ------------------ STATISTICS ------------------
st.subheader("📊 Flood Risk Statistics")

high     = len(buildings_gdf[buildings_gdf["Risk"] == "High Risk"])
moderate = len(buildings_gdf[buildings_gdf["Risk"] == "Moderate Risk"])
low      = len(buildings_gdf[buildings_gdf["Risk"] == "Low Risk"])
safe     = len(buildings_gdf[buildings_gdf["Risk"] == "Safe"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔴 High Risk Buildings",     high)
col2.metric("🟡 Moderate Risk Buildings", moderate)
col3.metric("🟠 Low Risk Buildings",      low)
col4.metric("🟢 Safe Buildings",          safe)

# ------------------ DESCRIPTION ------------------
st.markdown("---")
st.markdown("### Project Description")
st.write(
    "This application predicts flood risk zones based on rainfall levels and "
    "identifies buildings that are likely to be affected. The system uses real geospatial "
    "data and spatial analysis techniques to provide flood impact assessment for Uttarakhand."
)
