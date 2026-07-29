# pitchkit/tactics — pitch control & Voronoi (pure functions, not yet `@feature`s)

## Status
Both tactical modules **landed as pure numpy functions** with synthetic tests green.
They are NOT registered as pipeline `@feature`s yet — that wiring needs metric-space
coords/velocity from **calibration (T4)** + smoothed velocity (**T5**).

## Modules
- **`pitch_control.py` (T11)** — Spearman pitch-control surface. `compute_pitch_control(players, ball_xy)`
  returns a 2-D P(team A controls) field in [0,1]: per grid cell, each player adds a Gaussian 'reach'
  influence over their time-to-reach (speed + reaction); `P(A) = sumA / (sumA+sumB)`. Simplified model
  (no acceleration, no ball-arrival gate); mirrors `detection/detect.py` structure.
- **`voronoi.py` (T12)** — dominant-region tessellation: `dominant_regions` / `team_area_ratio`,
  pure `cKDTree` rasterization.

## Dependencies
Both need **metric-space** player positions + velocities → depend on **T4** (homography) and **T5**
(smoothed velocity). The pure functions are unit-testable today with synthetic metric positions.

## When it becomes a `@feature`
After T4/T5 land metric coords + velocity in the pipeline. These are PREDA's tactical
differentiators (space creation, passing-lane value).

## Original reference
None in `src/`. See `research_repos_features/findings_tactical.md`.
