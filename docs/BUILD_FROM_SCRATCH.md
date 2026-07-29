# pitchkit — Build-from-Scratch Guide for an LLM

> **Goal:** reproduce the `pitchkit` framework **exactly** — same files, same logic, same
> behaviour — by following these ordered, TDD-locked todos. If you (an LLM) complete every
> phase, you will arrive at a package with **121 passing tests** that runs the full
> broadcast-football pipeline (detect → track → ball → teams → events → stats) with high ball
> recall, accurate metric calibration, an auto reliability signal, and a one-command report.
>
> **Reproduction contract:** `python -m pytest pitchkit -q` → **121 passed**; `import pitchkit;
> pitchkit.run(video)` works standalone; `src/` (the original engine) stays untouched.

---

## How to use this guide

- Work **top to bottom**; each phase depends on the prior. Use the `todo` tool to track each
  `TODO` block (create → claim → do → done). **TDD is mandatory:** write the test first (red),
  implement (green); only green marks a todo done. Keep `pytest pitchkit -q` green between
  phases.
- **Conventions (non-negotiable)** — every feature file obeys the rule
  `pitchkit-framework-conventions-...`: one feature per file; every feature function returns
  `core.result.Result`; every event carries `source_frames` via `core.provenance`; each file
  has a co-located `tests/` with a footage-driven test that dumps artifacts to
  `pitchkit/tests/out/<feature>/`; **no `src.`/repo imports inside `pitchkit/`** (standalone,
  copyable).
- **Data contracts** (memorize — every feature's I/O conforms):
  - `detect`/`ball`/`track` values are `{"frames": {frame_no(int): [...]}}`.
  - box dict: `{"x1","y1","x2","y2","class"(int),"confidence"(float)}`.
  - track entry: `{"track_id"(int), "x1","y1","x2","y2","confidence"}`.
  - ball entry: a box dict or `None`; interpolated/synthetic points have `confidence == 0.0`.
  - `teams` value: `{"teams": {track_id: "A"|"B"}}`.
  - event dicts always have `source_frames: [int,...]` and `type: str`.
  - `stats` value: `{"players": {tid: {...}}, "teams": {"A":{...},"B":{...}}}`.
  - `Result.Ok(value, **meta)` / `Result.Fail(error, **meta)`; `bool(result)` reads success.

---

## Prerequisites

- Python ≥ 3.10, a venv. `pip install` core deps: `numpy opencv-python scipy scikit-learn
  filterpy pytest`. Extras: `pip install ultralytics supervision` (vision),
  `matplotlib mplsoccer` (viz), `sahi` (ball recall), and — only for accurate calibration —
  `kornia soccernet pytorch-lightning` + the external `tvcalib` repo (Phase 14, optional).
- The canonical test fixture **`football-1.mp4`** (1920×1080 @ 29.97fps, 1806 frames) in the
  repo root. All footage-driven tests key off it (skip gracefully if absent).
- `yolov8s.pt` (Ultralytics auto-downloads) and, for high ball recall, a specialist model at
  `models/martinjolif_ball.pt` (Phase 3).

---

## Phase 0 — Scaffold the standalone package  *(TODO F0)*
- Create `pitchkit/pyproject.toml` (name=pitchkit, requires-python>=3.10; core deps + optional
  extras `[vision]`, `[viz]`, `[dev]`) and the **nested** layout `pitchkit/pitchkit/` (the
  importable package) with `__init__.py` (`__version__="0.1.0"`) + domain folders `core
  detection tracking calibration events stats tactics reliability viz pipeline docs`, each with
  `__init__.py`, and `pitchkit/tests/`.
- **Test (red→green):** `pitchkit/tests/test_imports.py` asserts `import pitchkit` +
  `__version__` + every subpackage resolves.
- **Accept:** `pip install -e ./pitchkit --no-deps` works; `import pitchkit` from a **clean
  cwd** works; pytest green. *(Critical: nested layout — flat layout silently breaks the
  editable install.)*

## Phase 1 — Core contracts  *(TODOs F1, F2, F3)*
- **F1 `core/result.py`** — `@dataclass Result(ok,value,error,meta)` + `Result.Ok/Fail`;
  `__bool__` returns `ok`. Test: `Ok()` truthy + meta round-trips; `Fail()` falsy + error set.
- **F2 `core/provenance.py`** — `attach_provenance(event, source_frames, **refs)`; raises
  `ValueError` on empty frames. Test: pass event gets `source_frames`; rejects empty.
- **F3 `core/fixtures.py`** — `DEFAULT_FOOTAGE="football-1.mp4"`; `load_sample_frames(n)`,
  `footage_meta()`, `dump_artifacts(feature, frames, data, fig, out_root)` → writes
  `tests/out/<feature>/{annotated.png, results.json[, figure.png]}`. Test: loads 3 frames from
  football-1.mp4 (1080×1920); dump writes PNG+JSON. *(Fixtures are lazy-imported: numpy/cv2
  only inside functions.)*

## Phase 2 — Pipeline core  *(TODO F4)*
- `pipeline/registry.py` — `@feature(name, deps=[])` decorator + global `_FEATURES`; `Feature`
  holds `(name, fn, deps)`.
- `pipeline/runner.py` — `PipelineState(footage, meta, data, results)` with `.get(name)`;
  `run(names, footage, meta)` executes in **topological (dep) order**, collects `Result`s,
  **flags failed features without crashing** (try/except per feature); `run_feature(name,
  footage, meta, data)` isolates ONE feature (pre-fill upstream via `data`); `compare(baseline,
  current)` diffs metric dicts. `_topo_order` detects cycles + unknown features.
- **Test (`pipeline/tests/test_runner.py`):** 3-node graph runs dep-order; a failing node is
  flagged and run completes; downstream reads `state.get(upstream)`; `run_feature` isolation;
  unknown feature → Fail; `compare` deltas. *(Use uniquely-named throwaway features + explicit
  `names=` so tests never clobber the real registry.)*

## Phase 3 — Detection  *(TODOs P1, T8)*
- `detection/detect.py` — `detect(video, *, max_frames, conf=0.3, classes=(0,32),
  model_path="yolov8s.pt", model=None, sahi=False, slice_size=640, ball_model_path=None,
  ball_class=0) -> Result(value={"frames":{f:[boxes]}})`. `boxes_from_result(r)` parses an
  ultralytics result; `annotate(frame, boxes)` draws; `build_vision_config(...)` returns a
  config dict (T8); when `sahi`, `_run_sahi(...)` does per-frame sliced inference (injectable
  `frames=` for tests); `detect_ball_sahi(video, ball_model_path, ...)` returns ball boxes
  normalized to `class=BALL(32)` (the validated 98%-recall path). Register `@feature("detect")`
  + `@feature("detect_ball")` reading `state.meta`. `PERSON=0`, `BALL=32`.
- **Tests:** mocked-YOLO unit tests (inject `model=`) for config passthrough + SAHI branch
  (monkeypatch `sahi.predict.get_sliced_prediction`); a real-footage smoke on football-1.mp4
  (3 frames) that dumps `tests/out/detect/annotated.png`.
- **Accept:** `detect_ball_sahi` on football-1.mp4 with the martinjolif model ≈ **98% ball
  coverage** (the headline win).

## Phase 4 — Tracking  *(TODOs P2, P3, T6, P4, T1, T2, T3, T9)*
- `tracking/player_tracker.py` — `track_players(detections_value, *, fps=25, ...) -> Result`;
  `sv.ByteTrack` over person boxes. `@feature("track", deps=["detect"])`.
- `tracking/ball_tracker.py` — `track_ball(detections_value, *, total_frames, max_gap=100) ->
  Result`; **linear** interpolation, synthetic points `confidence=0.0`, never fails.
  `@feature("ball", deps=["detect"])` that **prefers `state.get("detect_ball")` else
  `state.get("detect")"`**, and dispatches to Kalman when `meta["ball_method"]=="kalman"`.
- `tracking/ball_trajectory.py` (T6) — `KalmanBall2D` (pure-numpy constant-velocity Kalman) +
  `track_ball_kalman(...)`: ~100% coverage from first detection; lower RMSE than linear on
  noisy linear motion.
- `tracking/team_classifier.py` — `extract_torso_hsv(frame, box)`; `_hue_circular(hs)` →
  `(cos,sin,S)`; `cluster_teams_hsv(samples, k=2, circular=True)` (T1 fix for red jerseys);
  `classify_teams(video, tracks, *, sample_frames=100, frame_source=None)` KMeans k=2;
  `stabilize_team_labels(per_frame_teams)` per-track majority vote (T2). `@feature("teams",
  deps=["track"])` (injectable `frame_source=` for tests).
- `tracking/role_filter.py` (T3) — `classify_roles(tracks_value, *, width=None) ->
  Result({"roles":{tid:"player"|"gk"|"referee"}})` via bbox-centroid heuristics (referee =
  large x-spread + many frames; gk = confined to edge band). `@feature("roles", deps=["track"])`.
- `tracking/tracker_factory.py` (T9) — `build_tracker(name, *, reid, gmc)` returns a config
  dict; `"botsort"` → engine ultralytics + the shipped `pitchkit_botsort.yaml` (CMC
  `gmc_method: sparseOptFlow`); `"bytetrack"` → supervision. `track_via_ultralytics(video,
  model_path, tracker=None, ...)` runs `model.track(tracker=<our yaml>)`. Ship
  `pitchkit/pitchkit/tracking/pitchkit_botsort.yaml` (the CMC config — this fixes the dead-config bug).
- **Tests:** synthetic-data unit tests for each (consistent track_ids; interpolation coverage;
  circular-hue clusters wrapped reds; majority vote; role heuristics; factory config). All
  co-located in `tracking/tests/`.

## Phase 5 — Calibration  *(TODOs T4, +keypoint quality, +DLT, +metric, +solver, +calibrate)*
- `calibration/homography.py` (T4) — `PITCH_M=(105,68)`; `estimate_homography(img_pts,
  tpl_pts)` (cv2.findHomography RANSAC, None if <4); `warp_points(pts,H)`;
  `px_to_meters(pt,H)`; `self_verify(H,img,tpl,tau=0.5)`. Test: known rectangle → meters ±0.5.
- `calibration/keypoint.py` — IFAB `TEMPLATE_POINTS` (metres); `pairs_from_keypoints(img_by_name,
  template)`; `is_ground_line(name)` (drop Goal/Circle/unknown — paper's 2D ground-plane rule);
  `filter_keypoints(kp, ground_only, min_separation, min_points)`; `line_coverage(kp_list)`;
  `keypoint_summary(kp)`; `_load_tvcalib_model(checkpoint)`; `detect_keypoints_tvcalib(frame,
  *, model=None, ground_only=True, ...)` (seg → extremities → full-image px, **filtered by
  default**); `homography_from_keypoints(kp, w, h)` (DLT-from-lines via SoccerPitch template,
  returns image→template H or None). Tests are pure/synthetic.
- `calibration/homography_lines.py` — pure-numpy `normalization_transform` +
  `estimate_homography_from_line_correspondences(lines, T1, T2)`. Test: recover a known H.
- `calibration/metric.py` — `tracks_to_metric(track_value, H, teams=None)` warps feet → metres
  (the bridge for stats/tactics).
- `calibration/tvcalib_solver.py` — `calibrate_with_tvcalib(kp_full_px, w, h, ...) -> (H, loss)
  | None`: keypoints normalized → `InferenceDatasetCalibration` → `TVCalibModule.self_optim_batch`
  → project a **template ground grid** (z=0, filtered finite+in-bounds) → cv2 homography; read
  loss key **`loss_ndc_total`**; gate τ≈0.05. *(THE two bugs to avoid: pass points as
  `(1,-1,3)` not `(1,1,-1,3)`; read `loss_ndc_total` not `loss_total`.)*
- `calibration/features.py` — `@feature("calibrate")`: samples 12 frames, loads seg model ONCE,
  runs the **solver (primary)** with DLT fallback, publishes `H` to `state.meta["H"]`, gates on
  `loss < τ` (solver) or reprojection <15 m (DLT).
- **Accept:** solver `loss_ndc_total ≈ 0.0057` (< τ), grid-H self-consistent ≈ 0 m, real metres
  in stats.

## Phase 6 — Events  *(TODOs P5, T7)*
- `events/events.py` — `detect_events(tracks, ball, teams, *, possession_radius=80,
  change_threshold=3, tackle_radius=80) -> Result({possession,passes,tackles,interceptions})`.
  Possession = nearest player (feet) to ball each frame it's seen; debounced changes;
  same-team → `type="pass"`, cross-team+close → `type="tackle"`, else `type="interception"`.
  **Every event gets `attach_provenance(..., source_frames=[frame])` + `type`.** `@feature
  ("events", deps=["track","ball","teams"])`.
- **Tests:** synthetic pass (same team) + tackle (cross-team, close) with non-empty
  `source_frames`; per-frame possession when ball present every frame (T7).

## Phase 7 — Stats  *(TODOs P6, T5)*
- `stats/stats.py` — `compute_stats(tracks, teams, events, *, fps=25, sprint_threshold=150,
  H=None) -> Result({players, teams})`. Per player: distance/speed/sprints (px always; **+**
  `distance_m`/`top_speed_km_h` when `H` via `tracks_to_metric` warping feet each frame),
  passes/tackles/possession counts. `_empty_player` includes both px + metric fields (metric
  default 0.0). `@feature("stats", deps=["track","teams","events"])` reads `meta["H"]`.
- **Tests:** synthetic moving track → distance/speed; metric stats with a known H; possession
  aggregation to team.

## Phase 8 — Tactics  *(TODOs T11, T12)*
- `tactics/pitch_control.py` (T11) — `compute_pitch_control(players, ball_xy, pitch_m,
  grid_step=1.0) -> np.ndarray` (2D prob surface, values in [0,1]); pure numpy, Spearman-style
  reach (time-to-intercept via clamped run speed). Not a `@feature` (needs metric+velocity).
- `tactics/voronoi.py` (T12) — `dominant_regions(players, pitch_m, step=1.0)` (cKDTree raster
  assignment → team areas) + `team_area_ratio(...)`.
- `tactics/features.py` — `@feature("voronoi", deps=["track"])` and `@feature("pitch_control",
  deps=["track"])` that read `track` + `meta["H"]`, convert via `tracks_to_metric`, and compute
  (velocity by finite-diff for pitch control); Fail clearly without H. *(Watch the
  `np.unique`-groups-by-index trap: accumulate area per team, don't overwrite.)*
- **Tests:** pitch-control surface shape + attacker-dominates pattern; voronoi areas sum ≈ pitch
  area; both features run with `meta={"H":...}` and Fail without H.

## Phase 9 — Reliability  *(TODOs T10, B2)*
- `reliability/reliability.py` (T10) — `compute_reliability(ball, track, *, total_frames,
  homography_conf=1.0, expected_players=22) -> Result({...})`: `ball_coverage` (real-ball
  frames/total), `interpolation_ratio`, `tracking_stability` (1 − over/expected), composites.
- `reliability/features.py` (B2) — `@feature("reliability", deps=["ball","track"])`.

## Phase 10 — Viz  *(TODO T13)*
- `viz/charts.py` — `heatmap(positions)`, `pass_network(avg_positions, passes)`, `radar(params,
  values, low, high)`; headless (`matplotlib.use("Agg")`); mplsoccer `Pitch`/`Radar`; return
  `Figure`s. Test: each returns a `matplotlib.figure.Figure`.

## Phase 11 — Pipeline wiring  *(TODOs P7, B2-cont)*
- `pipeline/default.py` — import **all** feature modules (so `@feature` decorators register:
  detect, trackers, events, stats, calibration.features, tactics.features, reliability.features);
  `DEFAULT_FEATURES = ["detect","track","ball","teams","events","stats","reliability"]`;
  `run(video, *, max_frames, meta, features)` inserts `"detect_ball"` before `"ball"` when
  `meta["ball_model_path"]`, and `"calibrate"` before the first metric feature when
  `meta["calib_checkpoint"]`; `run_feature(name, video, meta)`.
- `pipeline/cli.py` — `python -m pitchkit.pipeline.cli <video> [--feature NAME] [--max-frames N]
  [--ball-model-path P] [--calib-checkpoint P]`; dumps `tests/out/<tag>/results.json`.
- **Test (`pipeline/tests/test_default.py`):** all features registered; `run_feature("detect")`
  isolation (mocked model); a subset run; **e2e smoke on football-1.mp4** (5 frames) →
  detect/track/stats present + n_players>0.

## Phase 12 — Report  *(TODO B3)*
- `report.py` — `report(video, out_dir, *, max_frames, meta)` runs the pipeline and writes
  `summary.json`, `stats.json`, `reliability.json`, and best-effort `radar.png`/
  `pass_network.png`/`heatmap.png` (positions normalized to the statsbomb pitch when no H).
  `main(argv)` CLI `python -m pitchkit.report <video> [--out DIR] ...`.
- **Test (`tests/test_report.py`):** monkeypatch `pitchkit.pipeline.default.run` → fake Result;
  assert summary/stats/reliability/radar written; failing-pipeline still writes summary.

## Phase 13 — Packaging + docs  *(TODOs B4, F6, D1, D2, D3)*
- `__init__.py` (B4) — `from pitchkit.pipeline.default import run, run_feature`; `__all__`.
  Verify `import pitchkit; pitchkit.run` from a **clean cwd**.
- `docs/build_docs.py` (F6) — scans feature `.py`, extracts docstring summary + the
  `# === Quality & when to use ===` block, emits `FEATURES.md` (manifest table) +
  `docs/site/index.html` (sidebar nav, collapsible cards, search, dark mode, print). `docs/tests/
  test_docs.py` regenerates + asserts every feature `.py` is in `FEATURES.md` + every feature
  has a docstring.
- **D1** — each feature file opens with a `# === Quality & when to use (for devs / LLMs) ===`
  comment block (What/Does/GOOD/WEAK/When/Upgrade). **D2** — an LLM/dev-focused `README.md` in
  every domain folder (what's here / how to use / when / quality / tests / not-here-yet / src
  mapping). **D3** — verify `src/` untouched + each README maps to its `src/` origin.

## Phase 14 — (Optional) External TVCalib for accurate calibration
Only needed to make `calibrate` produce real metres (otherwise it fails gracefully → pixels).
- `git clone --recurse-submodules https://github.com/MM4SPA/tvcalib external/tvcalib`.
- Download the 488 MB seg checkpoint: `curl -L
  https://tib.eu/cloud/s/x68XnTcZmsY4Jpg/download/train_59.pt -o
  external/tvcalib/data/segment_localization/train_59.pt`.
- `pip install kornia soccernet pytorch-lightning`.
- **Three compat shims** in the external copy (research code predates torch 2.x / cv2 4.x):
  1. `tvcalib/sncalib_dataset.py`: `from torch._six import string_classes` → fallback
     `string_classes = (str, bytes)`.
  2. `tvcalib/inference.py`: `torch.load(checkpoint)` → `torch.load(checkpoint,
     weights_only=False)`.
  3. `sn_segmentation/src/custom_extremities.py`: `cv.erode(semantic_mask,…)` → cast
     `.astype(np.uint8)` before erode.
- Then `calibrate` runs: `meta={"calib_checkpoint": ".../train_59.pt",
  "tvcalib_path": "external/tvcalib"}`.

---

## Final acceptance (the reproduction is correct when ALL hold)

1. `python -m pytest pitchkit -q` → **121 passed**.
2. `cd /tmp && python -c "import pitchkit; print(pitchkit.__version__, pitchkit.run)"` works
   (truly standalone, not path-dependent).
3. `python -m pitchkit.pipeline.cli football-1.mp4 --max-frames 30` → artifacts written, no
   failed features.
4. With the martinjolif ball model: `detect_ball` ≈ **98% ball coverage** on football-1.mp4.
5. With TVCalib (Phase 14): `calibrate` method `tvcalib_solver`, `loss_ndc_total < 0.019`, and
   `stats` players have sane `distance_m` (single-digit metres over ~30 frames) — not 1e15.
6. `python -m pitchkit.report football-1.mp4 --out report/` writes summary + stats +
   reliability + radar/pass-network/heatmap.
7. `src/` is unchanged from the original repo.

## Reference: the target file tree (28 source files)
```
pitchkit/pitchkit/{__init__,report}.py
pitchkit/pitchkit/core/{result,provenance,fixtures}.py
pitchkit/pitchkit/detection/detect.py
pitchkit/pitchkit/tracking/{player_tracker,ball_tracker,ball_trajectory,team_classifier,
                            role_filter,tracker_factory}.py + pitchkit_botsort.yaml
pitchkit/pitchkit/calibration/{homography,homography_lines,keypoint,metric,
                               tvcalib_solver,features}.py
pitchkit/pitchkit/events/events.py
pitchkit/pitchkit/stats/stats.py
pitchkit/pitchkit/tactics/{pitch_control,voronoi,features}.py
pitchkit/pitchkit/reliability/{reliability,features}.py
pitchkit/pitchkit/viz/charts.py
pitchkit/pitchkit/pipeline/{registry,runner,default,cli}.py
pitchkit/pitchkit/docs/build_docs.py
```
Plus ~25 co-located `tests/test_*.py` files (one or more per feature) and per-folder
`README.md`s. `FEATURES.md` + `docs/site/index.html` are **generated**, not hand-written.

---

## Pitfalls already solved (do not re-introduce)
- **Nested package layout** — flat layout silently breaks `pip install -e` from a clean cwd.
- **T9 dead config** — BoT-SORT CMC only applies if you point `tracker=` at a yaml that sets
  `gmc_method`; passing `"botsort.yaml"` name alone leaves CMC off.
- **HSV hue circularity** — cluster on `(cos,sin,S)`, not raw `(H,S)`, or red teams split.
- **events `type`** — set `ev["type"]` explicitly; provenance `kind` is not the same field.
- **SAHI monkeypatch** — patch `sahi.predict.get_sliced_prediction` (lazy submodule), not
  `sahi.predict` as an attribute.
- **TVCalib point shape** — `project_point2pixel` wants `(1,N,3)`, **not** `(1,1,N,3)`.
- **TVCalib loss key** — `loss_ndc_total`, not `loss_total`.
- **Voronoi area** — accumulate per team (`areas[t] += …`); `np.unique` counts group by player
  index, not team.
- **Measure before flipping defaults** — ByteTrack beat BoT-SORT on the test footage; keep
  ByteTrack default until BoT-SORT is validated on high-motion clips.
