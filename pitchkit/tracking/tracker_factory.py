"""T9 — tracker factory: ByteTrack (supervision) or BoT-SORT/OC-SORT (ultralytics model.track).

Why a factory: supervision 0.29 has NO ``BotSort`` and ``ByteTrack`` is deprecated, so BoT-SORT
runs via ultralytics ``model.track(tracker='botsort.yaml')`` (camera-motion compensation via
``gmc_method: sparseOptFlow`` + optional ReID). This returns the CONFIG; ``track_via_ultralytics``
runs the combined detect+track pass.

Quality & when to use
- GOOD: BoT-SORT adds CMC for broadcast pan/zoom — the main fix for ID fragmentation.
- WEAK: combines detect+track in one ultralytics call (different from the separated
  detect→sv.ByteTrack path); ReID needs a ReID encoder file. Verified: Ultralytics track docs.
- When: prefer "botsort" for broadcast; "bytetrack" preserves the current separated pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

from pitchkit.core.result import Result

# Shipped BoT-SORT config with camera-motion compensation enabled (gmc_method: sparseOptFlow).
# Ultralytics accepts an absolute path to a tracker yaml, so we point `tracker=` here.
_BOTSORT_YAML = Path(__file__).resolve().parent / "pitchkit_botsort.yaml"


def build_tracker(name: str = "botsort", *, reid: bool = False, gmc: str = "sparseOptFlow") -> dict:
    """Return a tracker config (pure). ``botsort``→ultralytics (CMC+ReID); ``bytetrack``→supervision."""
    name = (name or "botsort").lower()
    if name == "botsort":
        return {"engine": "ultralytics", "tracker": str(_BOTSORT_YAML), "gmc_method": gmc, "with_reid": bool(reid)}
    if name == "ocsort":
        return {"engine": "ultralytics", "tracker": "ocsort.yaml", "gmc_method": "none", "with_reid": False}
    if name == "bytetrack":
        return {"engine": "supervision", "tracker": "sv.ByteTrack"}
    raise ValueError(f"unknown tracker: {name!r}")


def track_via_ultralytics(
    video,
    *,
    model_path: str = "yolov8s.pt",
    tracker: Optional[str] = None,
    classes: Sequence[int] = (0,),
    conf: float = 0.3,
    max_frames: Optional[int] = None,
    model: Any = None,
) -> Result:
    """Detect+track in one pass via ultralytics ``model.track()``.

    Defaults to our shipped BoT-SORT config (CMC enabled). Returns
    ``Result(value={"frames": {f: [{track_id, x1..y2, confidence}]}})``.
    """
    from ultralytics import YOLO

    tracker = tracker or str(_BOTSORT_YAML)
    mdl = model if model is not None else YOLO(model_path)
    out: dict[int, list[dict]] = {}
    try:
        stream = mdl.track(source=video, stream=True, persist=True, tracker=tracker,
                           conf=conf, classes=list(classes))
    except Exception as exc:
        return Result.Fail(f"track inference failed: {exc}", feature="track_botsort")
    for i, r in enumerate(stream, start=1):
        boxes = getattr(r, "boxes", None)
        tids = getattr(boxes, "id", None) if boxes is not None else None
        lst = []
        if boxes is not None and tids is not None and len(boxes) > 0:
            xy = boxes.xyxy.cpu().numpy()
            ids = tids.cpu().numpy()
            cf = boxes.conf.cpu().numpy()
            for j in range(len(xy)):
                x1, y1, x2, y2 = (float(v) for v in xy[j])
                lst.append({"track_id": int(ids[j]), "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                            "confidence": round(float(cf[j]), 3)})
        out[i] = lst
        if max_frames and i >= max_frames:
            break
    if not out:
        return Result.Fail("no frames tracked", feature="track_botsort")
    return Result.Ok({"frames": out}, feature="track_botsort", frames=len(out), tracker=tracker)
