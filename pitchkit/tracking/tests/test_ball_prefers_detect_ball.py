"""Task 1 — the ball feature prefers the specialist detect_ball when present."""
from pitchkit.detection.detect import BALL
from pitchkit.pipeline import runner
import pitchkit.tracking.ball_tracker  # noqa: F401  (registers the "ball" feature)


def _ball_box():
    return {"x1": 1, "y1": 1, "x2": 2, "y2": 2, "class": BALL, "confidence": 0.9}


def test_ball_feature_prefers_detect_ball():
    detect_ball = {"frames": {1: [_ball_box()]}}
    detect = {"frames": {1: []}}  # generic detect found no ball
    res = runner.run_feature("ball", footage=None, meta={"total_frames": 1},
                             data={"detect_ball": detect_ball, "detect": detect})
    assert res.ok
    assert res.value["frames"][1] is not None  # ball came from detect_ball


def test_ball_falls_back_to_detect_without_specialist():
    detect = {"frames": {1: [_ball_box()]}}
    res = runner.run_feature("ball", footage=None, meta={"total_frames": 1}, data={"detect": detect})
    assert res.ok
    assert res.value["frames"][1] is not None
