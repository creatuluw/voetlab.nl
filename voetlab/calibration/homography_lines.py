"""DLT homography from LINE correspondences (SoccerNet/sn-calibration baseline).

Pure numpy, self-contained (the seg/keypoint side needs tvcalib; this math does not).
Each correspondence is ``(template_line, image_line)`` as homogeneous 3-vectors [a,b,c]
with ax+by+c=0. The returned homography maps IMAGE -> TEMPLATE (pixels -> pitch coords),
matching the convention of ``calibration.homography.estimate_homography``.
"""
from __future__ import annotations

import numpy as np


def normalization_transform(points) -> np.ndarray:
    """Similarity transform centering ``points`` and scaling mean radius to sqrt(2)."""
    points = np.asarray(points, dtype=float)
    center = points.mean(axis=0)
    d = 0.0
    for n, p in enumerate(points, 1):
        d += (np.hypot(p[0] - center[0], p[1] - center[1]) - d) / n
    s = (np.sqrt(2) / d) if d > 0 else 1.0
    T = np.zeros((3, 3))
    T[0, 0], T[1, 1], T[2, 2] = s, s, 1.0
    T[0, 2], T[1, 2] = -s * center[0], -s * center[1]
    return T


def estimate_homography_from_line_correspondences(lines, T1=None, T2=None):
    """Estimate H from line correspondences via DLT (SVD). Returns (ok, H)."""
    if T1 is None:
        T1 = np.eye(3)
    if T2 is None:
        T2 = np.eye(3)
    A = np.zeros((len(lines) * 2, 9))
    for i, (src_line, tgt_line) in enumerate(lines):
        u, v, w = np.linalg.inv(T1).T @ np.asarray(src_line, float)
        x, y, z = np.linalg.inv(T2).T @ np.asarray(tgt_line, float)
        A[2 * i, :] = [0, x * w, -x * v, 0, y * w, -v * y, 0, z * w, -v * z]
        A[2 * i + 1, :] = [x * w, 0, -x * u, y * w, 0, -u * y, z * w, 0, -u * z]
    try:
        _, s, vh = np.linalg.svd(A)
    except np.linalg.LinAlgError:
        return False, np.eye(3)
    idx = len(s) - 1
    if not (s[idx] > 0):
        return False, np.eye(3)
    H = vh[idx].reshape(3, 3)
    H = np.linalg.inv(T2) @ H @ T1
    H /= H[2, 2]
    return True, H
