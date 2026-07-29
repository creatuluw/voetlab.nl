"""T13 — mplsoccer chart adapters (dashboard chart engine).

Thin adapters that turn voetlab analytics output into matplotlib ``Figure`` objects via
mplsoccer — no UI. A webapp consumes these later. Coordinates are in the mplsoccer
``pitch_type`` system (default ``statsbomb``: x 0-120, y 0-80).

Quality & when to use
- GOOD: production-grade pitch plots (mplsoccer 1.7, MIT); returns plain Figures (render to
  PNG/SVG/HTML anywhere).
- WEAK: stats assume metric/pitch coords already exist — needs calibration (T4) for real
  footage; radar needs percentile/normalized params.
- When: after a pipeline run; pass the ``stats``/``events`` outputs to these adapters.
"""
from __future__ import annotations

from collections import Counter

import matplotlib

matplotlib.use("Agg")  # headless: build Figures without a display
import matplotlib.pyplot as plt  # noqa: E402
from mplsoccer import Pitch, Radar  # noqa: E402


def heatmap(positions, pitch_type: str = "statsbomb"):
    """Density heatmap of (x, y) positions. Returns a matplotlib Figure."""
    pitch = Pitch(pitch_type=pitch_type)
    fig, ax = pitch.draw()
    if positions:
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        pitch.hexbin(xs, ys, ax=ax, cmap="YlOrRd")
    return fig


def pass_network(avg_positions: dict, passes, pitch_type: str = "statsbomb"):
    """Pass network: nodes = avg positions {id:(x,y)}, edges = pass counts [(from,to),...]."""
    pitch = Pitch(pitch_type=pitch_type)
    fig, ax = pitch.draw()
    counts = Counter((p[0], p[1]) for p in passes)
    for (a, b), n in counts.items():
        if a in avg_positions and b in avg_positions:
            ax.plot([avg_positions[a][0], avg_positions[b][0]],
                    [avg_positions[a][1], avg_positions[b][1]],
                    color="gray", alpha=min(1.0, 0.2 + 0.1 * n), lw=1 + 0.5 * n, zorder=1)
    if avg_positions:
        xs = [p[0] for p in avg_positions.values()]
        ys = [p[1] for p in avg_positions.values()]
        ax.scatter(xs, ys, s=200, color="red", zorder=2)
    return fig


def radar(params, values, low, high):
    """Player radar: params (labels), values, low/high (per-param range). Returns a Figure."""
    r = Radar(params=params, min_range=list(low), max_range=list(high))
    fig, ax = r.setup_axis()
    r.draw_circles(ax=ax)
    r.draw_radar(values, ax=ax)
    r.draw_range_labels(ax=ax)
    r.draw_param_labels(ax=ax)
    return fig
