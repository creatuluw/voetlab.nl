---
type: Glossary
title: Glossary
description: Key terms for this project.
timestamp: "2026-07-29T17:16:52.594Z"
---

# Glossary

| Term | Definition |
|------|------------|
| voetlab | The standalone, copyable football video-analytics framework this project ships. Python 3.10+, MIT. |
| voetlab | The product (voetlab.nl) that voetlab powers — broadcast-footage match analytics. |
| Result | The universal success indicator (`core.result`). Every feature returns `Result.Ok(value, **meta)` / `Result.Fail(error, **meta)`; `bool(result)` reads success. |
| Provenance | Frame traceability (`core.provenance.attach_provenance`). Stamps each event with the `source_frames` it came from. |
| Feature | A single pipeline unit, one per file, registered via `@feature(name, deps=[...])`. |
| PipelineState | The shared clipboard the runner threads between features; each result lands in `state.data[name]`. |
| `run` / `run_feature` | Top-level API. `run(video)` = full default graph; `run_feature(name, video)` = isolate one stage. |
| `compare` | Runner helper that diffs two metric snapshots for before/after analysis. |
| DEFAULT_FEATURES | The default pipeline graph; includes `reliability`, so every run auto-emits per-stat confidence. |
| SAHI | Sliced Aided Hyper Inference. N× tiled inference that lifts ball recall from ~1% (COCO) to ~98% with a specialist model. |
| Ball recall / coverage | Fraction of frames the real ball is detected on — the key CV-quality signal feeding reliability. |
| TVCalib | Full broadcast-camera solver (WACV23, MM4SPA/tvcalib) that yields an accurate pixel→metre homography. |
| Homography | The 3×3 transform mapping broadcast pixels to real pitch metres (105×68 m); unlocks true-pitch stats, heatmaps, tactics. |
| DLT | Direct Linear Transform — the line-correspondence homography fallback (SoccerNet/sn-calibration baseline). |
| Metric space | Real-world pitch coordinates (metres) as opposed to raw pixel coordinates. |
| ByteTrack / BoT-SORT | Multi-object trackers. ByteTrack (supervision) is default; BoT-SORT/OC-SORT (ultralytics) via the tracker factory adds CMC/ReID. |
| ID fragmentation | A tracking failure where one player gets many IDs across pan/zoom — degrades per-player stats. |
| Pitch control | (Tactics) Spearman-style field giving P(team A controls) at each pitch point from player reach/time-to-reach. |
| Voronoi / dominant region | (Tactics) Tessellation of the pitch into each player's nearest territory; yields team-area ratio. |
| Reliability signal | voetlab's product moat: an honest, automatic per-stat confidence derived from measurable CV-quality (ball coverage, tracking stability, interpolation ratio, calibration confidence). |
| Footage-driven test | A feature's co-located test that runs on `football-1.mp4`, asserts `Result.ok`, and dumps artifacts to `tests/out/<feature>/`. |
| `[vision]` / `[viz]` / `[dev]` | Optional extras in `pyproject.toml`: vision = ultralytics+supervision; viz = matplotlib+mplsoccer; dev = pytest. |
| OKF | The knowledge-wiki bundle format this `docs/wiki/` follows (concepts, decisions, rules, learnings, preferences). |
