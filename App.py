import sys
import os
import io
import base64
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import streamlit.components.v1 as components
import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import Polygon, box, shape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import requests
import numpy as np
import tempfile
import pathlib
import struct
from PIL import Image

st.set_page_config(page_title="GeoFlood Uttarakhand",
                   page_icon="🌊", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
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
.sat-card    { border-top: 3px solid #f39c12 !important; }
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
.sat-banner {
    background: linear-gradient(90deg, #0f2027, #1a2a1a);
    border-radius: 10px; padding: 14px 18px; color: white;
    border-left: 4px solid #f39c12; margin-bottom: 16px;
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
.district-info-card {
    background: #111827; border-radius: 12px;
    padding: 20px; color: white;
    border: 1px solid #1f2937;
    height: 420px; overflow-y: auto; box-sizing: border-box;
}
.chart-panel {
    background: #111827; border-radius: 12px;
    padding: 16px 20px; border: 1px solid #1f2937;
    height: 420px; display: flex; flex-direction: column;
    justify-content: center; box-sizing: border-box;
}
.panel-title {
    font-size: 1rem; font-weight: 700; color: white;
    margin-bottom: 10px; padding-bottom: 8px;
    border-bottom: 2px solid #1a6bff; letter-spacing: 0.3px;
}
.info-row {
    display: flex; align-items: center;
    padding: 9px 0; border-bottom: 1px solid #1f2937; font-size: 0.88rem;
}
.info-row:last-child { border-bottom: none; }
.info-label { color: #94a3b8; width: 52%; }
.info-value { font-weight: 700; width: 48%; text-align: right; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🌊 GeoFlood — Uttarakhand</h1>
    <p>🛰️ Real-time Flood Detection · NDWI · SAR · Building Impact Assessment</p>
    <p style="font-size:0.8rem;opacity:0.55;margin-top:2px">
        📡 Sentinel-1 SAR · 🌿 Sentinel-2 NDWI · 🏞️ OSM Buildings · ⚠️ Risk Classification
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DISTRICT DATA
# ─────────────────────────────────────────────────────────────────────────────
UTTARAKHAND_LOCATIONS = {
    "Haridwar":    {"place":"Haridwar, Uttarakhand, India",    "center":[29.9457,78.1642],"zoom":15,"river":"Ganga",             "risk":"Extreme","description":"Ganga river flooding near Har Ki Pauri ghats",         "flood_bbox":[78.140,29.930,78.200,29.970]},
    "Rishikesh":   {"place":"Rishikesh, Uttarakhand, India",   "center":[30.0869,78.2676],"zoom":15,"river":"Ganga",             "risk":"High",   "description":"Ganga river overflow near Laxman Jhula",              "flood_bbox":[78.245,30.065,78.295,30.110]},
    "Dehradun":    {"place":"Dehradun, Uttarakhand, India",    "center":[30.3165,78.0322],"zoom":14,"river":"Rispana & Bindal",  "risk":"High",   "description":"Seasonal flooding in Rispana and Bindal river basins","flood_bbox":[78.000,30.295,78.080,30.345]},
    "Nainital":    {"place":"Nainital, Uttarakhand, India",    "center":[29.3919,79.4542],"zoom":15,"river":"Naini Lake",        "risk":"Moderate","description":"Lake overflow and landslide-induced flooding",       "flood_bbox":[79.435,29.380,79.475,29.410]},
    "Rudraprayag": {"place":"Rudraprayag, Uttarakhand, India", "center":[30.2847,78.9812],"zoom":15,"river":"Alaknanda/Mandakini","risk":"Extreme","description":"River confluence — Kedarnath disaster zone",          "flood_bbox":[78.965,30.270,78.998,30.300]},
    "Uttarkashi":  {"place":"Uttarkashi, Uttarakhand, India",  "center":[30.7268,78.4354],"zoom":15,"river":"Bhagirathi",        "risk":"High",   "description":"Bhagirathi river flooding in narrow valley",          "flood_bbox":[78.420,30.715,78.455,30.742]},
    "Chamoli":     {"place":"Chamoli, Uttarakhand, India",     "center":[30.3993,79.3253],"zoom":15,"river":"Alaknanda",         "risk":"Extreme","description":"Alaknanda — glacial outburst flood risk",            "flood_bbox":[79.308,30.385,79.345,30.415]},
    "Pithoragarh": {"place":"Pithoragarh, Uttarakhand, India", "center":[29.5830,80.2181],"zoom":15,"river":"Kali & Saryu",      "risk":"High",   "description":"Kali and Saryu river flooding in border region",      "flood_bbox":[80.200,29.568,80.235,29.598]},
    "Tehri":       {"place":"Tehri Garhwal, Uttarakhand, India","center":[30.3784,78.4800],"zoom":14,"river":"Bhilangana",       "risk":"Moderate","description":"Bhilangana river and Tehri dam downstream risk",    "flood_bbox":[78.462,30.362,78.500,30.395]},
    "Roorkee":     {"place":"Roorkee, Uttarakhand, India",     "center":[29.8543,77.8880],"zoom":15,"river":"Ganga Canal",       "risk":"Moderate","description":"Upper Ganga canal overflow during heavy rainfall",   "flood_bbox":[77.870,29.840,77.905,29.868]},
}

# ─────────────────────────────────────────────────────────────────────────────
# ██  SATELLITE TIFF PROCESSING  ██
# ─────────────────────────────────────────────────────────────────────────────

def read_tiff_raw(path):
    """
    Pure-Python BigTIFF reader.
    Returns: (band_arrays, geo_bounds, crs_wkt, metadata_dict)
    band_arrays  = list of 2D numpy float32 arrays, one per band
    geo_bounds   = [west, south, east, north] in degrees (or None)
    """
    with open(path, 'rb') as f:
        raw = f.read()

    endian = '<' if raw[:2] == b'II' else '>'
    magic  = struct.unpack(endian + 'H', raw[2:4])[0]
    is_big = magic == 43                      # BigTIFF

    if is_big:
        ifd_offset = struct.unpack(endian + 'Q', raw[8:16])[0]
    else:
        ifd_offset = struct.unpack(endian + 'I', raw[4:8])[0]

    # ── parse IFD tags ──────────────────────────────────────────────────────
    def read_val(offset, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(endian + fmt, raw[offset:offset+size])[0]

    def read_rational(offset):
        n = read_val(offset,   'I')
        d = read_val(offset+4, 'I')
        return n / d if d else 0.0

    tags = {}
    if is_big:
        n_tags = read_val(ifd_offset, 'Q')
        tag_start = ifd_offset + 8
        tag_size  = 20
    else:
        n_tags = read_val(ifd_offset, 'H')
        tag_start = ifd_offset + 2
        tag_size  = 12

    for i in range(n_tags):
        t_off = tag_start + i * tag_size
        tag   = read_val(t_off, 'H')
        dtype = read_val(t_off+2, 'H')
        if is_big:
            count  = read_val(t_off+4, 'Q')
            voff   = t_off + 12
        else:
            count  = read_val(t_off+4, 'I')
            voff   = t_off + 8
        tags[tag] = (dtype, count, voff)

    def tag_val(tag_id, default=None):
        if tag_id not in tags:
            return default
        dtype, count, voff = tags[tag_id]
        if dtype == 1:  fmt = 'B'
        elif dtype == 3: fmt = 'H'
        elif dtype == 4: fmt = 'I'
        elif dtype == 5:
            off = read_val(voff, 'I' if not is_big else 'Q')
            return read_rational(off)
        elif dtype == 11: fmt = 'f'
        elif dtype == 12: fmt = 'd'
        elif dtype == 16: fmt = 'Q'
        else:             fmt = 'I'
        return read_val(voff, fmt)

    width      = tag_val(256, 256)
    height     = tag_val(257, 256)
    bits       = tag_val(258, 8)
    n_bands    = tag_val(277, 1)
    sample_fmt = tag_val(339, 1)   # 1=uint, 2=int, 3=float

    # ── GeoTIFF ModelPixelScale & ModelTiepoint ─────────────────────────────
    geo_bounds = None
    # Tag 33550 = ModelPixelScaleTag, Tag 33922 = ModelTiepointTag
    scale_x = scale_y = None
    tie_x   = tie_y   = None

    if 33550 in tags:
        _, _, voff = tags[33550]
        ptr = read_val(voff, 'I' if not is_big else 'Q')
        scale_x = struct.unpack(endian+'d', raw[ptr:ptr+8])[0]
        scale_y = struct.unpack(endian+'d', raw[ptr+8:ptr+16])[0]

    if 33922 in tags:
        _, _, voff = tags[33922]
        ptr = read_val(voff, 'I' if not is_big else 'Q')
        # tiepoint: I J K X Y Z  (6 doubles)
        tie_x = struct.unpack(endian+'d', raw[ptr+24:ptr+32])[0]
        tie_y = struct.unpack(endian+'d', raw[ptr+32:ptr+40])[0]

    if scale_x and tie_x is not None:
        west  = tie_x
        north = tie_y
        east  = tie_x + scale_x * width
        south = tie_y - scale_y * height
        geo_bounds = [west, south, east, north]

    # ── Read pixel data ─────────────────────────────────────────────────────
    strip_offsets = []
    strip_counts  = []

    if 273 in tags:   # StripOffsets
        dtype, count, voff = tags[273]
        fmt = 'I' if dtype == 4 else ('Q' if dtype == 16 else 'H')
        if count == 1:
            strip_offsets = [read_val(voff, fmt)]
        else:
            ptr = read_val(voff, 'I' if not is_big else 'Q')
            strip_offsets = [
                struct.unpack(endian+fmt, raw[ptr+j*struct.calcsize(fmt):ptr+(j+1)*struct.calcsize(fmt)])[0]
                for j in range(count)
            ]

    if 279 in tags:   # StripByteCounts
        dtype, count, voff = tags[279]
        fmt = 'I' if dtype == 4 else ('Q' if dtype == 16 else 'H')
        if count == 1:
            strip_counts = [read_val(voff, fmt)]
        else:
            ptr = read_val(voff, 'I' if not is_big else 'Q')
            strip_counts = [
                struct.unpack(endian+fmt, raw[ptr+j*struct.calcsize(fmt):ptr+(j+1)*struct.calcsize(fmt)])[0]
                for j in range(count)
            ]

    # Assemble raw pixel bytes
    pixel_bytes = b''.join(
        raw[o:o+c] for o, c in zip(strip_offsets, strip_counts)
    ) if strip_offsets else b''

    # Determine numpy dtype
    if sample_fmt == 3:
        np_dtype = np.float32 if bits == 32 else np.float64
    elif sample_fmt == 2:
        np_dtype = np.int16 if bits == 16 else np.int32
    else:
        np_dtype = np.uint8 if bits == 8 else (np.uint16 if bits == 16 else np.uint32)

    bands = []
    if pixel_bytes:
        try:
            arr = np.frombuffer(pixel_bytes, dtype=np_dtype)
            total_pixels = width * height * n_bands
            if len(arr) >= total_pixels:
                arr = arr[:total_pixels]
                if n_bands > 1:
                    arr = arr.reshape(n_bands, height, width)
                    for b in range(n_bands):
                        bands.append(arr[b].astype(np.float32))
                else:
                    bands.append(arr.reshape(height, width).astype(np.float32))
        except Exception:
            pass

    meta = {
        "width": width, "height": height,
        "bands": n_bands, "bits": bits,
        "sample_fmt": {1:"uint",2:"int",3:"float"}.get(sample_fmt,"uint"),
    }
    return bands, geo_bounds, meta


def process_ndwi_tiff(bands, geo_bounds):
    """
    Process NDWI GeoTIFF (single band, values roughly -1 to +1).
    Returns water_mask (bool array) + colored RGBA base64 PNG.
    """
    if not bands:
        return None, None, {}

    ndwi = bands[0].copy()

    # Replace nodata
    ndwi[ndwi < -3] = np.nan
    ndwi[ndwi > 3]  = np.nan

    threshold = 0.2
    water_mask = ndwi > threshold

    stats = {
        "min":   float(np.nanmin(ndwi)),
        "max":   float(np.nanmax(ndwi)),
        "mean":  float(np.nanmean(ndwi)),
        "water_pixels": int(water_mask.sum()),
        "total_pixels": int(np.isfinite(ndwi).sum()),
        "water_pct":    round(water_mask.sum() / max(np.isfinite(ndwi).sum(),1) * 100, 2),
        "threshold": threshold,
        "mode": "NDWI (Sentinel-2)"
    }

    # Colorize: blue gradient for water, tan/brown for land
    h, w = ndwi.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Water pixels → blue
    rgba[water_mask, 0] = 30
    rgba[water_mask, 1] = 100
    rgba[water_mask, 2] = 220
    rgba[water_mask, 3] = 200

    # Non-water land → semi-transparent brown
    land = ~water_mask & np.isfinite(ndwi)
    rgba[land, 0] = 180
    rgba[land, 1] = 140
    rgba[land, 2] = 90
    rgba[land, 3] = 60

    img    = Image.fromarray(rgba, 'RGBA')
    buf    = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return water_mask, img_b64, stats


def process_watermask_tiff(bands, geo_bounds):
    """
    Process binary WaterMask GeoTIFF (0=land, 1=water).
    """
    if not bands:
        return None, None, {}

    mask = bands[0].copy()
    water_mask = mask > 0.5

    stats = {
        "water_pixels": int(water_mask.sum()),
        "total_pixels": int(mask.size),
        "water_pct":    round(water_mask.sum() / max(mask.size,1) * 100, 2),
        "mode": "Water Mask (Sentinel-2)"
    }

    h, w = mask.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[water_mask, 0] = 0
    rgba[water_mask, 1] = 150
    rgba[water_mask, 2] = 255
    rgba[water_mask, 3] = 210
    rgba[~water_mask, 3] = 0

    img    = Image.fromarray(rgba, 'RGBA')
    buf    = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return water_mask, img_b64, stats


def process_sar_tiff(bands, geo_bounds):
    """
    Process SAR Flood GeoTIFF (binary 0/1 or float backscatter).
    """
    if not bands:
        return None, None, {}

    sar = bands[0].copy()

    # If values look like dB (negatives), apply threshold
    if sar.min() < -1:
        water_mask = sar < -15    # -15 dB water threshold
        mode_str   = "SAR Backscatter (Sentinel-1 GRD)"
    else:
        water_mask = sar > 0.5   # binary mask
        mode_str   = "SAR Binary Flood Mask (Sentinel-1)"

    stats = {
        "min":   float(np.nanmin(sar)),
        "max":   float(np.nanmax(sar)),
        "water_pixels": int(water_mask.sum()),
        "total_pixels": int(sar.size),
        "water_pct":    round(water_mask.sum() / max(sar.size,1) * 100, 2),
        "mode": mode_str
    }

    h, w = sar.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[water_mask, 0] = 0
    rgba[water_mask, 1] = 200
    rgba[water_mask, 2] = 180
    rgba[water_mask, 3] = 220
    rgba[~water_mask, 3] = 0

    img    = Image.fromarray(rgba, 'RGBA')
    buf    = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return water_mask, img_b64, stats


def mask_to_flood_gdf(water_mask, geo_bounds):
    """Convert binary water_mask array → GeoDataFrame of flood polygons."""
    if water_mask is None or geo_bounds is None:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    west, south, east, north = geo_bounds
    h, w = water_mask.shape
    px_w = (east - west) / w
    px_h = (north - south) / h

    # Sample every Nth pixel to keep polygon count manageable
    step = max(1, min(h, w) // 60)
    polys = []

    for row in range(0, h, step):
        for col in range(0, w, step):
            if water_mask[row, col]:
                lon0 = west  + col * px_w
                lat0 = north - row * px_h
                lon1 = lon0  + px_w * step
                lat1 = lat0  - px_h * step
                polys.append(box(lon0, lat1, lon1, lat0))

    if not polys:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    return gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326")


def combine_flood_sources(osm_gdf, sat_gdfs):
    """
    Merge OSM flood zones with satellite-derived flood zones.
    sat_gdfs = list of GeoDataFrames from NDWI / WaterMask / SAR
    """
    all_frames = [osm_gdf] + [g for g in sat_gdfs if g is not None and len(g) > 0]
    if len(all_frames) == 1:
        return osm_gdf
    try:
        combined = gpd.GeoDataFrame(
            pd.concat(all_frames, ignore_index=True),
            crs="EPSG:4326"
        )
        return combined
    except Exception:
        return osm_gdf


# ─────────────────────────────────────────────────────────────────────────────
# OSM DATA FETCHERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_buildings(place_name, bbox):
    try:
        minx, miny, maxx, maxy = bbox
        query = (
            "[out:json][timeout:60];"
            "(way[\"building\"]"
            "(" + str(miny)+","+str(minx)+","+str(maxy)+","+str(maxx)+");"
            "relation[\"building\"]"
            "(" + str(miny)+","+str(minx)+","+str(maxy)+","+str(maxx)+"););"
            "out geom;"
        )
        r    = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=60)
        data = r.json()
        buildings = []
        for el in data.get("elements", []):
            if el.get("type") == "way":
                coords = [(n["lon"], n["lat"]) for n in el.get("geometry", [])]
                if len(coords) >= 3:
                    try:
                        p = Polygon(coords)
                        if p.is_valid:
                            buildings.append(p)
                    except Exception:
                        pass
        if buildings:
            return gpd.GeoDataFrame(geometry=buildings, crs="EPSG:4326")
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
            bx = minx + i*step_x + step_x*0.1
            by = miny + j*step_y + step_y*0.1
            buildings.append(box(bx, by, bx+step_x*0.7, by+step_y*0.7))
    return gpd.GeoDataFrame(geometry=buildings, crs="EPSG:4326")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_flood_zones(place_name, bbox, river_name):
    try:
        minx, miny, maxx, maxy = bbox
        query = (
            "[out:json][timeout:60];"
            "(way[\"waterway\"=\"river\"]"
            "(" + str(miny)+","+str(minx)+","+str(maxy)+","+str(maxx)+");"
            "way[\"waterway\"=\"stream\"]"
            "(" + str(miny)+","+str(minx)+","+str(maxy)+","+str(maxx)+");"
            "way[\"natural\"=\"water\"]"
            "(" + str(miny)+","+str(minx)+","+str(maxy)+","+str(maxx)+");"
            "relation[\"natural\"=\"water\"]"
            "(" + str(miny)+","+str(minx)+","+str(maxy)+","+str(maxx)+"););"
            "out geom;"
        )
        r    = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=60)
        data = r.json()
        water_polys = []
        for el in data.get("elements", []):
            if el.get("type") == "way":
                coords = [(n["lon"], n["lat"]) for n in el.get("geometry", [])]
                if len(coords) >= 3:
                    try:
                        p = Polygon(coords)
                        if p.is_valid and not p.is_empty:
                            water_polys.append(p.buffer(0.004))
                    except Exception:
                        pass
                elif len(coords) >= 2:
                    try:
                        from shapely.geometry import LineString
                        water_polys.append(LineString(coords).buffer(0.004))
                    except Exception:
                        pass
        if water_polys:
            return gpd.GeoDataFrame(geometry=water_polys, crs="EPSG:4326")
        return generate_fallback_flood(bbox)
    except Exception:
        return generate_fallback_flood(bbox)


def generate_fallback_flood(bbox):
    minx, miny, maxx, maxy = bbox
    cx = (minx + maxx) / 2
    flood_poly = Polygon([
        (cx-0.006, miny+0.002),(cx+0.006, miny+0.002),
        (cx+0.009, maxy-0.002),(cx-0.009, maxy-0.002),
    ])
    return gpd.GeoDataFrame(geometry=[flood_poly], crs="EPSG:4326")


def find_flooded_buildings(buildings_gdf, flood_gdf):
    try:
        if buildings_gdf.crs != flood_gdf.crs:
            flood_gdf = flood_gdf.to_crs(buildings_gdf.crs)
        flooded = gpd.sjoin(buildings_gdf, flood_gdf, how="inner", predicate="intersects")
        flooded = flooded[~flooded.index.duplicated(keep="first")]
        return flooded.reset_index(drop=True)
    except Exception:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


def get_risk_level(building_geom, flood_gdf):
    try:
        total_area = building_geom.area
        if total_area == 0:
            return "low"
        inter = sum(
            building_geom.intersection(r.geometry).area
            for _, r in flood_gdf.iterrows()
            if building_geom.intersects(r.geometry)
        )
        pct = (inter / total_area) * 100
        if pct >= 70:   return "high"
        elif pct >= 30: return "moderate"
        elif pct > 0:   return "low"
        return "none"
    except Exception:
        return "low"


# ─────────────────────────────────────────────────────────────────────────────
# RAINFALL
# ─────────────────────────────────────────────────────────────────────────────
DISTRICT_COORDS = {
    "Haridwar":(29.9457,78.1642),"Rishikesh":(30.0869,78.2676),
    "Dehradun":(30.3165,78.0322),"Nainital":(29.3919,79.4542),
    "Rudraprayag":(30.2847,78.9812),"Uttarkashi":(30.7268,78.4354),
    "Chamoli":(30.3993,79.3253),"Pithoragarh":(29.5830,80.2181),
    "Tehri":(30.3784,78.4800),"Roorkee":(29.8543,77.8880),
}

def get_live_rainfall(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "precipitation_sum,rain_sum",
            "timezone": "Asia/Kolkata", "forecast_days": 7
        }
        r    = requests.get(url, params=params, timeout=10)
        data = r.json()
        daily  = data.get("daily", {})
        precip = daily.get("precipitation_sum", [])
        dates  = daily.get("time", [])
        today  = precip[0] if precip else 0.0
        total7 = sum(p for p in precip if p is not None)
        peak_i = precip.index(max(precip)) if precip else 0
        return {
            "today_mm":    round(today or 0, 1),
            "total_7day":  round(total7, 1),
            "peak_day":    dates[peak_i] if dates else "N/A",
            "peak_mm":     round(precip[peak_i] or 0, 1) if precip else 0,
            "daily_dates": dates,
            "daily_rain":  precip,
        }
    except Exception:
        return None


def analyse_rainfall(mm):
    if mm == 0:   return None
    if mm < 25:   return {"risk":"Low",     "color":"#2ecc71","emoji":"🟢","advice":"🌦️ Light rainfall. Minimal flood risk.",         "expected":"<5%"}
    if mm < 65:   return {"risk":"Moderate","color":"#f39c12","emoji":"🟡","advice":"🌧️ Some areas may waterlog.",                    "expected":"5–20%"}
    if mm < 115:  return {"risk":"High",    "color":"#e74c3c","emoji":"🔴","advice":"⛈️ Heavy rainfall! Significant flood risk.",     "expected":"20–50%"}
    return             {"risk":"Extreme", "color":"#c0392b","emoji":"🆘","advice":"🚨 Extreme rainfall! Immediate evacuation needed.","expected":">50%"}


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def impact_chart(total, flooded):
    safe = total - flooded
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    fig.patch.set_facecolor("white")
    ax1.pie([flooded, safe], colors=["#E24B4A","#9FE1CB"], startangle=90,
            wedgeprops={"width":0.5,"edgecolor":"white","linewidth":2})
    ax1.set_title("🏠 Building Impact", fontsize=13, fontweight="bold", pad=15)
    ax1.legend(handles=[
        mpatches.Patch(color="#E24B4A", label=f"🔴 Flooded ({flooded})"),
        mpatches.Patch(color="#9FE1CB", label=f"🟢 Safe ({safe})")
    ], loc="lower center", bbox_to_anchor=(0.5,-0.15), ncol=2, fontsize=10)
    bars = ax2.bar(["Total","Flooded","Safe"],[total,flooded,safe],
                   color=["#3B8BD4","#E24B4A","#1D9E75"],edgecolor="white",linewidth=1.5,width=0.5)
    for bar, val in zip(bars,[total,flooded,safe]):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val),
                 ha="center",va="bottom",fontsize=11,fontweight="bold")
    ax2.set_title("📊 Building Count", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Number of buildings")
    ax2.spines[["top","right"]].set_visible(False)
    ax2.set_ylim(0, max(total*1.2, 10))
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MAP BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def create_map(flood_gdf, buildings_gdf, flooded_gdf, loc_key, sat_layers=None):
    loc = UTTARAKHAND_LOCATIONS[loc_key]
    m   = folium.Map(
        location=loc["center"], zoom_start=loc["zoom"],
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery"
    )
    folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Terrain Map"
    ).add_to(m)

    # ── Satellite overlays ────────────────────────────────────────────────────
    if sat_layers:
        for lyr in sat_layers:
            if lyr and lyr.get("img_b64") and lyr.get("bounds"):
                west, south, east, north = lyr["bounds"]
                folium.raster_layers.ImageOverlay(
                    image  = "data:image/png;base64," + lyr["img_b64"],
                    bounds = [[south, west], [north, east]],
                    opacity= 0.70,
                    name   = lyr["label"],
                    show   = lyr.get("show", True),
                    interactive=False
                ).add_to(m)

    # ── OSM Flood zone ────────────────────────────────────────────────────────
    fl = folium.FeatureGroup(name="OSM Flood Zone", show=True)
    for _, row in flood_gdf.iterrows():
        folium.GeoJson(row.geometry.__geo_interface__,
            style_function=lambda x: {"fillColor":"#0055ff","color":"#0033aa","weight":2.5,"fillOpacity":0.35},
            tooltip="Flood Zone — " + loc["river"]
        ).add_to(fl)
    fl.add_to(m)

    # ── Risk zones ────────────────────────────────────────────────────────────
    for buf, color, border, name, opacity in [
        (-0.0002, "#ff0000","#cc0000","High Risk Core",0.4),
        ( 0.0008, "#ffcc00","#cc9900","Moderate Risk",0.25),
        ( 0.0016, "#ff8800","#cc6600","Low Risk Zone",0.15),
    ]:
        zone = folium.FeatureGroup(name=name, show=True)
        for _, row in flood_gdf.iterrows():
            try:
                if buf < 0:
                    geom = row.geometry.buffer(buf)
                elif name == "Moderate Risk":
                    geom = row.geometry.buffer(0.0008).difference(row.geometry)
                else:
                    geom = row.geometry.buffer(0.0016).difference(row.geometry.buffer(0.0008))
                if not geom.is_empty:
                    folium.GeoJson(geom.__geo_interface__,
                        style_function=lambda x,c=color,b=border,o=opacity: {
                            "fillColor":c,"color":b,"weight":1.5,"fillOpacity":o},
                        tooltip=name
                    ).add_to(zone)
            except Exception:
                pass
        zone.add_to(m)

    # ── Safe buildings ────────────────────────────────────────────────────────
    flooded_idx = set(flooded_gdf.index.tolist())
    safe_layer  = folium.FeatureGroup(name="Safe Buildings", show=True)
    for idx, row in buildings_gdf.iterrows():
        if idx not in flooded_idx:
            c = row.geometry.centroid
            folium.GeoJson(row.geometry.__geo_interface__,
                style_function=lambda x: {"fillColor":"#00dd77","color":"#009944","weight":1.5,"fillOpacity":0.7},
                tooltip="✅ Safe Building",
                popup=folium.Popup(
                    f"<div style='font-family:Arial;width:180px'><b style='color:green'>✅ Safe Building</b>"
                    f"<hr>Lat:{round(c.y,5)}<br>Lon:{round(c.x,5)}</div>", max_width=200)
            ).add_to(safe_layer)
    safe_layer.add_to(m)

    # ── Flooded buildings ─────────────────────────────────────────────────────
    high_bld = folium.FeatureGroup(name="High Risk Buildings",     show=True)
    mod_bld  = folium.FeatureGroup(name="Moderate Risk Buildings", show=True)
    low_bld  = folium.FeatureGroup(name="Low Risk Buildings",      show=True)

    for i, (_, row) in enumerate(flooded_gdf.iterrows()):
        c    = row.geometry.centroid
        risk = get_risk_level(row.geometry, flood_gdf)
        cfg  = {
            "high":     ("#ff2222","#aa0000","🔴 HIGH RISK",    "red",       high_bld,"🚨 Evacuate now"),
            "moderate": ("#ffbb00","#cc8800","🟡 MODERATE RISK","orange",     mod_bld, "⚠️ Monitor closely"),
            "low":      ("#ff7700","#cc5500","🟠 LOW RISK",     "darkorange", low_bld, "👁️ Stay alert"),
        }.get(risk, ("#ff7700","#cc5500","🟠 LOW RISK","darkorange",low_bld,"👁️ Stay alert"))
        fill,border,label,color,target,action = cfg

        popup_html = (
            f"<div style='font-family:Arial;width:210px;padding:6px'>"
            f"<h4 style='color:{color};margin:0 0 6px'>{label}</h4><hr style='margin:4px 0'>"
            f"<b>🏢 Building:</b> #{i+1}<br><b>📍 District:</b> {loc_key}<br>"
            f"<b>🌊 River:</b> {loc['river']}<br>"
            f"<b>⚠️ Risk:</b> <span style='color:{color};font-weight:700'>{risk.upper()}</span><br>"
            f"<b>📍 Lat:</b> {round(c.y,5)}<br><b>📍 Lon:</b> {round(c.x,5)}<br>"
            f"<hr style='margin:4px 0'><b>📋 Action:</b> {action}</div>"
        )
        popup = folium.Popup(popup_html, max_width=230)
        folium.GeoJson(row.geometry.__geo_interface__,
            style_function=lambda x,f=fill,b=border: {"fillColor":f,"color":b,"weight":2.5,"fillOpacity":0.85},
            tooltip=f"{label} — Building #{i+1}", popup=popup
        ).add_to(target)
        folium.CircleMarker(
            location=[c.y,c.x], radius=6, color=border,
            fill=True, fill_color=fill, fill_opacity=0.95,
            tooltip=f"{label} #{i+1}", popup=popup
        ).add_to(target)

    high_bld.add_to(m); mod_bld.add_to(m); low_bld.add_to(m)

    # ── Flow arrows ───────────────────────────────────────────────────────────
    flow_layer = folium.FeatureGroup(name="Water Flow Direction", show=True)
    bounds = flood_gdf.total_bounds
    minx,miny,maxx,maxy = bounds
    sx=(maxx-minx)/4; sy=(maxy-miny)/3
    for i in range(4):
        for j in range(3):
            lat1=miny+(j+0.8)*sy; lon1=minx+(i+0.5)*sx
            lat2=lat1-sy*0.45;     lon2=lon1+sx*0.1
            folium.PolyLine([[lat1,lon1],[lat2,lon2]],color="#00eeff",weight=3,opacity=0.9).add_to(flow_layer)
            folium.Marker([lat2,lon2],icon=folium.DivIcon(
                html="<div style='font-size:14px;color:#00eeff;font-weight:bold'>v</div>",
                icon_size=(14,14),icon_anchor=(7,7))).add_to(flow_layer)
    flow_layer.add_to(m)

    # ── Legend ────────────────────────────────────────────────────────────────
    sat_legend = ""
    if sat_layers:
        sat_legend = "<hr style='margin:7px 0;border-color:#2a2a4a'><b style='font-size:11px;color:#f39c12;letter-spacing:1px'>🛰️ SATELLITE</b><br>"
        for lyr in sat_layers:
            if lyr:
                sat_legend += f"<span style='color:{lyr['color']};font-size:13px'>&#9632;</span> {lyr['label']}<br>"

    legend_html = f"""
    <div id="lc" style="position:fixed;bottom:40px;right:10px;z-index:9999;font-family:Arial;font-size:12px">
        <button onclick="tgl()" style="background:rgba(10,15,30,.95);color:white;border:1px solid #3a3a5a;
        border-radius:8px 8px 0 0;padding:6px 14px;cursor:pointer;font-size:12px;font-weight:700;width:100%;text-align:left">
        🗺️ Map Legend  &#9660;</button>
        <div id="lb" style="background:rgba(5,10,20,.96);border-radius:0 0 10px 10px;padding:12px 16px;
        color:white;border:1px solid #2a2a3a;border-top:none;min-width:200px">
        <b style="font-size:11px;color:#8ab4f8;letter-spacing:1px">🗂️ ZONES</b><br>
        <span style="color:#3366ff;font-size:15px">&#9646;</span> 🌊 Flood Zone<br>
        <span style="color:#ff2222;font-size:15px">&#9646;</span> 🔴 High Risk Core<br>
        <span style="color:#ffcc00;font-size:15px">&#9646;</span> 🟡 Moderate Risk<br>
        <span style="color:#ff8800;font-size:15px">&#9646;</span> 🟠 Low Risk Zone<br>
        {sat_legend}
        <hr style="margin:7px 0;border-color:#2a2a4a">
        <b style="font-size:11px;color:#8ab4f8;letter-spacing:1px">🏢 BUILDINGS</b><br>
        <span style="color:#ff2222;font-size:13px">&#9679;</span> 🔴 High Risk<br>
        <span style="color:#ffbb00;font-size:13px">&#9679;</span> 🟡 Moderate Risk<br>
        <span style="color:#ff7700;font-size:13px">&#9679;</span> 🟠 Low Risk<br>
        <span style="color:#00dd77;font-size:13px">&#9632;</span> ✅ Safe Building<br>
        <hr style="margin:7px 0;border-color:#2a2a4a">
        <small style="color:#888">🖱️ Click buildings for details</small>
        </div>
    </div>
    <script>
    function tgl(){{var b=document.getElementById("lb"),btn=document.querySelector("#lc button");
    if(b.style.display==="none"){{b.style.display="block";btn.innerHTML="🗺️ Map Legend  &#9660;"}}
    else{{b.style.display="none";btn.innerHTML="🗺️ Map Legend  &#9650;"}}}}
    </script>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(toggle_display=True,position="bottomleft",width=120,height=120,zoom_level_offset=-5).add_to(m)
    plugins.MousePosition(position="bottomright",prefix="📍 Coordinates: ").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
for key in ["done","sat_layers","rain_data","ndwi_stats","sar_stats","wm_stats"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "done" else False
if "sat_layers" not in st.session_state or st.session_state.sat_layers is None:
    st.session_state.sat_layers = []

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd

with st.sidebar:
    st.markdown("## 🗺️ Uttarakhand Districts")
    st.markdown("---")
    selected = st.selectbox("📍 Select District",
                            options=list(UTTARAKHAND_LOCATIONS.keys()), index=2)
    loc = UTTARAKHAND_LOCATIONS[selected]
    risk_colors = {"Extreme":"#ff2222","High":"#ffaa00","Moderate":"#ffcc00","Low":"#00cc66"}
    risk_emojis = {"Extreme":"🆘","High":"🔴","Moderate":"🟡","Low":"🟢"}
    rc = risk_colors.get(loc["risk"],"#fff")
    re = risk_emojis.get(loc["risk"],"⚠️")
    st.markdown(
        f"<div class='loc-card'><b>📍 {selected}</b><br>"
        f"<small style='opacity:0.7'>{loc['description']}</small><br><br>"
        f"<b>🌊 River:</b> {loc['river']}<br>"
        f"<b>⚠️ Risk:</b> <span style='color:{rc};font-weight:700'>{re} {loc['risk']}</span></div>",
        unsafe_allow_html=True)

    st.markdown("---")

    # ── 🛰️ Satellite Data Upload ──────────────────────────────────────────────
    st.markdown("### 🛰️ Satellite Data")
    st.caption("Upload your downloaded GeoTIFF files")

    ndwi_file = st.file_uploader("🌿 NDWI GeoTIFF",    type=["tif","tiff"], key="ndwi_up")
    wm_file   = st.file_uploader("💧 Water Mask GeoTIFF", type=["tif","tiff"], key="wm_up")
    sar_file  = st.file_uploader("📡 SAR Flood GeoTIFF", type=["tif","tiff"], key="sar_up")

    # Pre-load default files if they exist
    use_defaults = st.checkbox("Use pre-loaded Dehradun TIFFs", value=True,
                               help="Uses Dehradun_NDWI.tif, Dehradun_WaterMask.tif, Dehradun_SAR_Flood.tif from data/ folder")

    process_sat_btn = st.button("⚡ Process Satellite Data", use_container_width=True)

    if process_sat_btn:
        sat_layers = []
        st.session_state.ndwi_stats = None
        st.session_state.sar_stats  = None
        st.session_state.wm_stats   = None

        DEFAULT_PATHS = {
            "ndwi": "data/Dehradun_NDWI.tif",
            "wm":   "data/Dehradun_WaterMask.tif",
            "sar":  "data/Dehradun_SAR_Flood.tif",
        }

        def load_tiff(uploaded, default_path):
            if uploaded is not None:
                data = uploaded.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp:
                    tmp.write(data); return tmp.name
            if use_defaults and os.path.exists(default_path):
                return default_path
            return None

        # ── NDWI ──────────────────────────────────────────────────────────────
        ndwi_path = load_tiff(ndwi_file, DEFAULT_PATHS["ndwi"])
        if ndwi_path:
            with st.spinner("🌿 Processing NDWI..."):
                try:
                    bands, bounds, meta = read_tiff_raw(ndwi_path)
                    if bounds is None:
                        bounds = UTTARAKHAND_LOCATIONS["Dehradun"]["flood_bbox"]
                        bounds = [bounds[0], bounds[1], bounds[2], bounds[3]]
                    water_mask, img_b64, stats = process_ndwi_tiff(bands, bounds)
                    if img_b64:
                        flood_gdf_ndwi = mask_to_flood_gdf(water_mask, bounds)
                        sat_layers.append({
                            "label":     "🌿 NDWI Water Layer",
                            "img_b64":   img_b64,
                            "bounds":    bounds,
                            "flood_gdf": flood_gdf_ndwi,
                            "color":     "#3498db",
                            "show":      True,
                        })
                        st.session_state.ndwi_stats = stats
                        st.success(f"✅ NDWI — {stats['water_pct']}% water detected")
                except Exception as e:
                    st.warning(f"NDWI error: {e}")

        # ── Water Mask ────────────────────────────────────────────────────────
        wm_path = load_tiff(wm_file, DEFAULT_PATHS["wm"])
        if wm_path:
            with st.spinner("💧 Processing Water Mask..."):
                try:
                    bands, bounds, meta = read_tiff_raw(wm_path)
                    if bounds is None:
                        bounds = list(UTTARAKHAND_LOCATIONS["Dehradun"]["flood_bbox"])
                    water_mask, img_b64, stats = process_watermask_tiff(bands, bounds)
                    if img_b64:
                        flood_gdf_wm = mask_to_flood_gdf(water_mask, bounds)
                        sat_layers.append({
                            "label":     "💧 Water Mask Layer",
                            "img_b64":   img_b64,
                            "bounds":    bounds,
                            "flood_gdf": flood_gdf_wm,
                            "color":     "#1abc9c",
                            "show":      True,
                        })
                        st.session_state.wm_stats = stats
                        st.success(f"✅ Water Mask — {stats['water_pct']}% water")
                except Exception as e:
                    st.warning(f"Water Mask error: {e}")

        # ── SAR ───────────────────────────────────────────────────────────────
        sar_path = load_tiff(sar_file, DEFAULT_PATHS["sar"])
        if sar_path:
            with st.spinner("📡 Processing SAR Flood..."):
                try:
                    bands, bounds, meta = read_tiff_raw(sar_path)
                    if bounds is None:
                        bounds = list(UTTARAKHAND_LOCATIONS["Dehradun"]["flood_bbox"])
                    water_mask, img_b64, stats = process_sar_tiff(bands, bounds)
                    if img_b64:
                        flood_gdf_sar = mask_to_flood_gdf(water_mask, bounds)
                        sat_layers.append({
                            "label":     "📡 SAR Flood Layer",
                            "img_b64":   img_b64,
                            "bounds":    bounds,
                            "flood_gdf": flood_gdf_sar,
                            "color":     "#00d2ff",
                            "show":      True,
                        })
                        st.session_state.sar_stats = stats
                        st.success(f"✅ SAR — {stats['water_pct']}% flood area")
                except Exception as e:
                    st.warning(f"SAR error: {e}")

        st.session_state.sat_layers = sat_layers
        if sat_layers:
            st.success(f"🛰️ {len(sat_layers)} satellite layer(s) ready!")
        else:
            st.warning("No satellite layers processed. Check files.")

    # Show current satellite status
    if st.session_state.sat_layers:
        st.markdown(f"**🛰️ Active layers: {len(st.session_state.sat_layers)}**")
        for lyr in st.session_state.sat_layers:
            st.markdown(f"- {lyr['label']}")

    st.markdown("---")

    # ── Rainfall ──────────────────────────────────────────────────────────────
    st.markdown("### 🌧️ Rainfall")
    use_live = st.checkbox("📡 Fetch live rainfall (Open-Meteo)", value=True)
    if use_live:
        if st.button("☔ Get Live Rainfall", use_container_width=True):
            lat, lon = DISTRICT_COORDS.get(selected, (30.3165, 78.0322))
            with st.spinner("Fetching rainfall data..."):
                rd = get_live_rainfall(lat, lon)
            st.session_state.rain_data = rd
            if rd:
                st.metric("Today", f"{rd['today_mm']} mm")
                st.metric("7-Day Total", f"{rd['total_7day']} mm")
    else:
        rainfall_mm = st.number_input("💧 Manual rainfall (mm)", 0.0, 1000.0, 0.0, 10.0)
        st.session_state.rain_data = {"today_mm": rainfall_mm, "manual": True}

    st.markdown("---")
    with st.expander("⚙️ Detection Settings"):
        ndwi_threshold = st.slider("NDWI Threshold", 0.0, 1.0, 0.2, 0.05)
        use_sat_flood  = st.checkbox("Merge satellite flood zones", value=True,
                                     help="Combine satellite water detection with OSM flood zones")

    st.markdown("---")
    run_btn = st.button("🚀 Run Full Analysis", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown(
        "<div style='color:gray;font-size:0.72rem;text-align:center'>"
        "🌊 GeoFlood v2.0 — Uttarakhand<br>👥 Dinesh · Likhitha · Gayatri<br>"
        "<small>📡 Sentinel-1 · Sentinel-2 · OSM</small></div>",
        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SATELLITE STATS PANEL (always visible after processing)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.sat_layers:
    st.markdown(
        "<div class='sat-banner'>"
        "🛰️ <b>Satellite Data Active</b> — "
        + str(len(st.session_state.sat_layers)) + " layer(s) loaded and overlaid on map"
        "</div>", unsafe_allow_html=True)

    cols = st.columns(len(st.session_state.sat_layers))
    for col, lyr in zip(cols, st.session_state.sat_layers):
        with col:
            stats = {}
            if "NDWI" in lyr["label"] and st.session_state.ndwi_stats:
                stats = st.session_state.ndwi_stats
            elif "Water" in lyr["label"] and st.session_state.wm_stats:
                stats = st.session_state.wm_stats
            elif "SAR" in lyr["label"] and st.session_state.sar_stats:
                stats = st.session_state.sar_stats

            st.markdown(
                f"<div class='metric-card sat-card'>"
                f"<div class='label'>{lyr['label']}</div>"
                f"<div class='value'>{stats.get('water_pct', '—')}%</div>"
                f"<div class='sub'>💧 {stats.get('water_pixels','—')} water pixels</div>"
                f"<div class='sub' style='color:#aaa'>{stats.get('mode','')}</div>"
                f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RAINFALL PANEL
# ─────────────────────────────────────────────────────────────────────────────
rd = st.session_state.rain_data
if rd and rd.get("today_mm", 0) > 0:
    r = analyse_rainfall(rd["today_mm"])
    if r:
        st.markdown(
            "<div class='section-box'><div class='section-title'>🌧️ Rainfall Risk Assessment</div></div>",
            unsafe_allow_html=True)
        rc1, rc2, rc3 = st.columns(3)
        rc1.markdown(f"<div class='metric-card rain-card'><div class='label'>💧 Today</div><div class='value'>{rd['today_mm']}mm</div></div>", unsafe_allow_html=True)
        rc2.markdown(f"<div class='metric-card rain-card'><div class='label'>📅 7-Day</div><div class='value'>{rd.get('total_7day','—')}mm</div></div>", unsafe_allow_html=True)
        rc3.markdown(f"<div class='metric-card rain-card'><div class='label'>⚠️ Risk</div><div class='value'>{r['emoji']}</div><div class='sub' style='color:{r['color']}'>{r['risk']}</div></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='rain-result'><b>Advisory:</b> {r['advice']} | "
            f"<b>Expected affected:</b> {r['expected']}</div>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
if run_btn:
    loc  = UTTARAKHAND_LOCATIONS[selected]
    bbox = loc["flood_bbox"]

    with st.spinner("🌊 Fetching OSM flood zones..."):
        osm_flood_gdf = fetch_real_flood_zones(loc["place"], bbox, loc["river"])

    # Merge satellite flood zones if available
    if use_sat_flood and st.session_state.sat_layers:
        sat_gdfs = [lyr.get("flood_gdf") for lyr in st.session_state.sat_layers]
        all_frames = [osm_flood_gdf] + [g for g in sat_gdfs if g is not None and len(g) > 0]
        try:
            flood_gdf = gpd.GeoDataFrame(
                pd.concat(all_frames, ignore_index=True), crs="EPSG:4326")
        except Exception:
            flood_gdf = osm_flood_gdf
        st.info(f"🛰️ Merged OSM + {len(st.session_state.sat_layers)} satellite flood layer(s)")
    else:
        flood_gdf = osm_flood_gdf

    with st.spinner("🏢 Fetching buildings from OpenStreetMap..."):
        buildings_gdf = fetch_real_buildings(loc["place"], bbox)

    with st.spinner("🔍 Running spatial intersection analysis..."):
        flooded_gdf = find_flooded_buildings(buildings_gdf, flood_gdf)

    with st.spinner("🗺️ Building interactive map..."):
        map_obj = create_map(
            flood_gdf, buildings_gdf, flooded_gdf, selected,
            sat_layers=st.session_state.sat_layers
        )
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name
        map_obj.save(tmp_path)
        map_html = pathlib.Path(tmp_path).read_text(encoding="utf-8")

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
    st.session_state.used_sat = bool(st.session_state.sat_layers) and use_sat_flood

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.done:
    total   = st.session_state.total
    flooded = st.session_state.flooded
    pct     = st.session_state.pct
    safe    = st.session_state.safe

    # Metrics
    st.markdown("<div class='section-box'><div class='section-title'>📊 Impact Metrics</div></div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"<div class='metric-card total-card'><div class='label'>🏢 Total Buildings</div><div class='value'>{total}</div><div class='sub'>Found in area</div></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card flood-card'><div class='label'>🌊 Flooded Buildings</div><div class='value'>{flooded}</div><div class='sub' style='color:#e74c3c'>🔴 {pct}% affected</div></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card safe-card'><div class='label'>✅ Safe Buildings</div><div class='value'>{safe}</div><div class='sub' style='color:#2ecc71'>🟢 {100-pct}% safe</div></div>", unsafe_allow_html=True)

    # Data source badge
    src_txt = "🛰️ OSM + Sentinel SAR + NDWI" if st.session_state.get("used_sat") else "📡 OSM Flood Zones"
    st.markdown(f"<div style='text-align:center;margin:10px 0;font-size:0.8rem;color:#8ab4f8'>Data Source: {src_txt}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Risk classification
    st.markdown(
        "<div class='section-box'><div class='section-title'>🎯 Risk Classification</div>"
        "<div style='color:#ccc;font-size:0.88rem;line-height:2'>"
        "<span class='risk-badge badge-high'>🔴 High Risk</span> Over 70% inside flood zone — 🚨 Evacuate now<br>"
        "<span class='risk-badge badge-moderate'>🟡 Moderate Risk</span> 30–70% inside flood zone — ⚠️ Monitor<br>"
        "<span class='risk-badge badge-low'>🟠 Low Risk</span> Under 30% inside flood zone — 👁️ Stay alert<br>"
        "<span class='risk-badge badge-safe'>✅ Safe</span> Outside flood zone — No immediate action"
        "</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Map
    st.markdown("<div class='section-title' style='color:white;font-size:1rem;font-weight:700'>🗺️ Interactive Flood Map</div>", unsafe_allow_html=True)
    components.html(st.session_state.map_html, height=560, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart + Info
    chart_col, info_col = st.columns(2)
    with chart_col:
        fig = impact_chart(total, flooded)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white", dpi=110)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        st.markdown(
            f"<div class='chart-panel'><div class='panel-title'>📊 Impact Summary</div>"
            f"<img src='data:image/png;base64,{img_b64}' style='width:100%;border-radius:8px;object-fit:contain'></div>",
            unsafe_allow_html=True)

    with info_col:
        loc_risk = UTTARAKHAND_LOCATIONS[st.session_state.place]["risk"]
        rcol = risk_colors.get(loc_risk,"#fff")
        remo = risk_emojis.get(loc_risk,"⚠️")
        sat_info = ""
        if st.session_state.sat_layers:
            sat_info = (
                f"<div class='info-row'><span class='info-label'>🛰️ Satellite Layers</span>"
                f"<span class='info-value' style='color:#f39c12'>{len(st.session_state.sat_layers)} active</span></div>"
            )
            if st.session_state.ndwi_stats:
                sat_info += (f"<div class='info-row'><span class='info-label'>🌿 NDWI Water</span>"
                             f"<span class='info-value' style='color:#3498db'>{st.session_state.ndwi_stats['water_pct']}%</span></div>")
            if st.session_state.sar_stats:
                sat_info += (f"<div class='info-row'><span class='info-label'>📡 SAR Flood Area</span>"
                             f"<span class='info-value' style='color:#00d2ff'>{st.session_state.sar_stats['water_pct']}%</span></div>")

        st.markdown(
            f"<div class='district-info-card'>"
            f"<div class='panel-title'>📋 District Information</div>"
            f"<div style='background:linear-gradient(90deg,#0f2027,#1a2a3a);border-radius:8px;padding:10px 14px;margin-bottom:14px;border-left:3px solid #1a6bff'>"
            f"<span style='font-size:1.05rem;font-weight:700;color:white'>📍 {st.session_state.place}</span></div>"
            f"<div class='info-row'><span class='info-label'>🌊 River</span><span class='info-value' style='color:#8ab4f8'>{st.session_state.river}</span></div>"
            f"<div class='info-row'><span class='info-label'>⚠️ Flood Risk</span><span class='info-value' style='color:{rcol}'>{remo} {loc_risk}</span></div>"
            f"<div class='info-row'><span class='info-label'>🏢 Total Buildings</span><span class='info-value' style='color:#3498db'>{total}</span></div>"
            f"<div class='info-row'><span class='info-label'>🌊 Flooded</span><span class='info-value' style='color:#e74c3c'>{flooded} ({pct}%)</span></div>"
            f"<div class='info-row'><span class='info-label'>✅ Safe</span><span class='info-value' style='color:#2ecc71'>{safe} ({100-pct}%)</span></div>"
            f"{sat_info}"
            f"<div style='margin-top:16px;padding-top:12px;border-top:1px solid #1f2937'>"
            f"<p style='font-size:0.76rem;font-weight:800;color:#60a5fa;margin:0 0 7px;letter-spacing:1px'>📡 DATA SOURCES</p>"
            f"<p style='font-size:0.76rem;color:#64748b;margin:3px 0'>🌍 OpenStreetMap (buildings)</p>"
            f"<p style='font-size:0.76rem;color:#64748b;margin:3px 0'>🛰️ Sentinel-1 SAR (flood mask)</p>"
            f"<p style='font-size:0.76rem;color:#64748b;margin:3px 0'>🌿 Sentinel-2 NDWI (water index)</p>"
            f"<p style='font-size:0.76rem;color:#64748b;margin:3px 0'>🌧️ Open-Meteo (rainfall)</p>"
            f"</div></div>",
            unsafe_allow_html=True)

    # Bottom banner
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='info-banner'>✅ Analysis complete — <b>{st.session_state.place}</b> | "
        f"🌊 River: {st.session_state.river} | 🏢 {total} buildings | "
        f"🔴 {flooded} flooded ({pct}%) | 🟢 {safe} safe ({100-pct}%)<br>"
        f"<small style='opacity:0.7'>📡 Sources: OSM · Sentinel-1 SAR · Sentinel-2 NDWI · Open-Meteo</small>"
        f"</div>", unsafe_allow_html=True)
