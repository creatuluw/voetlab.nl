"""Keypoint-detection quality logic — pure, synthetic tests (no tvcalib/model needed)."""
from voetlab.calibration.keypoint import (
    _dedup_points,
    filter_keypoints,
    is_ground_line,
    keypoint_summary,
    line_coverage,
)


def test_is_ground_line():
    assert is_ground_line("Side line left") is True
    assert is_ground_line("Big rect. left main") is True
    assert is_ground_line("Goal right crossbar") is False   # 3D structure
    assert is_ground_line("Circle central") is False         # arc, not a straight line
    assert is_ground_line("Line unknown") is False


def test_filter_drops_non_ground():
    kp = {"Side line left": [(10, 10), (20, 20)],
          "Goal right crossbar": [(5, 5), (6, 6)],
          "Circle central": [(1, 1)]}
    out = filter_keypoints(kp)
    assert "Side line left" in out
    assert "Goal right crossbar" not in out
    assert "Circle central" not in out


def test_filter_dedup_and_min_points():
    # two near-duplicate points + a far one; min_separation merges the close pair
    kp = {"Big rect. left main": [(100, 100), (101, 101), (500, 500)]}
    out = filter_keypoints(kp, min_separation=5.0, min_points=2)
    assert len(out["Big rect. left main"]) == 2  # 101,101 merged into 100,100; 500 kept
    # a line with only 1 point after dedup is dropped
    kp2 = {"Side line right": [(100, 100), (101, 101)]}
    assert filter_keypoints(kp2, min_separation=5.0, min_points=2) == {}


def test_dedup_keeps_well_separated():
    pts = [(0, 0), (50, 0), (100, 0)]
    assert len(_dedup_points(pts, 5.0)) == 3


def test_line_coverage_counts_classes_across_frames():
    frames = [
        {"Side line left": [(1, 1)], "Big rect. left main": [(2, 2)]},
        {"Side line left": [(3, 3)], "Circle central": [(4, 4)]},
        {"Side line left": [(5, 5)]},
    ]
    cov = line_coverage(frames)
    assert cov == {"Side line left": 3, "Big rect. left main": 1, "Circle central": 1}


def test_keypoint_summary():
    kp = {"Side line left": [(1, 1), (2, 2)], "Goal right post left": [(3, 3)]}
    s = keypoint_summary(kp)
    assert s["n_lines"] == 2
    assert s["n_ground_lines"] == 1  # only Side line left is ground
    assert "Side line left" in s["classes"]
