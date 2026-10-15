#!/usr/bin/env python3
"""
Fetch central-Bristol buildings + roads from OpenStreetMap (Overpass API)
and generate synthetic smart-city nodes for the UrbanGraph prototype viewer.

Usage:
    pip install requests
    python fetch_bristol.py          # writes bristol_data.json

Then serve the folder and open the viewer:
    python -m http.server 8000
    ->  http://localhost:8000/index.html
"""
import json, math, random, sys

try:
    import requests
except ImportError:
    sys.exit("pip install requests first")

# --- Area: Bristol city centre / Harbourside ---------------------------------
LAT_MIN, LAT_MAX = 51.4487, 51.4568
LON_MIN, LON_MAX = -2.6055, -2.5880
LAT0 = (LAT_MIN + LAT_MAX) / 2
LON0 = (LON_MIN + LON_MAX) / 2
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))

def xy(lat, lon):
    return [round((lon - LON0) * M_PER_DEG_LON, 2),
            round((lat - LAT0) * M_PER_DEG_LAT, 2)]

QUERY = f"""
[out:json][timeout:90];
(
  way["building"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
  way["highway"~"^(primary|secondary|tertiary|residential|unclassified|pedestrian|living_street)$"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
);
out geom;
"""

print("Querying Overpass API (this can take ~30s)...")
r = requests.post("https://overpass-api.de/api/interpreter",
                  data={"data": QUERY}, timeout=120)
r.raise_for_status()
elements = r.json()["elements"]

buildings, roads = [], []
for el in elements:
    if el.get("type") != "way" or "geometry" not in el:
        continue
    tags = el.get("tags", {})
    pts = [xy(g["lat"], g["lon"]) for g in el["geometry"]]
    if "building" in tags:
        h = None
        if "height" in tags:
            try: h = float(tags["height"].split()[0].replace("m", ""))
            except ValueError: pass
        if h is None and "building:levels" in tags:
            try: h = float(tags["building:levels"]) * 3.2
            except ValueError: pass
        if h is None:
            h = random.uniform(7, 14)
        buildings.append({"footprint": pts, "height": round(min(h, 80), 1)})
    else:
        roads.append({"path": pts, "kind": tags.get("highway", "road")})

print(f"  {len(buildings)} buildings, {len(roads)} road segments")

# --- Synthetic nodes ---------------------------------------------------------
random.seed(42)
nodes = []

def along(path, spacing):
    """Points every `spacing` m along a polyline."""
    out, carry = [], 0.0
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        seg = math.hypot(x2 - x1, y2 - y1)
        d = spacing - carry
        while d < seg:
            t = d / seg
            out.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
            d += spacing
        carry = (carry + seg) % spacing
    return out

streetlight_pts, junction_pts = [], []
for rd in roads:
    streetlight_pts += along(rd["path"], 45)
    junction_pts.append(tuple(rd["path"][0]))
    junction_pts.append(tuple(rd["path"][-1]))

random.shuffle(streetlight_pts)
for x, y in streetlight_pts[:220]:
    nodes.append({"type": "streetlight", "x": round(x, 1), "y": round(y, 1),
                  "protocol": random.choice(["NB-IoT", "LoRaWAN"])})

junction_pts = list(dict.fromkeys(junction_pts))
random.shuffle(junction_pts)
for x, y in junction_pts[:60]:
    nodes.append({"type": "cctv", "x": round(x, 1), "y": round(y, 1),
                  "protocol": random.choice(["Wi-Fi", "Cellular"])})

half_w = (LON_MAX - LON_MIN) * M_PER_DEG_LON / 2 * 0.9
half_h = (LAT_MAX - LAT_MIN) * M_PER_DEG_LAT / 2 * 0.9
for _ in range(45):
    nodes.append({"type": "air_quality",
                  "x": round(random.uniform(-half_w, half_w), 1),
                  "y": round(random.uniform(-half_h, half_h), 1),
                  "protocol": "LoRaWAN"})
for _ in range(8):
    nodes.append({"type": "gateway",
                  "x": round(random.uniform(-half_w, half_w), 1),
                  "y": round(random.uniform(-half_h, half_h), 1),
                  "protocol": "Cellular"})

print(f"  {len(nodes)} synthetic nodes")

with open("bristol_data.json", "w") as f:
    json.dump({"attribution": "Buildings/roads (c) OpenStreetMap contributors; nodes are synthetic",
               "buildings": buildings, "roads": roads, "nodes": nodes}, f)
print("Wrote bristol_data.json")
