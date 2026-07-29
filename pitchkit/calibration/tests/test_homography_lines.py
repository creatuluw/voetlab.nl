"""DLT-from-lines homography — recovers a known H from projected line correspondences."""
import numpy as np

from pitchkit.calibration.homography_lines import (
    estimate_homography_from_line_correspondences,
    normalization_transform,
)


def _line_through(p1, p2):
    return np.cross(np.array([p1[0], p1[1], 1.0]), np.array([p2[0], p2[1], 1.0]))


def test_recover_known_homography_from_lines():
    H_true = np.array([[0.5, 0.0, 10.0], [0.0, 0.4, 5.0], [0.0, 0.0, 1.0]])  # image -> template
    tmpl_pts = [(0, 0), (10, 0), (10, 6), (0, 6), (5, 0), (5, 6)]
    img_pts = [(float((H_true @ np.array([x, y, 1.0]))[0]),
                float((H_true @ np.array([x, y, 1.0]))[1])) for x, y in tmpl_pts]
    lines = [
        (_line_through(tmpl_pts[0], tmpl_pts[1]), _line_through(img_pts[0], img_pts[1])),
        (_line_through(tmpl_pts[2], tmpl_pts[3]), _line_through(img_pts[2], img_pts[3])),
        (_line_through(tmpl_pts[0], tmpl_pts[3]), _line_through(img_pts[0], img_pts[3])),
        (_line_through(tmpl_pts[1], tmpl_pts[2]), _line_through(img_pts[1], img_pts[2])),
        (_line_through(tmpl_pts[4], tmpl_pts[5]), _line_through(img_pts[4], img_pts[5])),
    ]
    T1 = normalization_transform(tmpl_pts)
    T2 = normalization_transform(img_pts)
    ok, H_est = estimate_homography_from_line_correspondences(lines, T1, T2)
    assert ok
    H_img_to_tmpl = np.linalg.inv(H_est)  # H_est is template->image
    for (ix, iy), (tx, ty) in zip(img_pts, tmpl_pts):
        got = (H_img_to_tmpl @ np.array([ix, iy, 1.0]))
        got = got / got[2]
        assert np.allclose([got[0], got[1]], [tx, ty], atol=1e-3)


def test_normalization_transform_centers_points():
    T = normalization_transform([(0, 0), (10, 0), (10, 10), (0, 10)])
    assert T.shape == (3, 3)
    assert T[2, 2] == 1.0
