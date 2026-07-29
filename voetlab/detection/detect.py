"""P1 — per-frame detection (persons + ball) via YOLO.

The pipeline's entry point. Registered as feature ``"detect"``; its output lands in
``state.data["detect"]`` for downstream features (tracking, teams) to read via
``state.get("detect")``.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  detect() runs YOLO per-frame; boxes_from_result() parses; annotate() draws.
# Does:  emits per-frame person + ball boxes (feature "detect"); the pipeline entry point.
# GOOD:  person detection (COCO class 0) — high recall on broadcast footage.
# WEAK:  the BALL — COCO class 32 = baseball/tennis, NOT football → ~18% frame coverage,
#        which STARVES every ball-dependent downstream stat (possession, passes, ...).
# When:  always first in the pipeline; inject `model=` in unit tests (no weight download).
# Upgrade: T8 — football-ball model + SAHI sliced inference (same interface, no downstream change).

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

import numpy as np

from voetlab.core.result import Result
from voetlab.pipeline.registry import feature
from voetlab.pipeline.runner import PipelineState

# COCO class ids used by the default detector.
PERSON = 0
BALL = 32


def _load_model(model_path: str):
    """Lazy-load a YOLO model (kept out of the import path so the package stays light)."""
    from ultralytics import YOLO

    return YOLO(model_path)


def _frame_count(video) -> int:
    """Best-effort total frame count for progress reporting.

    Returns 0 if OpenCV is unavailable or the container can't report a count (the worker
    path sets ``max_frames`` so this fallback is rarely exercised).
    """
    try:
        import cv2

        cap = cv2.VideoCapture(video)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return n
    except Exception:
        return 0


def boxes_from_result(r) -> list[dict]:
    """Parse one ultralytics result into a list of box dicts (testable in isolation)."""
    boxes = getattr(r, "boxes", None)
    if boxes is None:
        return []
    xyxy = getattr(boxes, "xyxy", None)
    if xyxy is None or len(xyxy) == 0:
        return []
    xy = xyxy.cpu().numpy() if hasattr(xyxy, "cpu") else np.asarray(xyxy)
    cls = boxes.cls.cpu().numpy() if hasattr(boxes.cls, "cpu") else np.asarray(boxes.cls)
    conf = boxes.conf.cpu().numpy() if hasattr(boxes.conf, "cpu") else np.asarray(boxes.conf)
    out = []
    for i in range(len(xy)):
        x1, y1, x2, y2 = (float(v) for v in xy[i])
        out.append(
            {
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "class": int(cls[i]),
                "confidence": round(float(conf[i]), 3),
            }
        )
    return out


def annotate(frame, boxes: list[dict], player_color=(0, 255, 0)):
    """Draw detection boxes on a copy of ``frame`` (players green, ball red)."""
    import cv2

    out = frame.copy()
    for b in boxes:
        x1, y1, x2, y2 = int(b["x1"]), int(b["y1"]), int(b["x2"]), int(b["y2"])
        color = (0, 0, 255) if b["class"] == BALL else player_color
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
    return out


def _run_sahi(video, *, model_path, conf, classes, max_frames=None, slice_size=640, frames=None,
               progress: Optional[Callable[[dict], None]] = None):
    """Sliced (SAHI) inference for small-object recall — per frame. ``frames`` is injectable for tests."""
    import cv2
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction

    det_model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics", model_path=model_path, confidence_threshold=conf)
    wanted = set(classes)
    out: dict[int, list[dict]] = {}
    iterator = frames if frames is not None else None
    cap = None if frames is not None else cv2.VideoCapture(video)
    # ponytail: best-known total for progress only; frames-injected (tests) → len(frames),
    # capped run → the cap, else a container probe. No effect on results.
    if frames is not None:
        total = len(frames)
    elif max_frames:
        total = max_frames
    else:
        total = _frame_count(video)
    i = 0
    while True:
        if frames is not None:
            if i >= len(frames):
                break
            frame = frames[i]
        else:
            ok, frame = cap.read()
            if not ok:
                break
        i += 1
        result = get_sliced_prediction(
            frame, det_model, slice_height=slice_size, slice_width=slice_size,
            overlap_height_ratio=0.2, overlap_width_ratio=0.2, perform_standard_pred=True)
        boxes = []
        for pred in result.object_prediction_list:
            cid = int(pred.category.id)
            if cid in wanted:
                x1, y1, x2, y2 = pred.bbox.to_xyxy()
                boxes.append({"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                              "class": cid, "confidence": round(float(pred.score.value), 3)})
        out[i] = boxes
        if progress:
            progress({"type": "frame", "stage": "detect", "currentFrame": i, "totalFrames": total})
        if max_frames and i >= max_frames:
            break
    if cap is not None:
        cap.release()
    return out


def detect_ball_sahi(video, ball_model_path, *, ball_class: int = 0, conf: float = 0.15,
                        slice_size: int = 512, max_frames=None, frames=None) -> Result:
    """High-recall ball detection: SAHI sliced inference with a football-ball specialist model.

    VALIDATED on football-1.mp4: 96% ball-frame coverage vs 1% for COCO class 32 (see wiki
    learning). Boxes are normalized to ``class=BALL (32)`` so the rest of the pipeline
    (ball_tracker filters class==32) consumes them unchanged.
    """
    try:
        raw = _run_sahi(video, model_path=ball_model_path, conf=conf, classes=[ball_class],
                        max_frames=max_frames, slice_size=slice_size, frames=frames)
    except Exception as exc:
        return Result.Fail(f"ball SAHI failed: {exc}", feature="detect_ball")
    out = {f: [{**b, "class": BALL} for b in bxs] for f, bxs in raw.items()}
    detected = sum(1 for bxs in out.values() if bxs)
    total = len(out)
    return Result.Ok({"frames": out}, feature="detect_ball", frame_count=total,
                     ball_frames=detected, coverage=round(detected / total, 4) if total else 0.0)


@feature("detect_ball")
def _detect_ball_feature(state) -> Result:
    """Pipeline entry for the validated high-recall ball detector (SAHI + ball model)."""
    meta = state.meta or {}
    path = meta.get("ball_model_path")
    if not path:
        return Result.Fail("detect_ball needs meta['ball_model_path']", feature="detect_ball")
    return detect_ball_sahi(state.footage, path, ball_class=meta.get("ball_class", 0),
                            conf=meta.get("conf", 0.15), slice_size=meta.get("slice_size", 512),
                            max_frames=meta.get("max_frames"))


def detect(
    video,
    *,
    max_frames: Optional[int] = None,
    conf: float = 0.3,
    classes: Sequence[int] = (PERSON, BALL),
    model_path: str = "yolov8s.pt",
    model: Any = None,
    sahi: bool = False,
    slice_size: int = 640,
    progress: Optional[Callable[[dict], None]] = None,
) -> Result:
    """Run YOLO over ``video``; return ``Result(value={"frames": {frame_no: [boxes]}})``.

    ``model`` is injectable so tests can run without loading/downloading weights.
    ``sahi=True`` switches to sliced inference (small-object recall; needs a football-ball
    model to actually help — SAHI is orthogonal to the COCO class-32 problem).
    ``progress`` is an optional ``callable(event: dict) -> None`` receiving per-frame events
    (``{"type":"frame","stage":"detect","currentFrame":i,"totalFrames":n}``); omit for none.
    """
    if sahi:
        try:
            frames = _run_sahi(video, model_path=model_path, conf=conf, classes=list(classes),
                               max_frames=max_frames, slice_size=slice_size, progress=progress)
        except Exception as exc:
            return Result.Fail(f"SAHI sliced inference failed: {exc}", feature="detect")
        if not frames:
            return Result.Fail("no frames read (SAHI)", feature="detect")
        return Result.Ok({"frames": frames}, feature="detect", frame_count=len(frames),
                         classes=list(classes), conf=conf, sahi=True)
    mdl = model if model is not None else _load_model(model_path)
    frames: dict[int, list[dict]] = {}
    try:
        stream = mdl(source=video, stream=True, conf=conf, classes=list(classes))
    except Exception as exc:
        return Result.Fail(f"detection inference failed: {exc}", feature="detect")
    # ponytail: best-known total for progress only; the cap when set, else a container probe
    # (a second open of the file — acceptable; the worker always sets max_frames).
    total = max_frames if max_frames else _frame_count(video)
    for i, r in enumerate(stream, start=1):
        frames[i] = boxes_from_result(r)
        if progress:
            progress({"type": "frame", "stage": "detect", "currentFrame": i, "totalFrames": total})
        if max_frames and i >= max_frames:
            break
    if not frames:
        return Result.Fail("no frames read from video", feature="detect")
    return Result.Ok(
        {"frames": frames},
        feature="detect",
        frame_count=len(frames),
        classes=list(classes),
        conf=conf,
    )


def build_vision_config(*, model_path: str = "yolov8s.pt", ball_model_path: str | None = None,
                        classes: Sequence[int] | None = None, conf: float = 0.25,
                        imgsz: int = 1280, sahi: bool = False) -> dict:
    """Build a vision config (T8). Supply a football-ball model via ``ball_model_path``/
    ``classes`` to stop using COCO class 32 (baseball/tennis). ``sahi`` toggles sliced inference
    for small-ball recall (requires the ``sahi`` package; weights/SAHI-install are ops)."""
    return {
        "model_path": model_path,
        "ball_model_path": ball_model_path,
        "classes": list(classes) if classes is not None else [PERSON, BALL],
        "conf": conf,
        "imgsz": imgsz,
        "sahi": sahi,
    }


@feature("detect")
def _detect_feature(state: PipelineState) -> Result:
    """Registered pipeline node. Reads config from ``state.meta``."""
    meta = state.meta or {}
    return detect(
        state.footage,
        max_frames=meta.get("max_frames"),
        conf=meta.get("conf", 0.3),
        classes=meta.get("classes", (PERSON, BALL)),
        model_path=meta.get("model_path", "yolov8s.pt"),
        model=meta.get("model"),  # injectable for tests
        sahi=meta.get("sahi", False),
        slice_size=meta.get("slice_size", 640),
        progress=state.progress,
    )
