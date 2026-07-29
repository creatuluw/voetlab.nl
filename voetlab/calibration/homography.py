"""T4 — pitch homography pure engine: broadcast pixels → real-world meters.

This is the testable CORE of calibration: given image↔template point pairs, estimate a
homography and warp points to meters, with TVCalib-style self-verification (reject a
per-frame H whose reprojection error exceeds τ). The keypoint DETECTOR (TVCalib
segmentation → field landmarks) is a separate ops step that plugs ``image_pts`` in here.

Quality & when to use
- GOOD: exact, deterministic; perspectiveTransform correctly handles non-uniform px/m
  (far players get the right scale when their whole trajectory is warped).
- WEAK: accuracy is entirely determined by the quality of the input keypoints — a bad
  point set gives a confident-but-wrong H. ``self_verify`` catches gross mismatches only.
- When: call after you have ≥4 well-spread pitch landmarks per frame; warp each player's
  feet through H before computing distance/speed (T5). Verified technique: TVCalib (WACV23).
"""
from __future__ import annotations

import cv2
import numpy as np

# IFAB standard pitch (length × width), metres.
PITCH_M = (105.0, 68.0)


def estimate_homography(image_pts, template_pts):
    """Image→template homography via RANSAC (returns None if <4 point pairs)."""
    img = np.float32(image_pts)
    tpl = np.float32(template_pts)
    if len(img) < 4 or len(img) != len(tpl):
        return None
    H, _ = cv2.findHomography(img, tpl, cv2.RANSAC, 5.0)
    return H


def warp_points(pts, H) -> np.ndarray:
    """Map an array of (x, y) points through homography ``H`` → (N, 2) output."""
    arr = np.float32(pts).reshape(-1, 1, 2)
    out = cv2.perspectiveTransform(arr, H)
    return out.reshape(-1, 2)


def px_to_meters(pt, H) -> tuple[float, float]:
    """Map a single pixel point to pitch meters via ``H``."""
    x, y = warp_points([pt], H)[0]
    return (float(x), float(y))


def self_verify(H, image_pts, template_pts, tau: float = 0.5) -> bool:
    """TVCalib-style gate: accept ``H`` only if mean reprojection error ≤ ``tau`` metres."""
    if H is None:
        return False
    proj = warp_points(image_pts, H)
    tpl = np.float32(template_pts)
    err = float(np.mean(np.linalg.norm(proj - tpl, axis=1)))
    return err <= tau
