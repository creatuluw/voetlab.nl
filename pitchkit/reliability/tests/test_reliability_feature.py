"""B2 — reliability pipeline feature (synthetic data, no footage)."""
from pitchkit.detection.detect import BALL, PERSON
from pitchkit.pipeline import runner
import pitchkit.reliability.features  # noqa: F401  (registers "reliability")


def _ball(frames_conf):
    return {"frames": {f: {"x1": 1, "y1": 1, "x2": 2, "y2": 2, "confidence": c} for f, c in frames_conf}}


def test_reliability_feature_runs():
    ball = _ball([(f, 0.8) for f in range(1, 19)] + [(f, 0.0) for f in range(19, 101)])
    track = {"frames": {f: [{"track_id": (f % 30) + 1}] for f in range(1, 101)}}
    res = runner.run_feature("reliability", footage=None, meta={"total_frames": 100},
                             data={"ball": ball, "track": track})
    assert res.ok
    v = res.value
    assert v["ball_coverage"] == 0.18
    assert v["n_tracks"] == 30


def test_reliability_feature_needs_upstream():
    res = runner.run_feature("reliability", footage=None, meta={"total_frames": 10}, data={})
    assert not res.ok
