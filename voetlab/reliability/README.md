# voetlab/reliability — per-stat confidence (the voetlab signal)

voetlab's product moat is "a reliability signal on every number". Instead of inventing a score,
this propagates **real, measurable CV-quality signals** (ball coverage, interpolation ratio,
track-ID fragmentation, homography confidence) into a 0–1 confidence per category. Fully
transparent — every input is an inspectable number.

## What's here
- **`reliability.py`** — `compute_reliability(ball_value, track_value, *, total_frames,
  homography_conf=1.0, expected_players=22) -> Result`. Emits:
  - `ball_coverage` / `ball_total_coverage` — real-ball frames / total (and any-ball incl. interpolated);
  - `interpolation_ratio` — synthetic-ball frames / ball frames;
  - `n_tracks` + `tracking_stability` — `1 − max(0, n_tracks − expected)/expected` (a fragmentation proxy);
  - `homography_conf` — passthrough (1.0 until wired from calibration);
  - composites `composite_for_ball_events` (= ball_total_coverage × (1 − interp_ratio)) and
    `composite_for_physical` (= tracking_stability × homography_conf).
- **`features.py`** — the `reliability` feature (deps: `ball`, `track`). In `DEFAULT_FEATURES`,
  so **every run auto-emits a per-stat confidence**. Fails cleanly if upstream ball/track are missing.

## How to use
```python
from voetlab.pipeline.default import run
res = run("football-1.mp4", max_frames=500)
res.value["data"]["reliability"]
# {"ball_coverage": 0.18, "interpolation_ratio": 0.82, "tracking_stability": 0.86, ...}
```
Surface each number next to its stat (e.g. a badge: "possession 54% · confidence 0.18").

## When to use
After the pipeline run — consumes `ball` + `track` feature outputs and the run's `total_frames`.

## Quality & limitations — READ `reliability.py` header
- GOOD: deterministic, transparent (every input is a real signal).
- WEAK: `tracking_stability` is a **proxy** (unique-ID count vs ~22 expected) — a true IDF1/
  ID-switch metric needs ground truth; upgrade when a tracking benchmark is added.
- `homography_conf` is hardcoded 1.0 until calibration feeds it a real confidence.

## Tests
`tests/test_reliability.py` — asserts the honest ~18% ball coverage, the interpolation ratio,
fragmentation flagging, and that composites propagate correctly; `tests/test_reliability_feature.py`
covers the feature wrapper.

## Not here yet (planned)
- Wire a real `homography_conf` from the calibrate feature's solver loss / reprojection error.
- Per-stat granularity (today it's per-category); tracking ground-truth benchmark.

## Original reference
Built fresh — the voetlab product moat.
