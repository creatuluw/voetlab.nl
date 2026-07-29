"""P6 — physical + aggregate stats.

Consumes ``track`` + ``teams`` + ``events``. Registered as feature ``"stats"``
(deps: ``["track", "teams", "events"]``). Distances/speeds are in PIXELS for now
(meters = T4/T5 homography, later).
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  compute_stats() — per-player + per-team physical & event aggregates.
# Does:  distance/speed/sprints + passes/tackles/possession counts (feature "stats");
#        consumes track+teams+events.
# GOOD:  deterministic; full per-player + per-team summary.
# WEAK:  distances/speeds are in PIXELS (only RELATIVE comparisons valid until T4/T5);
#        sprint threshold is a pixel speed; inherits ID fragmentation from tracking.
# When:  feature "stats" (terminal output). Units become meters/km·h after homography.
# Upgrade: T4/T5 metric stats + Savitzky–Golay smoothing; T9 fixes ID fragmentation.

from __future__ import annotations

import math

from voetlab.core.result import Result
from voetlab.pipeline.registry import feature
from voetlab.pipeline.runner import PipelineState


def _empty_team() -> dict:
    return {"total_passes": 0, "total_tackles": 0, "total_interceptions": 0,
            "possession_frames": 0, "avg_distance_px": 0.0}


def _empty_player(tid: int, team) -> dict:
    return {"track_id": tid, "team": team, "passes_made": 0, "passes_received": 0,
            "tackles_made": 0, "tackles_suffered": 0, "interceptions_made": 0,
            "interceptions_suffered": 0, "possession_frames": 0,
            "distance_px": 0.0, "top_speed_px_s": 0.0, "sprint_count": 0,
            "distance_m": 0.0, "top_speed_km_h": 0.0}


def compute_stats(tracks_value, teams_value, events_value, *, fps: int = 25,
                  sprint_threshold: float = 150.0, H=None) -> Result:
    tframes = tracks_value.get("frames", {}) if isinstance(tracks_value, dict) else {}
    teams = teams_value.get("teams", {}) if isinstance(teams_value, dict) else (teams_value or {})
    ev = events_value if isinstance(events_value, dict) else {}

    # group track boxes by id, sorted by frame
    by_track: dict[int, list[tuple[int, dict]]] = {}
    for f, pl in tframes.items():
        for p in pl:
            by_track.setdefault(p["track_id"], []).append((f, p))

    warp = None
    if H is not None:
        from voetlab.calibration.homography import warp_points
        warp = lambda pts: warp_points(pts, H)

    players: dict[int, dict] = {}
    for tid, seq in by_track.items():
        seq.sort(key=lambda fs: fs[0])
        team = teams.get(tid)
        st = _empty_player(tid, team)
        dist = max_speed = 0.0
        met_dist = met_max = 0.0
        sprints = 0
        in_sprint = False
        prev = mprev = None
        for f, p in seq:
            x, y = (p["x1"] + p["x2"]) / 2.0, p["y2"]
            mx = my = None
            if warp is not None:
                mx, my = (float(v) for v in warp([(x, y)])[0])
            if prev is not None:
                pf, px, py = prev
                gap = f - pf
                if gap <= 5:
                    d = math.hypot(x - px, y - py)
                    dist += d
                    speed = (d / gap) * fps
                    max_speed = max(max_speed, speed)
                    if speed >= sprint_threshold:
                        if not in_sprint:
                            sprints += 1
                        in_sprint = True
                    else:
                        in_sprint = False
                    if warp is not None and mprev is not None:
                        md = math.hypot(mx - mprev[1], my - mprev[2])
                        met_dist += md
                        met_max = max(met_max, (md / gap) * fps)
                else:
                    in_sprint = False
            prev = (f, x, y)
            if warp is not None:
                mprev = (f, mx, my)
        st["distance_px"] = round(dist, 1)
        st["top_speed_px_s"] = round(max_speed, 1)
        st["sprint_count"] = sprints
        if warp is not None:
            st["distance_m"] = round(met_dist, 2)
            st["top_speed_km_h"] = round(met_max * 3.6, 1)
        players[tid] = st

    team_stats = {"A": _empty_team(), "B": _empty_team()}

    # possession
    for entry in ev.get("possession", []):
        tid, team = entry["track_id"], entry.get("team")
        if tid in players:
            players[tid]["possession_frames"] += 1
        if team in team_stats:
            team_stats[team]["possession_frames"] += 1

    def _gid(d, key):
        return players.get(d[key])

    for p in ev.get("passes", []):
        a, b = _gid(p, "from_track_id"), _gid(p, "to_track_id")
        if a:
            a["passes_made"] += 1
        if b:
            b["passes_received"] += 1
        if p.get("from_team") in team_stats:
            team_stats[p["from_team"]]["total_passes"] += 1

    for t in ev.get("tackles", []):
        a, b = _gid(t, "from_track_id"), _gid(t, "to_track_id")
        if a:
            a["tackles_suffered"] += 1
        if b:
            b["tackles_made"] += 1
        if t.get("to_team") in team_stats:
            team_stats[t["to_team"]]["total_tackles"] += 1

    for i in ev.get("interceptions", []):
        a, b = _gid(i, "from_track_id"), _gid(i, "to_track_id")
        if a:
            a["interceptions_suffered"] += 1
        if b:
            b["interceptions_made"] += 1
        if i.get("to_team") in team_stats:
            team_stats[i["to_team"]]["total_interceptions"] += 1

    moved = [p for p in players.values() if p["distance_px"] > 0]
    for name, ts in team_stats.items():
        tm = [p for p in moved if p["team"] == name]
        if tm:
            ts["avg_distance_px"] = round(sum(p["distance_px"] for p in tm) / len(tm), 1)

    return Result.Ok({"players": players, "teams": team_stats}, feature="stats",
                     n_players=len(players))


@feature("stats", deps=["track", "teams", "events"])
def _stats_feature(state: PipelineState) -> Result:
    tracks, teams, events = state.get("track"), state.get("teams"), state.get("events")
    if not tracks:
        return Result.Fail("upstream track missing", feature="stats")
    meta = state.meta or {}
    return compute_stats(tracks, teams or {"teams": {}}, events or {},
                          fps=meta.get("fps", 25), H=meta.get("H"))
