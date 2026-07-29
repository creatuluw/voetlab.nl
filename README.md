# pitchkit

Standalone, copyable football video-analytics framework. Broadcast video in → detection,
tracking, pitch calibration, events, physical/tactical stats, a per-stat reliability signal,
and charts.

pitchkit is the engine of **PREDA** (statspreda.com). The original Telegram-bot prototype
lives untouched in `../src/`; pitchkit is a separate, self-contained package — copy the folder
or `pip install -e`.

## Quickstart

```python
import pitchkit

# Full pipeline: detect → track → ball → teams → events → stats → reliability
res = pitchkit.run("football-1.mp4", max_frames=50, meta={
    "ball_model_path": "models/martinjolif_ball.pt",            # ~98% ball recall (SAHI)
    "calib_checkpoint": "external/tvcalib/data/segment_localization/train_59.pt",  # accurate metres
    "tvcalib_path": "external/tvcalib",
})
res.value["data"]["stats"]        # per-player distance_m / top_speed_km_h
res.value["data"]["reliability"]  # confidence on every number
res.value["failed"]               # any feature that didn't finish

pitchkit.run_feature("detect", "football-1.mp4")   # isolate one stage
```

One-command report (JSON + charts):
```bash
python -m pitchkit.report football-1.mp4 --max-frames 50 --out report/ \
    --ball-model-path models/martinjolif_ball.pt
```

## Install (in any project)

```bash
pip install -e "./pitchkit[vision,viz]"
# …or copy the inner `pitchkit/pitchkit/` folder into another project and `import pitchkit`.
```

Extras: `[vision]` (ultralytics + supervision), `[viz]` (matplotlib + mplsoccer), `[dev]`
(pytest). Core deps: numpy, opencv-python, scipy, scikit-learn, filterpy. `[vision]` + `sahi`
for high ball recall; the external `tvcalib` repo (see `docs/BUILD_FROM_SCRATCH.md` Phase 14)
for accurate metric calibration.

## Layout

```
pitchkit/
  core/        Result (success indicator), provenance, footage fixtures
  detection/   YOLO person+ball detection, SAHI specialist ball detector (detect_ball)
  tracking/    player/ball trackers, Kalman trajectory, team classifier, role filter,
               tracker_factory (ByteTrack default; BoT-SORT available)
  calibration/ homography engine, keypoints, DLT-from-lines, metric bridge,
               TVCalib full solver → accurate metres, calibrate feature
  events/      possession, passes, tackles, interceptions (all frame-provenanced)
  stats/       physical + aggregate stats (pixels + metres/km·h when calibrated)
  tactics/     Spearman pitch control, Voronoi dominant regions
  reliability/ per-stat confidence (the PREDA "reliability signal")
  viz/         mplsoccer chart adapters (heatmap, pass-network, radar)
  pipeline/    feature registry + runner (dep-order, isolation, compare) + default + cli
  report.py    end-to-end report generator + CLI
  docs/        doc generator + HTML site
```

## Conventions (every feature file)

- **One distinct feature per file**, named as a pipeline unit.
- **Returns `core.result.Result`** (`ok / value / error / meta`) — `bool(result)` reads success.
- **Events carry frame provenance** (`source_frames`) via `core.provenance`.
- **Footage-driven test per file**: runs on the canonical clip `football-1.mp4`, asserts
  `Result.ok`, and dumps artifacts to `pitchkit/tests/out/<feature>/` so you can *see* results.

## Test

```bash
python -m pytest pitchkit -q      # 121 tests
```

## Pipeline core

Register features with `@feature(name, deps=[...])`. The runner executes in dependency order,
threads a shared `PipelineState`, collects `Result`s, and **flags failures without crashing**.
`run_feature(name, ...)` isolates one stage; `compare(baseline, current)` diffs metric
snapshots for before/after analysis. The **reliability** feature is in `DEFAULT_FEATURES`, so
every run auto-emits a per-stat confidence.
