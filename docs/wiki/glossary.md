---
type: Glossary
title: Glossary
description: Key terms for this project.
timestamp: "2026-07-29T20:21:57.442Z"
---

# Glossary

| Term | Definition |
|------|------------|
| voetlab | The standalone, copyable football video-analytics framework that is the engine behind voetlab.nl. |
| Result | The universal success indicator (`core.result.Result`) returned by every feature; has `ok / value / error / meta`; `bool(result)` reads success. |
| Feature | A distinct pipeline unit; one feature per file, registered via `@feature(name, deps=[...])`. |
| Pipeline / runner | The dependency-ordered executor (`pipeline/runner.py`) that threads a shared `PipelineState`, collects `Result`s, and flags failures without crashing. |
| PipelineState | The shared "clipboard" the runner threads between features; each feature's `Result.value` lands in `state.data[name]` for downstream readers. |
| Provenance / source_frames | Frame index(es) stamped onto every event via `core.provenance` so any event traces back to the footage. |
| Footage-driven test | A per-feature test that runs on the canonical `football-1.mp4` clip, asserts `Result.ok`, and dumps artifacts to `tests/out/<feature>/`. |
| Graceful failure | A failing feature is flagged in `res.value["failed"]` rather than raising; the run completes and reports all failures. |
| run / run_feature | Top-level API: `run(video)` runs the full pipeline; `run_feature(name, video)` isolates one stage. |
| meta | The optional `meta` dict passed to a run, carrying opt-in knobs like `ball_model_path`, `ball_method`, `calib_checkpoint`, `tvcalib_path`, `max_frames`, `fps`, `width`. |
| Detection | Per-frame YOLO inference of persons (COCO class 0) and ball; the first pipeline stage. |
| detect_ball / SAHI | Sliced (tiled) inference with a specialist football-ball model yielding ~98% ball-frame recall vs ~1–18% for stock COCO class 32. |
| Track (player tracker) | ByteTrack multi-object tracking over person boxes; produces per-frame `track_id`-bearing entries. |
| ID fragmentation | ByteTrack assigning a single player many IDs across a pan/zoom — degrades per-player stats; the reason BoT-SORT (T9) is offered. |
| Ball tracker / ball trajectory | Ball-per-frame output; linear interpolation (default) or Kalman constant-velocity (`ball_method="kalman"`, T6); synthetic points carry `confidence=0.0`. |
| Team classifier | KMeans k=2 on median HSV torso color, with circular hue (T1) and per-track majority vote (T2) stabilization. |
| Role filter | Pure bbox-centroid geometry heuristics labeling each track `player` / `gk` / `referee` (T3). |
| Homography (H) | The 3×3 image→template (broadcast px → real-world metres) mapping; computed by keypoints+DLT or the TVCalib solver. |
| IFAB pitch | The reference pitch dimensions (105 m × 68 m) used as the template for calibration. |
| Keypoint | A pitch-landmark point detected on the broadcast frame, paired with its known template coordinate to estimate the homography. |
| DLT-from-lines | Direct Linear Transform homography estimated from line correspondences (SoccerNet/sn-calibration baseline). |
| TVCalib | The WACV'23 full camera solver (AdamW, ~2000 steps) that projects a template ground grid through a solved camera to derive an accurate H; the primary calibration path. |
| calibrate | The calibration feature that samples frames, runs the TVCalib solver (τ=0.05 loss gate) with DLT fallback (reproj < 15 m), and publishes `H` to `state.meta`. |
| metric (space) | Real-world metres coordinates obtained by warping pixel tracks (player feet) through `H`; what unlocks true distance/speed/heatmaps. |
| Events | On-ball actions (possession, passes, tackles, interceptions) derived from tracks+ball+teams, each frame-provenanced. |
| Stats | Terminal per-player/per-team aggregates: distance, top speed, sprints, pass/tackle/possession counts (pixels unless calibrated). |
| Pitch control | Spearman model giving P(team A controls) per pitch cell from time-to-reach influence (T11). |
| Voronoi / dominant region | Tessellation giving each team's nearest-player territory area ratio (T12). |
| Reliability signal | voetlab's per-stat 0–1 confidence propagated from measurable CV-quality inputs (ball coverage, interpolation ratio, track fragmentation, homography conf). |
| homography_conf | A reliability input currently hardcoded to `1.0` (not yet wired from calibration) — see the reliability learning. |
| tracking_stability | A reliability proxy = `1 − max(0, n_tracks − 22)/22`; a fragmentation indicator, not a true tracker-quality metric. |
| viz / charts | mplsoccer adapters producing matplotlib `Figure` objects (heatmap, pass network, radar); headless, no UI. |
| DEFAULT_FEATURES | The wired default graph, which includes `reliability`, so every run auto-emits a per-stat confidence. |
| compare | A runner helper that diffs two metric snapshots (baseline vs current) for before/after analysis. |
| T-codes (T1–T13) | Upgrade task identifiers in the dev log (e.g. T4=homography, T6=Kalman ball, T8=SAHI ball, T9=BoT-SORT, T11=pitch control, T12=Voronoi, T13=charts). |
| OKF | The Open Knowledge Format used for `docs/wiki/` — frontmatter-typed concepts (Decisions, Rules, Learnings, Preferences, Pages). |
