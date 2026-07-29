"""T8 — SAHI sliced-inference branch in detect (monkeypatched; no real model needed)."""
import numpy as np

from pitchkit.detection.detect import PERSON, _run_sahi


class _BBox:
    def to_xyxy(self):
        return [10, 10, 50, 90]


class _Pred:
    class category:
        id = PERSON

    class score:
        value = 0.9

    bbox = _BBox()


class _Result:
    object_prediction_list = [_Pred()]


def test_run_sahi_parses_predictions(monkeypatch):
    import sahi
    import sahi.predict as sahi_predict

    monkeypatch.setattr(sahi.AutoDetectionModel, "from_pretrained", lambda **k: object())
    monkeypatch.setattr(sahi_predict, "get_sliced_prediction", lambda *a, **k: _Result())

    frames = _run_sahi(video=None, model_path="x.pt", conf=0.3, classes=[PERSON],
                       max_frames=1, frames=[np.zeros((100, 100, 3), np.uint8)])
    assert frames[1][0]["class"] == PERSON
    assert frames[1][0]["confidence"] == 0.9


def test_run_sahi_drops_unwanted_classes(monkeypatch):
    import sahi
    from pitchkit.detection.detect import BALL

    class P2:
        class category:
            id = BALL  # not in wanted classes
        class score:
            value = 0.5
        bbox = _BBox()

    class R2:
        object_prediction_list = [_Pred(), P2()]

    monkeypatch.setattr(sahi.AutoDetectionModel, "from_pretrained", lambda **k: object())
    import sahi.predict as sahi_predict
    monkeypatch.setattr(sahi_predict, "get_sliced_prediction", lambda *a, **k: R2())

    frames = _run_sahi(video=None, model_path="x.pt", conf=0.3, classes=[PERSON],
                       max_frames=1, frames=[np.zeros((100, 100, 3), np.uint8)])
    assert len(frames[1]) == 1  # only PERSON kept; BALL dropped
