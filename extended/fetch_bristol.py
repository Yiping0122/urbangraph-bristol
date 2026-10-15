#!/usr/bin/env python3
"""
UrbanGraph Bristol ingestion — EXTENDED v1 (feasibility extension, 2026-10-11)

Extends the original fetch_bristol.py (preserved at ../original/fetch_bristol.py):
  1. Preserves OpenStreetMap way IDs for buildings and roads (original discarded them).
  2. Adds per-record provenance (source, licence, retrieval timestamp, height_source).
  3. Emits the versioned contract `urbangraph-asset/v1` with RESERVED fields
     (lifecycle / dpp_refs / federation) as explicit nulls/empty arrays — extension
     points only; no lifecycle, DPP or federation system is implemented here.
  4. Deterministic heights: the RNG is seeded BEFORE the synthetic-height fallback,
     so repeated runs are byte-comparable (original seeded only before node generation).

Does NOT: fabricate UPRN links, material attributes, or any non-OSM data.

Usage:
    pip install requests
    python fetch_bristol.py          # writes bristol_data_v1.json

Serve the folder and open the viewer:
    python -m http.server 8000
    ->  http://localhost:8000/index.html
"""
import json, math, random, sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("pip install requests first")

CONTRACT_VERSION = "urbangraph-asset/v1"

# --- Area: Bristol city centre / Harbourside (unchanged from original) --------
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

RETRIEVED_AT = datetime.now(timezone.utc).isoformat(timespec="seconds")

print("Querying Overpass API (this can take ~30s)...")
r = requests.post("https://overpass-api.de/api/interpreter",
                  data={"data": QUERY}, timeout=120)
r.raise_for_status()
osm_meta = r.json().get("osm3s", {})
elements = r.json()["elements"]

random.seed(42)  # seeded BEFORE any randomness -> fully deterministic output

buildings, roads = [], []
for el in elements:
    if el.get("type") != "way" or "geometry" not in el:
        continue
    tags = el.get("tags", {})
    pts = [xy(g["lat"], g["lon"]) for g in el["geometry"]]
    osm_id = f"osm:way/{el['id']}"
    if "building" in tags:
        h, h_src = None, None
        if "height" in tags:
            try:
                h = float(tags["height"].split()[0].replace("m", ""))
                h_src = "osm_tag:height"
            except ValueError:
                pass
        if h is None and "building:levels" in tags:
            try:
                h = float(tags["building:levels"]) * 3.2
                h_src = "osm_tag:building:levels x 3.2m estimate"
            except ValueError:
                pass
        if h is None:
            h = random.uniform(7, 14)
            h_src = "synthetic_fallback"  # explicitly flagged; not real data
        buildings.append({
            "id": osm_id,
            "kind": "building",
            "footprint": pts,
            "height": round(min(h, 80), 1),
            "height_source": h_src,
            "tags": {k: tags[k] for k in
                     ("building", "name", "addr:street", "addr:housenumber",
                      "addr:postcode", "building:levels", "height")
                     if k in tags},
            # --- reserved extension fields (contract v1): NOT implemented ---
            "lifecycle": None,        # future: building lifecycle state from P2
            "dpp_refs": [],           # future: product passport references from P3
            "federation": None,       # future: TwinBridge execution/trace refs
        })
    else:
        roads.append({"id": osm_id, "kind": "road",
                      "path": pts, "highway": tags.get("highway", "road")})

print(f"  {len(buildings)} buildings (IDs preserved), {len(roads)} road segments")

# --- Synthetic nodes (unchanged generation logic; IDs added; synthetic flagged) -
nodes = []

def along(path, spacing):
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
    junction_pts += [tuple(rd["path"][0]), tuple(rd["path"][-1])]

seq = 0
def node(ntype, x, y, protocol):
    global seq
    seq += 1
    nodes.append({"id": f"synthetic:node/{seq:04d}", "type": ntype,
                  "x": round(x, 1), "y": round(y, 1), "protocol": protocol,
                  "synthetic": True})

random.shuffle(streetlight_pts)
for x, y in streetlight_pts[:220]:
    node("streetlight", x, y, random.choice(["NB-IoT", "LoRaWAN"]))
junction_pts = list(dict.fromkeys(junction_pts))
random.shuffle(junction_pts)
for x, y in junction_pts[:60]:
    node("cctv", x, y, random.choice(["Wi-Fi", "Cellular"]))
half_w = (LON_MAX - LON_MIN) * M_PER_DEG_LON / 2 * 0.9
half_h = (LAT_MAX - LAT_MIN) * M_PER_DEG_LAT / 2 * 0.9
for _ in range(45):
    node("air_quality", random.uniform(-half_w, half_w), random.uniform(-half_h, half_h), "LoRaWAN")
for _ in range(8):
    node("gateway", random.uniform(-half_w, half_w), random.uniform(-half_h, half_h), "Cellular")

print(f"  {len(nodes)} synthetic nodes (flagged synthetic:true)")

doc = {
    "contract_version": CONTRACT_VERSION,
    "generated_at": RETRIEVED_AT,
    "provenance": {
        "spatial_source": "OpenStreetMap via Overpass API",
        "overpass_endpoint": "https://overpass-api.de/api/interpreter",
        "bbox": {"lat_min": LAT_MIN, "lat_max": LAT_MAX,
                 "lon_min": LON_MIN, "lon_max": LON_MAX},
        "osm_data_timestamp": osm_meta.get("timestamp_osm_base", "not reported by endpoint"),
        "licence": "ODbL 1.0 (c) OpenStreetMap contributors",
        "nodes_note": "nodes array is SYNTHETIC (seeded RNG), for demonstration only",
        "height_fallback_note": "height_source=synthetic_fallback is generated, not observed",
        "identity_note": "ids are OSM way ids; they are spatial-feature identifiers, "
                         "NOT UPRNs and NOT legal asset identifiers",
    },
    "buildings": buildings,
    "roads": roads,
    "nodes": nodes,
}
with open("bristol_data_v1.json", "w") as f:
    json.dump(doc, f)
print(f"Wrote bristol_data_v1.json (contract {CONTRACT_VERSION})")
