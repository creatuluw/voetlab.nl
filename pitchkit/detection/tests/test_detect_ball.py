"""T8 — high-recall ball detector (SAHI + specialist model), monkeypatched (no real model)."""
from pitchkit.detection import detect as d
from pitchkit.detection.detect import BALL, detect_ball_sahi


def test_detect_ball_sahi_remaps_class_to_BALL(monkeypatch):
    # _run_sahi would return ball boxes with the specialist model's class id (0)
    monkeypatch.setattr(d, "_run_sahi",
                        lambda video, **k: {1: [{"x1": 1, "y1": 1, "x2": 2, "y2": 2, "class": 0, "confidence": 0.9}]})
    res = detect_ball_sahi("v.mp4", "ball.pt", frames=[None])
    assert res.ok
    assert res.value["frames"][1][0]["class"] == BALL  # normalized 0 -> 32 for the pipeline
    assert res.meta["ball_frames"] == 1
    assert res.meta["coverage"] == 1.0


def test_detect_ball_sahi_empty_is_ok(monkeypatch):
    monkeypatch.setattr(d, "_run_sahi", lambda video, **k: {1: [], 2: []})
    res = detect_ball_sahi("v.mp4", "ball.pt", frames=[None, None])
    assert res.ok
    assert res.meta["ball_frames"] == 0
    assert res.meta["coverage"] == 0.0


def test_detect_ball_feature_isolation(monkeypatch):
    monkeypatch.setattr(d, "_run_sahi",
                        lambda video, **k: {1: [{"x1": 5, "y1": 5, "x2": 9, "y2": 9, "class": 0, "confidence": 0.8}]})
    from pitchkit.pipeline import runner
    res = runner.run_feature("detect_ball", footage="v.mp4",
                             meta={"ball_model_path": "ball.pt", "max_frames": 1})
    assert res.ok and res.value["frames"][1][0]["class"] == BALL
