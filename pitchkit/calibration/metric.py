"""T4/T5/T11/T12 bridge — convert pixel tracks to metric-space via a homography.

The missing link so tactics (pitch control, Voronoi) and metric stats can consume real
coordinates: warp each player's feet through H, per frame.
"""
from __future__ import annotations

from pitchkit.calibration.homography import warp_points


def tracks_to_metric(track_value, H, teams: dict | None = None) -> dict:
    """``track`` feature output + homography H → {"frames": {f: [{track_id, x_m, y_m, team}]}}."""
    tframes = track_value.get("frames", {}) if isinstance(track_value, dict) else {}
    teams = teams or {}
    out: dict[int, list[dict]] = {}
    for f, pl in tframes.items():
        if not pl:
            continue
        feet = [((p["x1"] + p["x2"]) / 2.0, p["y2"]) for p in pl]
        m = warp_points(feet, H)
        out[f] = [
            {"track_id": p["track_id"], "x_m": float(m[i][0]), "y_m": float(m[i][1]),
             "team": teams.get(p["track_id"])}
            for i, p in enumerate(pl)
        ]
    return {"frames": out}
