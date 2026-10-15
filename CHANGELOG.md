# Source-Change Log — UrbanGraph Extension v1

Date: 2026-10-11. Baseline: original `index.html` (185 lines) + `fetch_bristol.py` (122
lines), preserved byte-identical in `original/`. All changes are additive in `extended/`.

## fetch_bristol.py → extended/fetch_bristol.py

| # | Change | Lines (extended) | Motivation |
|---|---|---|---|
| C1 | Contract header: `CONTRACT_VERSION = "urbangraph-asset/v1"`; `RETRIEVED_AT` timestamp | 33–44 | Requirement 4 (versioned contract) |
| C2 | RNG seeded **before** building heights | 68 | Original seeded only before nodes → fallback heights were nondeterministic; now fully reproducible |
| C3 | Building records carry `id: osm:way/<id>`, `kind`, curated `tags` (building/name/addr/levels/height), `height_source` enum (`osm_tag:height` / `osm_tag:building:levels x 3.2m estimate` / `synthetic_fallback`) | 71–103 | Requirements 1 & 3; honesty flag for generated heights |
| C4 | Reserved extension fields `lifecycle: None`, `dpp_refs: []`, `federation: None` on every building | 95–97 | Requirement 4 — documented extension points, no systems implemented |
| C5 | Roads carry preserved `id` + `highway` class | 104–105 | Requirement 1 |
| C6 | Nodes carry `id: synthetic:node/NNNN` and `synthetic: true` | 118–124 | Provenance honesty (they are generated) |
| C7 | Top-level document: `contract_version`, `generated_at`, `provenance` block (endpoint, bbox, OSM timestamp, licence, identity-scope note: OSM ids ≠ UPRN) | 151–168 | Requirement 3 (provenance) + no fabricated UPRN links |
| C8 | `osm3s.timestamp_osm_base` captured when the endpoint reports it | 66, 161 | Data currency evidence |

## index.html → extended/index.html

| # | Change | Motivation |
|---|---|---|
| V1 | Loads `bristol_data_v1.json`; warns on unexpected `contract_version` | Contract consumption |
| V2 | **Per-building meshes** replace the single merged mesh (only intrusive rendering change); each mesh carries its record in `userData.building` and is named by OSM id | Requirement 2 — selection is impossible on a merged mesh (audit A2) |
| V3 | Raycaster click-pick with drag-vs-click disambiguation (5 px threshold); click empty ground deselects | Requirement 2 |
| V4 | Selected building highlighted (purple); synthetic-fallback-height buildings tinted warm at rest and flagged "⚠ generated fallback — not observed data" in the panel | Honesty invariant for generated heights |
| V5 | Asset information panel: identity, geometry-derived attributes (height + source, planar footprint area via shoelace, vertex count), OSM tags, provenance block (source/retrieved/OSM timestamp/licence/identity scope) | Requirement 3 |
| V6 | Panel section "Federation extension points": renders the three reserved fields with their current null/empty values and an explicit "no system connected" notice | Requirement 4 — visible documented extension point |
| V7 | `?select=<osm:way/ID|first|withtags>` URL hook for automated testing/screenshots | Testability |
| V8 | Removed unused BufferGeometryUtils import (merge no longer used); legend/hint text additions | Clean-up |

## Explicitly NOT changed / NOT implemented

- Original files untouched (verified: `original/` matches audited evidence copies).
- No P2/P4 twins, no BaSyx, no registry/discovery/composer — reserved fields only.
- No UPRN links fabricated; panel states identity scope explicitly.
- No material attributes invented.
- Camera/lights/roads/nodes rendering logic unchanged.

## Data-transport deviation (this run only)

Overpass unavailable from this network → data pulled from official OSM API `/api/0.6/map`
and replayed through **unmodified** scripts via `run_cached.py`. Details in REPRODUCIBILITY.md.
