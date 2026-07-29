"""T5 — metric physical stats (m / km·h) via homography."""
import pytest

from pitchkit.calibration.homography import estimate_homography
from pitchkit.stats.stats import compute_stats

# H: 1 px = 0.1 m  (image 1000x1000 → template 100x100 m)
H = estimate_homography([(0, 0), (1000, 0), (1000, 1000), (0, 1000)],
                        [(0, 0), (100, 0), (100, 100), (0, 100)])


def _p(tid, fx):
    return {"track_id": tid, "x1": fx - 10, "y1": 400, "x2": fx + 10, "y2": 500}  # feet=(fx, 500)


def _empty_events():
    return {"possession": [], "passes": [], "tackles": [], "interceptions": []}


def test_metric_distance_and_speed():
    # feet move 10 px (=1 m) per frame
    tracks = {"frames": {1: [_p(1, 0)], 2: [_p(1, 10)], 3: [_p(1, 20)]}}
    res = compute_stats(tracks, {"teams": {1: "A"}}, _empty_events(), fps=25, H=H)
    assert res.ok
    st = res.value["players"][1]
    assert st["distance_m"] == pytest.approx(2.0, abs=0.1)          # 2 steps × 1 m
    assert st["top_speed_km_h"] == pytest.approx(1.0 * 25 * 3.6, abs=1.0)


def test_pixel_fields_still_present_without_H():
    tracks = {"frames": {1: [_p(1, 0)], 2: [_p(1, 10)]}}
    res = compute_stats(tracks, {"teams": {1: "A"}}, _empty_events(), fps=25)
    st = res.value["players"][1]
    assert st["distance_px"] > 0
    assert st["distance_m"] == 0.0  # default when no H
