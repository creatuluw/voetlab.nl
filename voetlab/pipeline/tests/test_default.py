"""P7 — default pipeline wiring + single-feature run + end-to-end smoke on football-1.mp4."""
from pathlib import Path

import numpy as np
import pytest

from voetlab.pipeline import default
from voetlab.pipeline.registry import registered

HAS_FOOTAGE = Path("football-1.mp4").exists()


class _FakeBoxes:
    def __init__(self, xy):
        self.xyxy = np.asarray(xy, dtype=float)
        self.cls = np.zeros(len(xy), dtype=float)
        self.conf = np.full(len(xy), 0.9, dtype=float)


class _FakeResult:
    def __init__(self, xy):
        self.boxes = _FakeBoxes(xy)


class _FakeModel:
    def __call__(self, *, source, stream, conf, classes):
        for r in [
            _FakeResult([[10, 10, 50, 90], [400, 100, 440, 180]]),
            _FakeResult([[12, 12, 52, 92]]),
        ]:
            yield r


def test_all_features_registered():
    for name in default.DEFAULT_FEATURES:
        assert name in registered(), f"{name} not registered"


def test_run_feature_isolation_detect():
    res = default.run_feature("detect", "fake.mp4", meta={"model": _FakeModel(), "max_frames": 2})
    assert res.ok
    assert "frames" in res.value


def test_run_subset_features():
    # detect + track only, with injected model
    res = default.run("fake.mp4", features=["detect", "track"], meta={"model": _FakeModel(), "max_frames": 2})
    assert res.ok
    assert "track" in res.value["data"]


@pytest.mark.skipif(not HAS_FOOTAGE, reason="football-1.mp4 not found")
def test_e2e_pipeline_on_footage():
    from voetlab.core.fixtures import dump_artifacts

    res = default.run("football-1.mp4", meta={"max_frames": 5, "sample_frames": 5})
    assert res.ok, f"pipeline failed features: {res.value.get('failed')}"
    data = res.value["data"]
    assert "detect" in data and "track" in data and "stats" in data
    n_players = len(data["stats"]["players"])
    dump_artifacts("pipeline", data={"failed": res.value["failed"], "n_players": n_players,
                                     "features_run": res.meta.get("features_run")})
    assert n_players > 0
