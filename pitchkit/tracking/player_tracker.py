"""P2 — player tracking (ByteTrack) over detection boxes.

Consumes the ``detect`` feature's output; emits per-frame person tracks with stable
``track_id``s. Registered as feature ``"track"`` (deps: ``["detect"]``). Downstream
features (teams, events, stats) read it via ``state.get("track")``.

Ported from ``src/agents/vision/vision_agent.py`` (tracking half).
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  track_players() runs ByteTrack over the detect() person boxes.
# Does:  assigns stable track_ids across frames (feature "track"); consumes "detect".
# GOOD:  fast; stable IDs while players stay in frame.
# WEAK:  sv.ByteTrack is DEPRECATED (supervision 0.28+, removed in 0.30) and has NO
#        camera-motion compensation or ReID → ID FRAGMENTATION under broadcast pan/zoom
#        and on re-entry; per-player physical stats get split across IDs (undercounted).
# When:  feature "track", after "detect"; set fps via state.meta.
# Upgrade: T9 — BoT-SORT + CMC (sparseOptFlow) + optional ReID via a tracker_factory.

from __future__ import annotations

from typing import Any

import numpy as np

from pitchkit.core.result import Result
from pitchkit.detection.detect import PERSON
from pitchkit.pipeline.registry import feature
from pitchkit.pipeline.runner import PipelineState


def _person_detections(person_boxes: list[dict]):
    """Build a supervision Detections from person box dicts (empty-safe)."""
    import supervision as sv

    if not person_boxes:
        return sv.Detections(
            xyxy=np.zeros((0, 4), dtype=float),
            confidence=np.zeros((0,), dtype=float),
            class_id=np.zeros((0,), dtype=int),
        )
    xyxy = np.array([[b["x1"], b["y1"], b["x2"], b["y2"]] for b in person_boxes], dtype=float)
    conf = np.array([b["confidence"] for b in person_boxes], dtype=float)
    cls = np.full((len(person_boxes),), PERSON, dtype=int)
    return sv.Detections(xyxy=xyxy, confidence=conf, class_id=cls)


def track_players(
    detections_value,
    *,
    fps: int = 25,
    track_activation_threshold: float = 0.5,
    lost_track_buffer: int = 60,
    minimum_matching_threshold: float = 0.8,
) -> Result:
    """Track persons across frames.

    Args:
        detections_value: ``detect`` output ``{"frames": {frame_no: [box_dicts]}}``.

    Returns:
        ``Result(value={"frames": {frame_no: [{track_id, x1,y1,x2,y2,confidence}]}})``.
    """
    import supervision as sv

    frames_in = detections_value.get("frames", {}) if isinstance(detections_value, dict) else {}
    if not frames_in:
        return Result.Fail("no frames to track", feature="track")

    tracker = sv.ByteTrack(
        track_activation_threshold=track_activation_threshold,
        lost_track_buffer=lost_track_buffer,
        minimum_matching_threshold=minimum_matching_threshold,
        frame_rate=fps,
    )

    out: dict[int, list[dict]] = {}
    for f in sorted(frames_in):
        persons = [b for b in frames_in[f] if b.get("class") == PERSON]
        tracked = tracker.update_with_detections(_person_detections(persons))
        lst = []
        tids = getattr(tracked, "tracker_id", None)
        if tids is not None and len(tracked) > 0:
            for i, tid in enumerate(tids):
                x1, y1, x2, y2 = tracked.xyxy[i]
                lst.append(
                    {
                        "track_id": int(tid),
                        "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                        "confidence": round(float(tracked.confidence[i]), 3),
                    }
                )
        out[f] = lst

    return Result.Ok({"frames": out}, feature="track", frames=len(out))


@feature("track", deps=["detect"])
def _track_feature(state: PipelineState) -> Result:
    det = state.get("detect")
    if not det:
        return Result.Fail("upstream detect missing", feature="track")
    meta = state.meta or {}
    return track_players(det, fps=meta.get("fps", 25))
