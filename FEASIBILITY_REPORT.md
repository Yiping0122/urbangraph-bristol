# Technical Feasibility Report — UrbanGraph Extension v1

**Date:** 2026-10-11 · **Timebox:** one working day (actual: ~3.5 hours, incl. endpoint
outage troubleshooting) · **Mode:** isolated copy; originals preserved.

## Success criterion assessment

> "A user can select an individually identifiable building in UrbanGraph, inspect its
> source-backed attributes and see a documented extension point for future federated asset
> information."

**MET.** Evidence: `screenshots/after_selected_cityhall.png` — Bristol City Hall
(`osm:way/4309554`) selected and highlighted; panel shows source-backed attributes (OSM tags:
government, College Green, BS1 5TR, 5 levels; height 16 m from `building:levels × 3.2`;
footprint ≈ 3,707 m² / 81 vertices), full provenance block, and the three reserved
federation fields rendered as documented nulls.

## Findings per scope item

1. **Preserve OSM identifiers — DONE, low cost.** The original pipeline read way IDs and
   discarded them. Threading them through cost ~15 lines. 1,341/1,341 buildings now have
   unique, preserved IDs. Caveat documented in-contract: OSM way IDs are spatial feature
   identifiers, **not** stable legal asset IDs (no UPRN fabrication — per constraint).
2. **Per-building picking — DONE, moderate cost.** Required replacing the merged mesh with
   per-building meshes (the audit's predicted single intrusive change). 1,341 extruded
   meshes render acceptably even in SwiftShader software WebGL (headless screenshot
   completed within the 25 s budget); hardware WebGL will be comfortably faster. Raycasting
   1,341 low-poly meshes per click is trivial. **No stop-condition triggered** — refactoring
   stayed well under the "major" threshold (~120 added lines in the viewer).
3. **Asset information panel — DONE.** Geometry-derived attributes are computed client-side
   (shoelace area) or carried from ingestion (height + height_source). Provenance is
   first-class: source, retrieval time, OSM data currency, licence, identity scope.
4. **Versioned JSON contract — DONE.** `urbangraph-asset/v1` (JSON Schema draft 2020-12)
   with three RESERVED fields (`lifecycle`, `dpp_refs`, `federation`) constrained to
   null/empty in v1 — future systems can populate them without breaking v1 readers, and v1
   tooling validates that nothing is fabricated prematurely. Generated output validated PASS.
5. **Existing visualisation intact — VERIFIED.** `before_original.png` vs
   `after_overview.png`: same scene composition, camera, lighting, roads, nodes, controls,
   screenshot button. The only visual difference is deliberate: warm tint on the 785
   buildings whose heights are generated fallbacks (honesty cue).
6. **Determinism — IMPROVED over original.** Original pipeline produced nondeterministic
   fallback heights (RNG seeded after use). Extension seeds before all randomness; double-run
   comparison confirms byte-identical output modulo timestamp.

## Issues encountered (for the risk register)

| Issue | Impact | Handling |
|---|---|---|
| Overpass API unavailable from this network (406/500 across three mirrors) | Medium — ingestion blocked until alternate transport found | Switched to official OSM API `/api/0.6/map` + format converter; scripts unchanged. **Confirms audit risk R7 (external availability); WP1 should snapshot data early.** |
| 59% of building heights are generated fallbacks (785/1,341) | Low for demonstrator; material for claims | Now measured, flagged in data (height_source), tinted in view, and disclosed in panel. Never present these heights as observed. |
| `jsonschema` package absent in runtime | Trivial | Manual validation performed; WP2 should pin a validator dependency |

## Implications for TwinBridge planning (no claim changes yet — per instruction)

- The F2-R2 "intrusive change" (per-building identity + picking) is **measured feasible at
  ~0.5 day**, against the F5 estimate of 3–10 days — evidence supports the optimistic end,
  though the UPRN join, service boundary and federation panel remain unbuilt and their
  estimates stand.
- The v1 contract demonstrates the reserved-field pattern the federation layer will use;
  final contract shape remains a WP2 decision.
- The endpoint outage is live evidence for early data snapshotting in WP1.

**Approval note:** per instruction, funding-application claims remain unchanged until this
extension is reviewed and approved. Suggested claim upgrade *if approved*: "UrbanGraph has
been extended (pre-award feasibility test) to per-building selectable assets with preserved
OSM identifiers, source-backed attribute panels and a versioned federation contract" —
supported by this directory's evidence.
