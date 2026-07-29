"""P5/T3 — referee/goalkeeper role filter (pure bbox heuristics).

Consumes the ``track`` feature's person tracks; assigns each ``track_id`` a role of
``"player"``, ``"gk"``, or ``"referee"``. Registered as feature ``"roles"``
(deps: ``["track"]``). Downstream features (teams, events) can use it to exclude GKs
and referees from team clustering and possession logic.

The heuristics operate purely on bounding-box centroids — no video frames, no model —
so this node is deterministic, cost-free, and trivially unit-testable.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  classify_roles() — pure centroid heuristics over per-frame track boxes.
# Does:  maps each track_id → "player"|"gk"|"referee" (feature "roles"); consumes "track".
# GOOD:  cheap, deterministic, no video/ML needed; isolates the two non-outfield roles so
#        team clustering (T1/T2) and possession can exclude GKs + referees cleanly.
# WEAK:  broadcast pan/zoom + ByteTrack ID fragmentation (see player_tracker) mean centroid
#        spreads are unreliable — a GK re-appearing at the far end can get a huge spread and
#        be misread as a referee; an injured/off-pitch official may skew edge-band counts.
# When:  feature "roles", after "track"; pass width= for non-1920px footage.
# Upgrade: fuse with teams HSV (GKs wear a distinct kit color) and a persistence/ReID signal
#          once track ids are stable (T9 BoT-SORT) — role then becomes the AND of geometry + kit.

from __future__ import annotations

from typing import Any

from pitchkit.core.result import Result
from pitchkit.pipeline.registry import feature
from pitchkit.pipeline.runner import PipelineState

# --- Heuristic knobs (pure bbox geometry, calibrated for 1920px broadcast width) ---
GK_EDGE_FRAC = 0.12          # goalkeepers live within the outer ~12% of pitch width
GK_MAJORITY = 0.6            # ...for the majority of their on-screen frames
REF_SPREAD_FRAC = 0.5        # referees roam >= half the pitch width (large x-spread)
REF_MIN_FRAMES_FRAC = 0.5    # ...and are on-screen for at least half the match
DEFAULT_WIDTH = 1920


def classify_roles(tracks_value: Any, *, width: int | None = None) -> Result:
    """Assign each ``track_id`` a role from pure bounding-box centroids.

    Args:
        tracks_value: ``track`` output ``{"frames": {frame_no: [{track_id, x1,y1,x2,y2, confidence}]}}``.
        width: frame width in px (default 1920); sets the edge-band + spread thresholds.

    Heuristics (checked in order, on each track's centroid-x across the frames it appears in):

    * **referee** — x-spread (max centroid-x − min centroid-x) is a large fraction of
      ``width`` (>= ``REF_SPREAD_FRAC``) AND the track is present on many frames
      (>= ``REF_MIN_FRAMES_FRAC`` of all frames). Officials roam the whole touchline.
    * **gk** — centroid-x is confined to the left or right ~``GK_EDGE_FRAC`` edge band for
      most (>= ``GK_MAJORITY``) of its frames. Keepers stay glued to their goal.
    * **player** — everything else.

    Returns:
        ``Result(value={"roles": {track_id: "player"|"gk"|"referee"}}, feature="roles", ...)``.
    """
    frames_in = tracks_value.get("frames", {}) if isinstance(tracks_value, dict) else {}
    if not frames_in:
        return Result.Fail("no tracks to classify", feature="roles")
    if width is None:
        width = DEFAULT_WIDTH

    total_frames = len(frames_in)

    # Collect per-frame centroid-x per track_id.
    per_track: dict[int, list[float]] = {}
    for f in frames_in:
        for t in frames_in[f]:
            tid = t.get("track_id")
            if tid is None:
                continue
            cx = (t["x1"] + t["x2"]) / 2.0
            per_track.setdefault(int(tid), []).append(cx)

    edge = GK_EDGE_FRAC * width
    ref_spread = REF_SPREAD_FRAC * width
    ref_min_frames = REF_MIN_FRAMES_FRAC * total_frames

    roles: dict[int, str] = {}
    counts = {"player": 0, "gk": 0, "referee": 0}
    for tid, xs in per_track.items():
        spread = max(xs) - min(xs)
        n = len(xs)
        in_edge = sum(1 for x in xs if x <= edge or x >= width - edge)
        if spread >= ref_spread and n >= ref_min_frames:
            role = "referee"
        elif n and in_edge / n >= GK_MAJORITY:
            role = "gk"
        else:
            role = "player"
        roles[tid] = role
        counts[role] += 1

    return Result.Ok(
        {"roles": roles},
        feature="roles",
        tracks=len(roles),
        players=counts["player"],
        goalkeepers=counts["gk"],
        referees=counts["referee"],
        width=width,
    )


@feature("roles", deps=["track"])
def _roles_feature(state: PipelineState) -> Result:
    """Registered pipeline node. Reads upstream tracks via ``state.get("track")``."""
    tracks = state.get("track")
    if not tracks:
        return Result.Fail("upstream track missing", feature="roles")
    meta = state.meta or {}
    return classify_roles(tracks, width=meta.get("width"))
