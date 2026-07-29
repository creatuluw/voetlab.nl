"""Annotated-video renderer smoke test (synthetic frames, no vision deps)."""
from pathlib import Path

import cv2
import numpy as np

from voetlab.viz.annotate import annotate_video


def _write_source(path: Path, frames: int = 6, w: int = 120, h: int = 80, fps: float = 10.0) -> Path:
    """Write a tiny all-black mp4 so the test has a real source to re-read."""
    wri = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    assert wri.isOpened(), "VideoWriter would not open — opencv/mp4v unavailable in this env"
    for _ in range(frames):
        wri.write(np.zeros((h, w, 3), dtype=np.uint8))
    wri.release()
    return path


def test_annotate_writes_nonempty_mp4(tmp_path):
    src = _write_source(tmp_path / "src.mp4")
    out = tmp_path / "annotated.mp4"

    fake = {
        "data": {
            "track": {"frames": {1: [{"track_id": 7, "x1": 10, "y1": 10, "x2": 50, "y2": 60,
                                      "confidence": 0.9}]}},
            "ball": {"frames": {1: {"x1": 60, "y1": 30, "x2": 70, "y2": 40, "confidence": 0.8}}},
            "teams": {"teams": {7: "A"}},
        }
    }

    res = annotate_video(fake, str(src), str(out))
    assert res is not None, "annotate_video returned None for a valid source"
    assert Path(res).exists() and Path(res).stat().st_size > 0


def test_annotate_missing_source_returns_none(tmp_path):
    out = tmp_path / "annotated.mp4"
    assert annotate_video({"data": {}}, str(tmp_path / "nope.mp4"), str(out)) is None
    assert not out.exists()


def test_annotate_accepts_result_object(tmp_path):
    """The worker passes a real Result (has .value); a duck-typed stand-in must work too."""
    src = _write_source(tmp_path / "src.mp4")
    out = tmp_path / "annotated.mp4"

    class _FakeResult:
        value = {"data": {"teams": {"teams": {}}}}

    res = annotate_video(_FakeResult(), str(src), str(out), draw_ball=False)
    assert res is not None and Path(res).stat().st_size > 0
