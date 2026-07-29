"""P1 — detection feature.

Mocked-YOLO unit tests (no weight download); plus a real-footage smoke on football-1.mp4
that dumps an annotated frame you can open in tests/out/detect/.
"""
from pathlib import Path

import numpy as np
import pytest

from voetlab.core.result import Result
from voetlab.detection.detect import BALL, PERSON, annotate, boxes_from_result, detect
from voetlab.pipeline import runner

# ---- minimal fakes mirroring the ultralytics result shape ----

class FakeBoxes:
    def __init__(self, xyxy, cls, conf):
        self.xyxy = np.asarray(xyxy, dtype=float)
        self.cls = np.asarray(cls, dtype=float)
        self.conf = np.asarray(conf, dtype=float)


class FakeResult:
    def __init__(self, xyxy, cls, conf):
        self.boxes = FakeBoxes(xyxy, cls, conf)


class FakeModel:
    """Yields FakeResults; records the conf/classes it was called with."""

    def __init__(self, results):
        self.results = results
        self.called = {}

    def __call__(self, *, source, stream, conf, classes):
        self.called = {"conf": conf, "classes": list(classes)}
        for r in self.results:
            yield r


# ---- unit tests (mocked, fast) ----

def test_detect_uses_config_and_returns_boxes():
    model = FakeModel(
        [
            FakeResult([[10, 10, 50, 90], [400, 100, 440, 180]], [PERSON, BALL], [0.9, 0.4]),
            FakeResult([[12, 12, 52, 92]], [PERSON], [0.85]),
        ]
    )
    res = detect("fake.mp4", max_frames=2, conf=0.25, classes=(PERSON, BALL), model=model)
    assert res.ok
    assert model.called["conf"] == 0.25
    assert model.called["classes"] == [PERSON, BALL]
    assert res.value["frames"][1][1]["class"] == BALL
    assert res.meta["frame_count"] == 2


def test_detect_fail_on_no_frames():
    res = detect("fake.mp4", model=FakeModel([]))
    assert not res.ok


def test_boxes_from_result_empty_when_no_boxes():
    class Empty:
        boxes = None

    assert boxes_from_result(Empty()) == []


def test_run_feature_isolation_detect():
    model = FakeModel([FakeResult([[1, 1, 20, 20]], [PERSON], [0.5])])
    res = runner.run_feature("detect", footage="fake.mp4", meta={"model": model, "max_frames": 1})
    assert res.ok
    assert "frames" in res.value


def test_annotate_draws_without_error():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    out = annotate(frame, [{"x1": 5, "y1": 5, "x2": 20, "y2": 20, "class": PERSON}])
    assert out.shape == frame.shape
    assert not np.array_equal(out, frame)  # something was drawn


# ---- real-footage smoke (football-1.mp4) ----

HAS_FOOTAGE = Path("football-1.mp4").exists()


@pytest.mark.skipif(not HAS_FOOTAGE, reason="football-1.mp4 not found")
def test_detect_smoke_on_footage():
    from voetlab.core.fixtures import dump_artifacts, load_sample_frames

    res = detect("football-1.mp4", max_frames=3, conf=0.3, classes=(PERSON, BALL))
    assert res.ok, res.error
    assert res.meta["frame_count"] == 3
    total = sum(len(v) for v in res.value["frames"].values())
    assert total > 0, "YOLO found nothing in 3 frames — model/footage issue"

    # annotate frame 1 over the first loaded frame and dump for human inspection
    frames = load_sample_frames(1)
    annotated = annotate(frames[0], res.value["frames"][1])
    d = dump_artifacts("detect", frames=[annotated], data={"frame_count": 3, "boxes_per_frame": {k: len(v) for k, v in res.value["frames"].items()}})
    assert (d / "annotated.png").exists()
