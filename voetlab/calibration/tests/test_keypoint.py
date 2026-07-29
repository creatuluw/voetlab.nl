"""T4 keypoint detector core — IFAB template + pairing → homography."""
import pytest

from voetlab.calibration.homography import estimate_homography, px_to_meters
from voetlab.calibration.keypoint import TEMPLATE_POINTS, pairs_from_keypoints


def test_template_ifab_landmarks():
    assert TEMPLATE_POINTS["center"] == (52.5, 34.0)
    assert TEMPLATE_POINTS["penalty_left"] == (11.0, 34.0)
    assert TEMPLATE_POINTS["penalty_right"] == (94.0, 34.0)


def test_pairs_drop_unknown_landmarks():
    img_by_name = {"corner_0_0": (10, 20), "center": (500, 300), "bogus": (1, 1)}
    img, tpl = pairs_from_keypoints(img_by_name)
    assert len(img) == 2 and len(tpl) == 2
    i = img.index((10, 20))
    assert tpl[i] == (0.0, 0.0)


def test_pairs_feed_estimate_homography():
    img_by_name = {
        "corner_0_0": (100, 100), "corner_105_0": (1105, 100),
        "corner_0_68": (100, 784), "corner_105_68": (1105, 784),
    }
    img, tpl = pairs_from_keypoints(img_by_name)
    H = estimate_homography(img, tpl)
    assert px_to_meters((100, 100), H)[0] == pytest.approx(0.0, abs=1.0)
    assert px_to_meters((1105, 784), H)[0] == pytest.approx(105.0, abs=1.0)
