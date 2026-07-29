# voetlab/events — possession, passes, tackles, interceptions (frame-provenanced)

## What's here
- **`events.py`** — `detect_events(tracks, ball, teams) -> Result({possession, passes, tackles,
  interceptions})`. **Every event carries `source_frames`** so it traces back to the footage.
  Feature **`"events"`** (deps: `["track", "ball", "teams"]`).

## How to use
```python
from voetlab.pipeline.default import run
res = run("football-1.mp4", max_frames=200)
events = res.value["data"]["events"]
for p in events["passes"]:
    print(p["from_track_id"], "→", p["to_track_id"], "at frames", p["source_frames"])
```

## When to use
After `track` + `ball` + `teams`. To answer "which frame did this event come from?" → read
`event["source_frames"]`.

## Quality & limitations — **READ the `events.py` header comment**
- Pixel-based thresholds (`possession_radius`, `tackle_radius`) — not pitch-calibrated.
- Event counts **scale with ball coverage** (~18% today → undercounted).
- No shots / dribbles / fouls; no intent or body-part.
- Improves automatically as ball (T6/T8) and homography (T4) land. Upgrade **T7**.

## Tests
`tests/test_events.py` — synthetic scenarios assert passes/tackles + non-empty provenance.

## Not here yet (planned)
T7 velocity-based per-frame possession; shots/dribbles; (optional) deep action-spotting.
