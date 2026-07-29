"""homography_from_keypoints — round-trip via the SoccerPitch template (soccernet installed)."""
import numpy as np

from pitchkit.calibration.keypoint import homography_from_keypoints


def test_roundtrip_recovers_known_homography():
    from SoccerNet.Evaluation.utils_calibration import SoccerPitch

    field = SoccerPitch()
    # ground-truth image<-template warp: scale template coords onto a 1920x1080 image region
    H_true = np.array([[18.0, 0.0, 200.0], [0.0, 14.0, 150.0], [0.0, 0.0, 1.0]])  # template->image
    kp = {}
    n = 0
    for line_class, keys in field.line_extremities_keys.items():
        if line_class == "Circle central" or "unknown" in line_class:
            continue
        pts = []
        for key in keys[:2]:
            tx, ty = field.point_dict[key][:2]
            v = H_true @ np.array([tx, ty, 1.0])
            pts.append((float(v[0] / v[2]), float(v[1] / v[2])))
        kp[line_class] = pts
        n += 1
        if n >= 6:
            break
    H = homography_from_keypoints(kp, 1920, 1080)
    assert H is not None, "need >=4 line correspondences"
    # H maps image->template; warping an image point should recover the template point
    tx, ty = field.point_dict[field.line_extremities_keys[list(kp)[0]][0]][:2]
    img = H_true @ np.array([tx, ty, 1.0]); img = img / img[2]
    got = H @ np.array([img[0], img[1], 1.0]); got = got / got[2]
    assert np.allclose([got[0], got[1]], [tx, ty], atol=1e-2)


def test_returns_none_with_too_few_lines():
    # only one line class → <4 correspondences → None
    H = homography_from_keypoints({"Big rect. left": [(10, 10), (20, 20)]}, 1920, 1080)
    assert H is None
