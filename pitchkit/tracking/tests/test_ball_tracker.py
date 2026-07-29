"""P3 — ball trajectory (linear interpolation, ported from ball_interpolation.py)."""
from pitchkit.detection.detect import BALL
from pitchkit.tracking.ball_tracker import track_ball


def _b(x1, y1, x2, y2, conf=0.8):
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "class": BALL, "confidence": conf}


def test_interpolates_gap_and_marks_synthetic():
    det = {"frames": {1: [_b(100, 100, 110, 110)], 10: [_b(190, 100, 200, 110)]}}
    res = track_ball(det, total_frames=10)
    assert res.ok
    fr = res.value["frames"]
    assert fr[1] is not None and fr[10] is not None
    assert fr[5] is not None and fr[5]["confidence"] == 0.0  # interpolated → marked synthetic
    assert res.meta["coverage"] == 1.0


def test_picks_highest_conf_ball_per_frame():
    det = {"frames": {1: [_b(100, 100, 110, 110, 0.3), _b(900, 900, 910, 910, 0.9)]}}
    res = track_ball(det, total_frames=1)
    assert res.ok
    assert res.value["frames"][1]["x1"] == 900  # higher-confidence ball chosen


def test_empty_returns_ok_with_zero_coverage():
    res = track_ball({"frames": {}}, total_frames=10)
    assert res.ok
    assert res.meta["coverage"] == 0.0
