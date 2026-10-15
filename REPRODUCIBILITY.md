# UrbanGraph Extension v1 — Reproducibility Note

Date: 2026-10-11. All artefacts in this directory; originals preserved untouched in
`original/` (byte-identical to the audited evidence copies).

## Layout

```
urbangraph_extension/
├── original/           # UNTOUCHED original demonstrator + its generated data
│   ├── index.html  fetch_bristol.py  bristol_data.json
│   └── run_cached.py  overpass_cache.json   # transport shim (see note below)
├── extended/           # extension v1
│   ├── index.html                                # picking + asset panel
│   ├── fetch_bristol.py                          # IDs + provenance + contract fields
│   ├── urbangraph_asset_contract_v1.schema.json  # versioned JSON contract
│   ├── bristol_data_v1.json                      # generated output (validated)
│   └── run_cached.py  overpass_cache.json
├── osm_map.osm         # raw OSM /api/0.6/map payload (source data, ODbL)
└── screenshots/        # before_original / after_overview / after_selected_cityhall
```

## Reproduce

```bash
# 1. Data (network path used this run)
curl "https://api.openstreetmap.org/api/0.6/map?bbox=-2.6055,51.4487,-2.5880,51.4568" \
     -H "User-Agent: UrbanGraph-research-prototype/1.0" -o osm_map.osm
# convert to Overpass-style JSON (converter inline in change log), then:
python3 run_cached.py fetch_bristol.py     # in original/ -> bristol_data.json
python3 run_cached.py fetch_bristol.py     # in extended/ -> bristol_data_v1.json

# 2. View
cd extended && python3 -m http.server 8000
open http://localhost:8000/index.html
# select a building by click, or:
open "http://localhost:8000/index.html?select=osm:way/4309554"   # Bristol City Hall

# 3. Screenshots (headless)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --use-angle=swiftshader --window-size=1440,900 \
  --virtual-time-budget=25000 --screenshot=out.png \
  "http://localhost:8000/index.html?select=osm:way/4309554"
```

## Transport note (honesty)

Overpass endpoints were unavailable from this network on 2026-10-11
(overpass-api.de → HTTP 406; kumi.systems / private.coffee → HTTP 500 after the first
successful test query). The same OSM data was therefore pulled from the **official OSM API**
`/api/0.6/map` bbox call (200 OK, 23,579 nodes / 3,950 ways), converted to Overpass-style
JSON (`overpass_cache.json`), and both pipeline scripts ran **unmodified** against that cache
via `run_cached.py` (monkeypatches `requests.post` only). When Overpass is reachable, the
extended script works directly: `python fetch_bristol.py` — no shim needed.

## Determinism

Extended pipeline output is byte-identical across runs except `generated_at`
(verified 2026-10-11 by double run + JSON comparison). The original script was NOT
deterministic for fallback heights (RNG seeded after building processing) — fixed in the
extension by seeding before any randomness; recorded in the change log.

## Data snapshot facts (this run)

- 1,341 buildings, all with unique preserved OSM way IDs; 444 road segments; 333 synthetic nodes.
- Height provenance: 6 `osm_tag:height`, 550 `building:levels × 3.2 m estimate`,
  785 `synthetic_fallback` (generated — visually tinted warm in the viewer, flagged in panel).
- OSM data timestamp: per-element timestamps are not present in the `/map` payload; the
  retrieval timestamp (2026-10-11T22:13:02Z) is recorded as `generated_at`.
- Schema validation of `bristol_data_v1.json` against contract v1: PASS (manual checks —
  `jsonschema` package not installed; all 1,341 ids match `^osm:way/\d+$`, reserved fields
  null/empty, nodes flagged synthetic).
