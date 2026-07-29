"""calibrate feature — monkeypatched model-load + keypoints -> H (no real tvcalib needed)."""
import numpy as np

from SoccerNet.Evaluation.utils_calibration import SoccerPitch

import voetlab.calibration.features  # noqa: F401  (registers "calibrate")
import voetlab.calibration.keypoint as kp_mod
from voetlab.pipeline import runner


def _synthetic_kp():
    field = SoccerPitch()
    H_true = np.array([[18.0, 0, 200.0], [0, 14.0, 150.0], [0, 0, 1.0]])  # template->image
    kp, n = {}, 0
    for lc, keys in field.line_extremities_keys.items():
        if lc == "Circle central" or "unknown" in lc:
            continue
        pts = []
        for key in keys[:2]:
            tx, ty = field.point_dict[key][:2]
            v = H_true @ np.array([tx, ty, 1.0])
            pts.append((float(v[0] / v[2]), float(v[1] / v[2])))
        kp[lc] = pts
        n += 1
        if n >= 6:
            break
    return kp


class _FakeCap:
    def __init__(self, *a, **k):
        pass

    def set(self, *a, **k):
        pass

    def get(self, prop):
        return 0

    def read(self):
        return True, np.zeros((1080, 1920, 3), np.uint8)

    def release(self):
        pass


def test_calibrate_produces_H(monkeypatch):
    monkeypatch.setattr(kp_mod, "_load_tvcalib_model", lambda ckpt, device=None: object())
    monkeypatch.setattr(kp_mod, "detect_keypoints_tvcalib", lambda frame, **k: _synthetic_kp())
    # unit test exercises the DLT fallback; the real 2000-step solver is validated in e2e
    monkeypatch.setattr("voetlab.calibration.tvcalib_solver.calibrate_with_tvcalib", lambda *a, **k: None)
    import cv2
    monkeypatch.setattr(cv2, "VideoCapture", lambda *a, **k: _FakeCap())
    res = runner.run_feature("calibrate", footage="v.mp4",
                             meta={"calib_checkpoint": "x.pt", "tvcalib_path": "external/tvcalib"})
    assert res.ok
    assert "H" in res.value and res.value["lines"]


def test_calibrate_needs_checkpoint():
    res = runner.run_feature("calibrate", footage="v.mp4", meta={})
    assert not res.ok
