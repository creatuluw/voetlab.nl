"""T11/T12 feature wrappers — read pixel tracks + meta H, convert to metric, compute tactics.

These register ``pitch_control`` and ``voronoi`` as pipeline features (deps ["track"]) that
activate when a homography H is supplied in ``state.meta`` (i.e. once calibration/keypoint
detection is wired). Without H they return a clear Fail rather than silently producing junk.
"""
from __future__ import annotations

import math

from pitchkit.calibration.metric import tracks_to_metric
from pitchkit.core.result import Result
from pitchkit.pipeline.registry import feature
from pitchkit.pipeline.runner import PipelineState
from pitchkit.tactics.pitch_control import compute_pitch_control
from pitchkit.tactics.voronoi import dominant_regions


def _metric_players(state: PipelineState):
    track = state.get("track")
    H = (state.meta or {}).get("H")
    if not track or H is None:
        return None
    teams = (state.get("teams") or {}).get("teams") or {}
    metric = tracks_to_metric(track, H, teams)
    return metric


@feature("voronoi", deps=["track"])
def _voronoi_feature(state: PipelineState) -> Result:
    metric = _metric_players(state)
    if metric is None:
        return Result.Fail("voronoi needs track + meta H (calibration)", feature="voronoi")
    players = [{"x": p["x_m"], "y": p["y_m"], "team": p.get("team") or "A"}
               for pl in metric["frames"].values() for p in pl]
    if not players:
        return Result.Fail("no metric players", feature="voronoi")
    return Result.Ok(dominant_regions(players), feature="voronoi", n_players=len(players))


@feature("pitch_control", deps=["track"])
def _pitch_control_feature(state: PipelineState) -> Result:
    """Pitch control for the LAST frame (velocity estimated by finite difference of metric pos)."""
    metric = _metric_players(state)
    if metric is None:
        return Result.Fail("pitch_control needs track + meta H (calibration)", feature="pitch_control")
    frames = sorted(metric["frames"])
    if len(frames) < 2:
        return Result.Fail("need >=2 frames to estimate velocity", feature="pitch_control")
    f0, f1 = frames[-2], frames[-1]
    dt = f1 - f0
    prev = {p["track_id"]: (p["x_m"], p["y_m"]) for p in metric["frames"][f0]}
    players = []
    for p in metric["frames"][f1]:
        px, py = prev.get(p["track_id"], (p["x_m"], p["y_m"]))
        vx = (p["x_m"] - px) / dt if dt else 0.0
        vy = (p["y_m"] - py) / dt if dt else 0.0
        players.append({"x": p["x_m"], "y": p["y_m"], "vx": vx, "vy": vy, "team": p.get("team") or "A"})
    ball = (state.get("ball") or {}).get("frames", {}) if False else None  # ball_xy optional
    surface = compute_pitch_control(players, ball_xy=(52.5, 34.0))
    return Result.Ok({"shape": list(surface.shape), "mean_team_a": float(surface.mean())},
                     feature="pitch_control", n_players=len(players))
