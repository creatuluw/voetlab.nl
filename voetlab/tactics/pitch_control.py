"""T11 — Spearman pitch-control surface (probability team A controls each pitch point).

Simplified model: for every grid cell each player contributes a Gaussian-like
'influence' over their **time-to-reach** the cell (closer / faster players dominate);
team-A control probability = sumA / (sumA + sumB).

NOT registered as a pipeline feature yet — the pipeline doesn't produce metric-space
velocity (needs calibration T4 + smoothed velocity T5). It is a pure numpy function,
unit-testable with synthetic metric positions, mirroring the structure of detection/detect.py.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  compute_pitch_control() — team-A pitch-control probability surface.
# Does:  per grid cell, sums Gaussian 'reach' influences per team; P(A) = sumA / (sumA+sumB).
# GOOD:  pure numpy, vectorised over the whole pitch; clean spatial-dominance signal.
# WEAK:  SIMPLIFIED Spearman — reach = Gaussian falloff over time-to-reach (speed + reaction);
#        no acceleration model, no ball-arrival gate, stationary players floored to a walk.
# When:  NOT yet a pipeline feature (needs metric-space velocity from T4/T5). Pure function for
#        later wiring; unit-testable with synthetic metric positions.
# Upgrade: full Spearman — exponential intercept PDF, ball-travel-time gate, acceleration.

from __future__ import annotations

import numpy as np

# Simplified-Spearman constants — calibration knobs for the fuller model.
_REACTION_TIME = 0.7  # s  — sensing + braking delay before a player can move (Spearman-ish).
_V_MAX = 8.0          # m/s — sprint cap; faster players reach sooner and dominate.
_V_MIN = 2.0          # m/s — walk floor so stationary players keep a baseline reach.
_SIGMA = 1.0          # s  — Gaussian width over time-to-reach (~pitch-control locality).


def compute_pitch_control(players, ball_xy, pitch_m=(105.0, 68.0), grid_step=1.0) -> np.ndarray:
    """Return a 2-D pitch-control surface: P(team A controls) per grid cell, in [0, 1].

    Shape ~ (pitch_height / step, pitch_width / step) — (68, 105) for a default 105x68 m
    pitch at 1 m resolution; ``surface[y_idx, x_idx]`` is the point ``(x, y)`` in metres.

    ``players``: list of dicts ``{"x", "y", "vx", "vy", "team": "A"|"B"}`` (metres / m·s⁻¹).
    ``ball_xy``: ``(x_m, y_m)`` — reserved for the ball-arrival-time gate of the full model;
                 the simplified reach here is player-only.
    """
    width_m, height_m = pitch_m
    # Grid axes: rows = y, cols = x  →  shape ~ (height/step, width/step).
    gx = np.arange(0.0, width_m, grid_step)
    gy = np.arange(0.0, height_m, grid_step)
    gx_grid, gy_grid = np.meshgrid(gx, gy)  # each shape (len(gy), len(gx))

    sum_a = np.zeros_like(gx_grid)
    sum_b = np.zeros_like(gx_grid)

    for p in players:
        # Time-to-reach = distance / effective run speed + reaction delay.
        dist = np.hypot(gx_grid - p["x"], gy_grid - p["y"])
        speed = (p["vx"] * p["vx"] + p["vy"] * p["vy"]) ** 0.5
        v_run = min(max(speed, _V_MIN), _V_MAX)
        tti = dist / v_run + _REACTION_TIME
        influence = np.exp(-(tti * tti) / (2.0 * _SIGMA * _SIGMA))
        if p["team"] == "A":
            sum_a += influence
        else:
            sum_b += influence

    denom = sum_a + sum_b
    surface = np.full_like(gx_grid, 0.5)           # neutral where no one has reach
    nz = denom > 0.0
    surface[nz] = sum_a[nz] / denom[nz]
    return surface
