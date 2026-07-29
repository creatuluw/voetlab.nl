# pitchkit/tracking — player/ball tracking + team classification + roles

## What's here
- **`player_tracker.py`** — `track_players(detections) -> Result({"frames": {f: [{track_id, x1..y2, confidence}]}})`.
  ByteTrack over persons. Feature **`"track"`** (deps: `["detect"]`).
- **`ball_tracker.py`** — `track_ball(detections, total_frames) -> Result({"frames": {f: ball_box|None}})`.
  Linear interpolation; synthetic points marked `confidence=0.0`. Feature **`"ball"`** (deps: `["detect"]`).
- **`ball_trajectory.py`** — **T6** constant-velocity Kalman (pure numpy): ball box on ~every frame
  from first detection. Feature **`"ball"`** (deps: `["detect"]`) when `meta={"ball_method": "kalman"}`.
- **`team_classifier.py`** — `classify_teams(video, tracks) -> Result({"teams": {track_id: "A"|"B"}})`.
  KMeans k=2 on median HSV torso color (**T1** circular hue, **T2** per-track majority vote).
  Feature **`"teams"`** (deps: `["track"]`).
- **`role_filter.py`** — **T3** `classify_roles(tracks) -> Result({"roles": {track_id: "player"|"gk"|"referee"}})`.
  Pure bbox-centroid heuristics (no video/ML): referee = large x-spread on many frames; gk =
  confined to the outer ~12% edge band for most frames; else player. Feature **`"roles"`** (deps: `["track"]`).

## How to use
```python
from pitchkit.pipeline.default import run_feature
run_feature("track", video, meta={"fps": 25})
run_feature("ball", video, meta={"total_frames": 1806, "ball_method": "kalman"})
run_feature("teams", video, meta={"sample_frames": 100})   # needs the VIDEO (reads frames)
run_feature("roles", video, meta={"width": 1920})           # pure geometry; width sets the bands
```

## When to use
After `"track"`. `"roles"` → exclude GKs/referees before `"teams"` clustering and possession
logic (downstream consumer, not yet wired into `classify_teams`); `"teams"` → team labels
(must read source frames for jersey color).

## Quality & limitations — **READ each file's header comment**
- `player_tracker`: `sv.ByteTrack` is **DEPRECATED** (supervision 0.28+); no CMC/ReID →
  **ID fragmentation** under pan/zoom. Upgrade **T9** (BoT-SORT + CMC).
- `ball_tracker`: **LINEAR** interpolation — wrong for curves/bounces. **T6** Kalman landed;
  linear remains default until Kalman is promoted.
- `team_classifier`: **T1/T2** landed (circular hue / per-track majority vote). **T3** role
  filter now exists here but is NOT yet consumed to drop GKs/refs before k=2.
- `role_filter`: geometry-only; **ID fragmentation** (ByteTrack) can give a re-appearing keeper
  a huge spread → misread as referee. Upgrade: fuse with teams HSV kit color + a ReID signal.

## Tests
`tests/` — `test_player_tracker.py`, `test_ball_tracker.py`, `test_ball_trajectory.py`,
`test_team_classifier.py`, `test_team_circular.py`, `test_team_stabilizer.py`,
`test_role_filter.py` (all synthetic data; no footage needed for unit tests).

## Not here yet (planned)
T9 BoT-SORT factory (via ultralytics `model.track(tracker="botsort.yaml")` — not `sv.BotSort`) ·
wire `roles` into `classify_teams` so GKs/refs are excluded before the k=2 split.

## Original reference
Ported from `src/agents/vision/vision_agent.py` (tracking) + `src/utils/ball_interpolation.py`
+ `src/utils/team_classifier.py`.
