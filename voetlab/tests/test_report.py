"""B3 — report generator (mocked pipeline run; no footage needed)."""
import json

from voetlab.core.result import Result
import voetlab.pipeline.default as default_mod


def test_report_writes_core_files(tmp_path, monkeypatch):
    fake = Result.Ok(
        {"data": {"stats": {"players": {"1": {"distance_px": 100.0, "passes_made": 5}},
                            "teams": {}},
                  "reliability": {"ball_coverage": 0.5, "tracking_stability": 0.9},
                  "track": {"frames": {1: [{"track_id": 1, "x1": 10, "y1": 10, "x2": 20, "y2": 20}]}},
                  "events": {"passes": [{"from_track_id": 1, "to_track_id": 1}]}},
         "failed": []},
        features_run=["detect", "track", "stats", "reliability"],
    )
    monkeypatch.setattr(default_mod, "run", lambda *a, **k: fake)
    import importlib
    report_mod = importlib.import_module("voetlab.report")
    res, out = report_mod.report("v.mp4", str(tmp_path))
    assert res.ok
    assert (out / "summary.json").exists()
    assert (out / "stats.json").exists()
    assert (out / "reliability.json").exists()
    assert json.loads((out / "reliability.json").read_text())["ball_coverage"] == 0.5
    assert (out / "radar.png").exists()  # radar always produced from stats


def test_report_failing_pipeline_still_writes_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(default_mod, "run", lambda *a, **k: Result.Fail("boom", feature="run"))
    import voetlab.report as report_mod
    res, out = report_mod.report("v.mp4", str(tmp_path))
    assert not res.ok
    s = json.loads((out / "summary.json").read_text())
    assert s["ok"] is False
