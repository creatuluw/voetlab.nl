"""T10 — reliability signal: an honest per-stat confidence from measurable CV-quality signals.

PREDA's product moat is "a reliability signal on every number". Instead of inventing a
score, this propagates real, measurable signals (ball detection coverage, interpolation
ratio, track-ID fragmentation, homography confidence) into a 0–1 confidence per category.

Quality & when to use
- GOOD: deterministic, fully transparent (every input is a real, inspectable signal).
- WEAK: tracking_stability is a PROXY (unique-ID count vs ~22 expected) — a true IDF1/
  ID-switch metric needs ground truth; upgrade when we add a tracking benchmark.
- When: call after the pipeline run with the ball + track feature outputs. Surface each
  number alongside its stat (e.g. a badge: "possession 54% · confidence 0.18").
"""
from __future__ import annotations

from pitchkit.core.result import Result


def compute_reliability(
    ball_value,
    track_value,
    *,
    total_frames: int,
    homography_conf: float = 1.0,
    expected_players: int = 22,
) -> Result:
    """Aggregate CV-quality signals into a per-category 0–1 confidence.

    Args:
        ball_value:     ``ball`` feature output (``{"frames": {f: ball_box|None}}``).
        track_value:    ``track`` feature output (``{"frames": {f: [{track_id, ...}]}}``).
        total_frames:   number of frames analyzed.
        homography_conf: 0–1 calibration confidence (1.0 until T4 lands).
        expected_players: ~22 on-pitch; more track IDs than this ⇒ fragmentation.
    """
    bframes = ball_value.get("frames", {}) if isinstance(ball_value, dict) else {}
    tframes = track_value.get("frames", {}) if isinstance(track_value, dict) else {}
    total = max(1, int(total_frames))

    real_ball = sum(1 for b in bframes.values() if b and b.get("confidence", 0) > 0)
    any_ball = sum(1 for b in bframes.values() if b)
    interpolated = any_ball - real_ball
    ball_coverage = real_ball / total
    ball_total_coverage = any_ball / total
    interpolation_ratio = (interpolated / any_ball) if any_ball else 1.0

    ids = {p.get("track_id") for pl in tframes.values() for p in pl}
    n_tracks = len(ids)
    over = max(0.0, n_tracks - expected_players)
    tracking_stability = max(0.0, 1.0 - over / expected_players)

    # composites: effective REAL-ball density for event stats; calibration×stability for physical stats
    composite_for_ball_events = ball_total_coverage * (1.0 - interpolation_ratio)
    composite_for_physical = tracking_stability * homography_conf

    return Result.Ok(
        {
            "ball_coverage": round(ball_coverage, 4),
            "ball_total_coverage": round(ball_total_coverage, 4),
            "interpolation_ratio": round(interpolation_ratio, 4),
            "n_tracks": n_tracks,
            "tracking_stability": round(tracking_stability, 4),
            "homography_conf": homography_conf,
            "composite_for_ball_events": round(composite_for_ball_events, 4),
            "composite_for_physical": round(composite_for_physical, 4),
        },
        feature="reliability",
        expected_players=expected_players,
    )
