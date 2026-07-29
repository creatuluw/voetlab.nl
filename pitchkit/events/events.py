"""P5 — events: possession, passes, tackles, interceptions — every event frame-provenanced.

Consumes ``track`` + ``ball`` + ``teams`` features. Registered as feature ``"events"``
(deps: ``["track", "ball", "teams"]``). Every output event carries ``source_frames`` so it
can be traced back to the frame(s) it was captured from.

Ported from ``src/agents/events/events_agent.py``.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  detect_events() — possession, passes, tackles, interceptions (all frame-provenanced).
# Does:  derives events from track+ball+teams (feature "events"); EVERY event carries
#        `source_frames` so you can trace it back to the exact frame(s).
# GOOD:  deterministic, cheap; reliable possession % and pass/turnover counts WHEN the
#        ball layer is dense.
# WEAK:  distance thresholds are in PIXELS (not pitch-calibrated); event counts scale with
#        ball coverage (~18% today → undercounted); no shots/dribbles/fouls; no intent/body-part.
# When:  feature "events", after track+ball+teams. Improves automatically as ball coverage
#        (T6/T8) and homography (T4) land.
# Upgrade: T7 per-frame velocity possession; T4 metric-space thresholds.

from __future__ import annotations

import math

from pitchkit.core.provenance import attach_provenance
from pitchkit.core.result import Result
from pitchkit.pipeline.registry import feature
from pitchkit.pipeline.runner import PipelineState


def _feet(b: dict) -> tuple[float, float]:
    return ((b["x1"] + b["x2"]) / 2.0, b["y2"])


def _center(b: dict) -> tuple[float, float]:
    return ((b["x1"] + b["x2"]) / 2.0, (b["y1"] + b["y2"]) / 2.0)


def detect_events(
    tracks_value,
    ball_value,
    teams_value,
    *,
    possession_radius: float = 80.0,
    change_threshold: int = 3,
    tackle_radius: float = 80.0,
) -> Result:
    tframes = tracks_value.get("frames", {}) if isinstance(tracks_value, dict) else {}
    bframes = ball_value.get("frames", {}) if isinstance(ball_value, dict) else {}
    teams = teams_value.get("teams", {}) if isinstance(teams_value, dict) else (teams_value or {})

    # --- possession: nearest player (feet) to the ball each frame it's seen ---
    possession = []
    for f in sorted(set(tframes) | set(bframes)):
        ball = bframes.get(f)
        if not ball:
            continue
        bx, by = _center(ball)
        best, best_d = None, float("inf")
        for p in tframes.get(f, []):
            px, py = _feet(p)
            d = math.hypot(bx - px, by - py)
            if d < best_d:
                best_d, best = d, p
        if best is not None and best_d <= possession_radius:
            possession.append(
                {"frame": f, "track_id": best["track_id"], "team": teams.get(best["track_id"]),
                 "distance": round(best_d, 1)}
            )

    # --- debounced possession changes ---
    changes = []
    if len(possession) >= 2:
        cur = possession[0]["track_id"]
        cur_team = possession[0].get("team")
        cand = cand_team = None
        cnt = 0
        cstart = None
        for e in possession[1:]:
            tid, team, fr = e["track_id"], e.get("team"), e["frame"]
            if tid == cur:
                cand, cnt, cstart, cand_team = None, 0, None, None
            elif tid == cand:
                cnt += 1
                if cnt >= change_threshold:
                    changes.append({"frame": cstart, "from_track_id": cur, "to_track_id": cand,
                                    "from_team": cur_team, "to_team": cand_team})
                    cur, cur_team = cand, cand_team
                    cand, cnt, cstart, cand_team = None, 0, None, None
            else:
                cand, cand_team, cnt, cstart = tid, team, 1, fr

    # --- classify: same-team = pass; different-team = tackle (close) or interception ---
    passes, tackles, interceptions = [], [], []
    for c in changes:
        f = c["frame"]
        same_team = c["from_team"] is not None and c["from_team"] == c["to_team"]
        ev = {"frame": f, "from_track_id": c["from_track_id"], "to_track_id": c["to_track_id"],
              "from_team": c["from_team"], "to_team": c["to_team"]}
        if same_team:
            ev["type"] = "pass"
            attach_provenance(ev, source_frames=[f], kind="pass")
            passes.append(ev)
            continue
        by_id = {p["track_id"]: p for p in tframes.get(f, [])}
        a, b = by_id.get(c["from_track_id"]), by_id.get(c["to_track_id"])
        if a and b:
            d = math.hypot(_feet(a)[0] - _feet(b)[0], _feet(a)[1] - _feet(b)[1])
            if d <= tackle_radius:
                ev["type"] = "tackle"
                attach_provenance(ev, source_frames=[f], kind="tackle", distance=round(d, 1))
                tackles.append(ev)
            else:
                ev["type"] = "interception"
                attach_provenance(ev, source_frames=[f], kind="interception", distance=round(d, 1))
                interceptions.append(ev)
        else:
            ev["type"] = "interception"
            attach_provenance(ev, source_frames=[f], kind="interception", distance=None)
            interceptions.append(ev)

    return Result.Ok(
        {"possession": possession, "passes": passes, "tackles": tackles, "interceptions": interceptions},
        feature="events",
        n_possession=len(possession), n_passes=len(passes),
        n_tackles=len(tackles), n_interceptions=len(interceptions),
    )


@feature("events", deps=["track", "ball", "teams"])
def _events_feature(state: PipelineState) -> Result:
    tracks, ball, teams = state.get("track"), state.get("ball"), state.get("teams")
    if not (tracks and ball and teams):
        return Result.Fail("upstream track/ball/teams missing", feature="events")
    return detect_events(tracks, ball, teams)
