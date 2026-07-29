---
type: Rule
title: Per-frame pipeline stages emit throttled progress via state.progress
description: "Stages with a per-frame loop emit progress events through the optional `state.progress` callback (a `Callable[[dict], None]`, default `None`). The runner always"
tags: [pipeline, progress, web-ui, tracking]
timestamp: "2026-07-29T20:38:34.575Z"
---

# Per-frame pipeline stages emit throttled progress via state.progress

Stages with a per-frame loop emit progress events through the optional `state.progress` callback (a `Callable[[dict], None]`, default `None`). The runner always emits `{"type":"start","stage":...}` and `{"type":"stage_done","stage":...}` around every stage; per-frame stages additionally emit `{"type":"frame","stage":<name>,"currentFrame":i,"totalFrames":n}`.

Convention for the per-frame `frame` events:
- `currentFrame` is **1-indexed** (matches `detect`).
- `totalFrames` = the count the loop iterates (`len(frames)`, `meta["total_frames"]`, the `sample_frames` cap for `teams`, or the sampled-frame count for `calibrate`) — NOT the whole clip when the stage only scans a window.
- **Throttle to ~every 20 frames** (`if i % 20 == 0`) for stages over many frames so the SSE isn't flooded. `detect` is the exception: it emits every frame (it's the heaviest entry stage).
- **Always emit one final `frame` event at the loop's end** (`currentFrame == totalFrames`) so the UI bar completes — even if the throttle already fired there (idempotent duplicate is harmless) or the clip was shorter than the window.
- Guard every emit with `if state.progress:` — the callback is optional and `None` in tests/CLI, so there must be zero overhead when absent.

Stages currently emitting per-frame progress: `detect` (every frame), `detect_ball` (throttled every ~20 frames + final; the high-recall SAHI ball stage, `stage="detect_ball"` — was previously the one per-frame stage with NO callback, freezing the web UI), `calibrate` (every sampled frame), `track` (throttled), `ball` (throttled on the Kalman path; single completion on the fast linear path since it has no expensive loop), `teams` (throttled over the `sample_frames` cap). Aggregation stages (`events`, `stats`, `reliability`) have no per-frame loop and rely on `start`/`stage_done` only.

Source: `voetlab/detection/detect.py`, `voetlab/calibration/features.py`, `voetlab/tracking/player_tracker.py`, `voetlab/tracking/ball_tracker.py`, `voetlab/tracking/ball_trajectory.py`, `voetlab/tracking/team_classifier.py`.
