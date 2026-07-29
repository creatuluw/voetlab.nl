# pitchkit/stats — per-player + per-team physical & event aggregates (terminal stage)

## What's here
- **`stats.py`** — `compute_stats(tracks, teams, events) -> Result({"players": {...}, "teams": {...}})`.
  Distance / top-speed / sprints (**pixels**) + passes / tackles / possession counts.
  Feature **`"stats"`** (deps: `["track", "teams", "events"]`). Terminal pipeline output.

## How to use
```python
from pitchkit.pipeline.default import run
res = run("football-1.mp4", max_frames=500)
stats = res.value["data"]["stats"]
stats["players"][track_id]   # {"distance_px","top_speed_px_s","sprint_count","passes_made",...}
stats["teams"]["A"]          # {"total_passes","possession_frames","avg_distance_px",...}
```

## When to use
Terminal stage. **NOTE: units are PIXELS** — only *relative* comparisons are valid until
homography (T4/T5) converts to meters / km·h.

## Quality & limitations — **READ the `stats.py` header comment**
- Pixel units (not meters) — meaningless absolute speeds until T4/T5.
- Sprint threshold is a pixel speed; inherits ID fragmentation from tracking (one player →
  many IDs → per-player load undercounted).
- Upgrades: **T4/T5** (meters + Savitzky–Golay smoothing), **T9** (fixes fragmentation).

## Tests
`tests/test_stats.py` — synthetic moving track → distance/speed; possession aggregation.

## Not here yet (planned)
T4/T5 metric stats (m / km·h) + Savitzky–Golay smoothing; heatmaps (pixel-based today).

## Original reference
Ported from `src/agents/analytics/analytics_agent.py`.
