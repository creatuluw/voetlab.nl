"""P3 — ball trajectory (linear interpolation).

Consumes the ``detect`` feature's ball boxes and fills gaps between sparse detections
(linear interp; interpolated points are marked ``confidence=0.0``). Registered as feature
``"ball"`` (deps: ``["detect"]``). Downstream ``events`` reads it via ``state.get("ball")``.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  track_ball() linearly interpolates between sparse ball detections.
# Does:  a ball box (or None) for EVERY frame (feature "ball"); interpolated points are
#        marked confidence=0.0 so downstream can tell synthetic from real.
# GOOD:  fills short gaps so ball-dependent features have a position on most frames.
# WEAK:  LINEAR fill — wrong for curves/bounces/deflections; corrupts possession near gap
#        edges. Coverage is bounded by detect() ball recall (~18% real).
# When:  feature "ball", after "detect". Never fails (absent ball → coverage 0).
# Upgrade: T6 — Kalman constant-velocity trajectory (same output contract).

from __future__ import annotations

from voetlab.core.result import Result
from voetlab.detection.detect import BALL
from voetlab.pipeline.registry import feature
from voetlab.pipeline.runner import PipelineState


def _as_box(b: dict) -> dict:
    return {"x1": b["x1"], "y1": b["y1"], "x2": b["x2"], "y2": b["y2"], "confidence": b["confidence"]}


def _interp(a: dict, b: dict, t: float) -> dict:
    return {
        "x1": a["x1"] + t * (b["x1"] - a["x1"]),
        "y1": a["y1"] + t * (b["y1"] - a["y1"]),
        "x2": a["x2"] + t * (b["x2"] - a["x2"]),
        "y2": a["y2"] + t * (b["y2"] - a["y2"]),
        "confidence": 0.0,  # marks this as interpolated (synthetic)
    }


def track_ball(detections_value, *, total_frames: int | None = None, max_gap: int = 100) -> Result:
    """Build a per-frame ball box dict (or None) across ``total_frames``.

    Returns ``Result(value={"frames": {frame_no: ball_box|None}})`` with ``meta`` coverage.
    Never fails — an absent ball is a degraded-but-valid result (coverage 0).
    """
    frames_in = detections_value.get("frames", {}) if isinstance(detections_value, dict) else {}

    # highest-confidence ball per detected frame
    detected: dict[int, dict] = {}
    for f, boxes in frames_in.items():
        balls = [b for b in boxes if b.get("class") == BALL]
        if balls:
            detected[f] = _as_box(max(balls, key=lambda x: x["confidence"]))

    if total_frames is None:
        total_frames = max(frames_in) if frames_in else 0
    total_frames = max(0, int(total_frames))

    out: dict[int, dict | None] = {f: None for f in range(1, total_frames + 1)}
    for f, b in detected.items():
        if 1 <= f <= total_frames:
            out[f] = b

    if len(detected) >= 2:
        for a, b in zip(sorted(detected), sorted(detected)[1:]):
            gap = b - a
            if gap <= 1 or gap > max_gap:
                continue
            ba, bb = detected[a], detected[b]
            for f in range(a + 1, b):
                out[f] = _interp(ba, bb, (f - a) / gap)

    total_ball = sum(1 for v in out.values() if v is not None)
    coverage = (total_ball / total_frames) if total_frames else 0.0
    return Result.Ok(
        {"frames": out},
        feature="ball",
        detected=len(detected),
        coverage=round(coverage, 4),
    )


@feature("ball", deps=["detect"])
def _ball_feature(state: PipelineState) -> Result:
    # Prefer the specialist high-recall ball detector (detect_ball) when it ran; fall back to
    # the generic detect's class-32 boxes.
    det = state.get("detect_ball") or state.get("detect")
    if not det:
        return Result.Fail("upstream detect missing", feature="ball")
    meta = state.meta or {}
    if meta.get("ball_method") == "kalman":  # T6 upgrade: Kalman trajectory
        from voetlab.tracking.ball_trajectory import track_ball_kalman
        return track_ball_kalman(det, total_frames=meta.get("total_frames"))
    return track_ball(det, total_frames=meta.get("total_frames"), max_gap=meta.get("max_gap", 100))
