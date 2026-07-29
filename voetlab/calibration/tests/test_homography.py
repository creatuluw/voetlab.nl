"""T4 — pitch homography pure engine (px → meters) with self-verification."""
import pytest

from voetlab.calibration.homography import (
    estimate_homography,
    px_to_meters,
    self_verify,
    warp_points,
)

IMG = [(100, 100), (300, 100), (300, 200), (100, 200)]     # a rectangle in pixels
TPL = [(0, 0), (20, 0), (20, 10), (0, 10)]                 # the same rectangle in meters


def test_homography_maps_corners_to_meters():
    H = estimate_homography(IMG, TPL)
    assert H is not None
    assert px_to_meters((100, 100), H) == pytest.approx((0, 0), abs=0.5)
    assert px_to_meters((300, 200), H) == pytest.approx((20, 10), abs=0.5)
    assert px_to_meters((200, 150), H)[0] == pytest.approx(10, abs=0.5)  # midpoint x


def test_warp_points_returns_array():
    H = estimate_homography(IMG, TPL)
    out = warp_points(IMG, H)
    assert out.shape == (4, 2)


def test_self_verify_accepts_correct_homography():
    H = estimate_homography(IMG, TPL)
    assert self_verify(H, IMG, TPL) is True


def test_self_verify_rejects_mismatched_template():
    H = estimate_homography(IMG, TPL)                       # correct H for TPL
    bad_tpl = [(0, 0), (5, 0), (5, 3), (0, 3)]              # wrong scale → high reprojection error
    assert self_verify(H, IMG, bad_tpl) is False


def test_estimate_returns_none_with_too_few_points():
    assert estimate_homography([(1, 1), (2, 2), (3, 3)], [(0, 0), (1, 1), (2, 2)]) is None
