# pitchkit/viz — mplsoccer chart adapters (dashboard chart engine)

Thin adapters that turn pitchkit analytics output into matplotlib `Figure` objects via
**mplsoccer** — no UI. A webapp consumes these later. Headless (`matplotlib.use("Agg")`) so
figures build without a display.

## What's here
- **`charts.py`** — adapters returning `matplotlib.figure.Figure`:
  - `heatmap(positions, pitch_type="statsbomb")` — density hexbin of `(x, y)` positions.
  - `pass_network(avg_positions, passes, pitch_type="statsbomb")` — nodes = avg positions
    `{id: (x, y)}`, edges = pass counts `[(from, to), ...]` (line weight/alpha scale with count).
  - `radar(params, values, low, high)` — player radar via `mplsoccer.Radar`.
- Coordinates are in the mplsoccer `pitch_type` system (default `statsbomb`: x 0–120, y 0–80).

## How to use
```python
from pitchkit.viz.charts import heatmap, pass_network, radar
fig1 = heatmap([(60, 40), (70, 40), (60, 40), (65, 42)])
fig2 = pass_network({1: (40, 30), 2: (60, 30), 3: (50, 50)}, [(1, 2), (1, 2), (3, 1)])
fig3 = radar(["Speed", "Pass", "Shot"], [5, 7, 3], [0, 0, 0], [10, 10, 10])
fig1.savefig("hm.png")   # render to PNG/SVG/HTML anywhere
```

## When to use
After a pipeline run — pass `stats`/`events` outputs (in mplsoccer coords) to the adapters.
For real footage this needs **calibration (T4)** so positions are on the pitch, not in pixels.

## Quality & limitations — READ `charts.py` header
- GOOD: production-grade pitch plots (mplsoccer 1.7, MIT); plain Figures render anywhere.
- WEAK: stats assume metric/pitch coords already exist; `radar` needs percentile/normalized params.

## Tests
`tests/test_charts.py` — each adapter returns a `matplotlib.figure.Figure` (headless).

## Not here yet (planned)
- Shot map + pizza/radar-from-percentiles.
- A coord-normalization adapter so pipeline pixel/metre output maps straight into `pitch_type`.

## Original reference
None in `src/`. Built fresh — verified lib: mplsoccer.
