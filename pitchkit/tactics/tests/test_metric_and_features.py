"""T4/T5/T11/T12 bridge — pixel tracks → metric via homography + tactics feature wiring."""
import pytest

from pitchkit.calibration.homography import estimate_homography
from pitchkit.calibration.metric import tracks_to_metric
from pitchkit.pipeline import runner

# H: 1 px = 0.1 m
H = estimate_homography([(0, 0), (1000, 0), (1000, 1000), (0, 1000)],
                        [(0, 0), (100, 0), (100, 100), (0, 100)])


def _player(tid, fx):
    return {"track_id": tid, "x1": fx - 10, "y1": 400, "x2": fx + 10, "y2": 500}  # feet=(fx, 500)


def test_tracks_to_metric_warps_feet():
    track = {"frames": {1: [_player(1, 100)]}}  # feet (100,500) → (10, 50) m
    out = tracks_to_metric(track, H, teams={1: "A"})
    p = out["frames"][1][0]
    assert p["x_m"] == pytest.approx(10.0, abs=0.5)
    assert p["y_m"] == pytest.approx(50.0, abs=0.5)
    assert p["team"] == "A"


def test_voronoi_feature_runs_with_H():
    # ensure the tactics feature modules import (registering the features)
    import pitchkit.tactics.features  # noqa: F401
    track = {"frames": {1: [_player(1, 100), _player(2, 900)]}}
    res = runner.run_feature("voronoi", footage=None, meta={"H": H},
                             data={"track": track, "teams": {"teams": {1: "A", 2: "B"}}})
    assert res.ok, res.error
    assert "areas_m2" in res.value
    assert res.value["areas_m2"]  # both teams present


def test_voronoi_feature_fails_without_H():
    import pitchkit.tactics.features  # noqa: F401
    res = runner.run_feature("voronoi", footage=None, meta={}, data={"track": {"frames": {1: [_player(1, 100)]}}})
    assert not res.ok  # no H → clear failure, not junk
