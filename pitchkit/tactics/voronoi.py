"""T12 — Voronoi / dominant-region territory (metric pitch).

Tessellates the metric pitch (metres) into nearest-player regions and sums each
team's *dominant area* — a territory-dominance measure. NOT registered as a
``@feature``: it needs metric-space player positions (from calibration T4),
which are not yet wired into the pipeline. Pure function for now; unit-testable
with synthetic positions.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  dominant_regions() rasterizes the pitch on a step-m grid and assigns each
#        cell to its NEAREST player (scipy cKDTree); team_area_ratio() = A/(A+B).
# Does:  territory dominance in m² per team — "who owns the pitch".
# GOOD:  instant, deterministic, model-free — any metric player positions work.
# WEAK:  pure distance tessellation — ignores player velocity/closing speed, so it
#        is NOT true pitch *control* (that is T11); nearest-player only.
# When:  once you have metric (x, y) positions per player (calibration applied).
#        Pass synthetic positions in tests; never feed pixel coords.

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def dominant_regions(
    players: list[dict],
    pitch_m: tuple[float, float] = (105.0, 68.0),
    step: float = 1.0,
) -> dict:
    """Return each team's dominant pitch area in m².

    ``players`` is a list of ``{"x": m, "y": m, "team": "A"|"B"}`` in metric
    pitch coordinates. The pitch is rasterized on a ``step``-metre grid; each
    cell is assigned to its NEAREST player (scipy ``cKDTree``) and that cell's
    area (``step * step``) is credited to that player's team.

    Returns ``{"areas_m2": {team: float}, "total_m2": float}`` where
    ``total_m2`` ≈ ``pitch_m[0] * pitch_m[1]`` (raster rounding aside).
    """
    cell_area = step * step
    # cell centres spanning each dimension (default step=1 → one cell per m²)
    xs = np.arange(step / 2.0, pitch_m[0], step)
    ys = np.arange(step / 2.0, pitch_m[1], step)
    gx, gy = np.meshgrid(xs, ys)
    centres = np.column_stack([gx.ravel(), gy.ravel()])
    total_m2 = float(len(centres) * cell_area)

    if not players:
        return {"areas_m2": {}, "total_m2": total_m2}

    pts = np.asarray([[p["x"], p["y"]] for p in players], dtype=float)
    teams = np.asarray([p["team"] for p in players])
    tree = cKDTree(pts)
    nearest = tree.query(centres, k=1)[1].astype(int)  # nearest player index per cell

    areas_m2: dict[str, float] = {}
    for ni, count in zip(*np.unique(nearest, return_counts=True)):
        team = str(teams[ni])  # np.unique groups by PLAYER index → sum across same-team players
        areas_m2[team] = areas_m2.get(team, 0.0) + float(count) * cell_area
    return {"areas_m2": areas_m2, "total_m2": total_m2}


def team_area_ratio(
    players: list[dict],
    pitch_m: tuple[float, float] = (105.0, 68.0),
    step: float = 1.0,
) -> float:
    """Return Team A's share of total dominant area, ``A / (A + B)``."""
    res = dominant_regions(players, pitch_m=pitch_m, step=step)
    a = res["areas_m2"].get("A", 0.0)
    b = res["areas_m2"].get("B", 0.0)
    denom = a + b
    return a / denom if denom > 0 else 0.0
