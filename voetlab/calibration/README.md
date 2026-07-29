# voetlab/calibration — pitch homography (broadcast px → real-world metres)

The stage that turns every pixel distance/speed into **metres / km·h**, and unlocks
true-pitch heatmaps, pitch control, and Voronoi. Two paths: the **TVCalib full camera solver**
(primary, accurate) and a **DLT-from-lines fallback**, both gated by self-verification.

## What's here
- **`homography.py`** — pure cv2 engine (the testable core): `estimate_homography` (RANSAC),
  `warp_points`, `px_to_meters`, `self_verify(H, …, tau=0.5m)`. IFAB pitch `PITCH_M = (105, 68)`.
- **`keypoint.py`** — pitch-landmark keypoints → homography point pairs. Named IFAB
  `TEMPLATE_POINTS` (metres); `pairs_from_keypoints`, `is_ground_line`, `filter_keypoints`,
  `line_coverage`, `keypoint_summary`; plus the ops integration `detect_keypoints_tvcalib`
  (seg → line-extremity extraction, full-image px) and `homography_from_keypoints` (DLT).
- **`homography_lines.py`** — DLT homography from LINE correspondences
  (SoccerNet/sn-calibration baseline). Pure numpy, self-contained: `normalization_transform`,
  `estimate_homography_from_line_correspondences`. Returns IMAGE→TEMPLATE.
- **`tvcalib_solver.py`** — the accurate path. `calibrate_with_tvcalib(kp_full_px, w, h)` runs
  `TVCalibModule.self_optim_batch` (AdamW, ~2000 steps — the WACV'23 method), projects a
  template ground grid through the solved camera, and derives `(H_image_to_template, loss_ndc_total)`
  (or `None` if tvcalib is unavailable).
- **`metric.py`** — the bridge: `tracks_to_metric(track_value, H, teams)` warps each player's
  **feet** (bbox bottom-centre) through `H` per frame → `{"frames": {f: [{track_id, x_m, y_m, team}]}}`.
- **`features.py`** — the `calibrate` feature (reg'd, no deps). Samples 12 frames, loads the seg
  model **once**, runs the TVCalib solver per frame, and accepts the lowest-`loss` `H` below
  **τ=0.05** (early-stops if loss < 0.02); falls back to DLT gated by reprojection error < 15 m.
  Publishes `H` to `state.meta["H"]` so metric features (stats/tactics) emit metres.

## How to use
```python
from voetlab.pipeline.default import run

res = run("football-1.mp4", max_frames=500, meta={
    "calib_checkpoint": "external/tvcalib/data/segment_localization/train_59.pt",
    "tvcalib_path": "external/tvcalib",
})
res.value["data"]["calibrate"]        # {"H": ..., "method": "tvcalib_solver", "solver_loss": 0.01...}
# Without meta["calib_checkpoint"] the feature returns Result.Fail and downstream degrades to pixels.
```
Pure-engine use (no video, fully unit-testable):
```python
from voetlab.calibration.homography import estimate_homography, px_to_meters, self_verify
H = estimate_homography(image_pts, template_pts)      # ≥4 point pairs
x_m, y_m = px_to_meters((120, 80), H)
self_verify(H, image_pts, template_pts, tau=0.5)      # accept only if reproj err ≤ 0.5 m
```

## When to use
After `track`/`ball`/`teams` (calibration is independent of them, but its output feeds the
metric features). Needs the external **tvcalib** repo on `sys.path` + the `train_59.pt`
checkpoint (see `docs/BUILD_FROM_SCRATCH.md` Phase 14 and wiki learning
`tvcalib-keypoint-detection-integration`). Without it, `calibrate` fails gracefully and the
pipeline continues in **pixels**.

## Quality & limitations — READ each file's header comment
- `homography`: exact & deterministic; correctness is **entirely determined by keypoint quality** —
  a bad point set gives a confident-but-wrong H. `self_verify` catches gross mismatches only.
- `tvcalib_solver`: the paper's method (verified loss ≈ 0.01 < τ=0.019); ~2000 opt steps/frame
  (seconds on GPU); needs enough visible ground lines.
- `keypoint`: broadcast frames often show <4 usable lines per frame → the feature samples many.
- `homography_lines`: needs the `soccernet` package; <4 valid line correspondences → `None`.

## Tests
`tests/` — `test_homography.py` (pure engine + self-verify), `test_homography_lines.py`
(DLT-from-lines), `test_keypoint.py` + `test_keypoint_quality.py` (pairing/filtering/coverage),
`test_calibrate.py` (feature wiring + fallback path). Pure-engine tests run with no tvcalib deps.

## Not here yet (planned)
- Per-shot re-calibration (reuse last good H within a shot); smoother metric velocity (T5).
- Wire `H` confidence into the reliability signal (currently `homography_conf=1.0`).

## Original reference
Built fresh — TVCalib (WACV23, MM4SPA/tvcalib).
