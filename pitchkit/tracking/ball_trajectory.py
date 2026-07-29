"""T6 — Kalman constant-velocity ball trajectory (upgrade over linear interp).

Why this exists: the linear ``track_ball`` only fills *between* two detections and draws a
straight line — wrong for curves and leaves frames after the last detection empty. This
Kalman CV filter predicts a ball position on EVERY frame from the first detection to the
end, and smooths noisy detections. Same output contract as ``track_ball`` so it's a drop-in
``meta={"ball_method": "kalman"}`` swap. Pure numpy (no filterpy dependency).

Quality & when to use
- GOOD: ~100% coverage from the first detection onward; smooths jittery ball boxes.
- WEAK: constant-velocity model — still drifts on sharp curves/bounces/deflections across
  long gaps (a constant-acceleration / physics model would be better; see findings_ball §5).
- When: feature "ball" with ball_method="kalman"; never fails (absent ball → coverage 0).
"""
from __future__ import annotations

import numpy as np

from pitchkit.core.result import Result
from pitchkit.detection.detect import BALL


class KalmanBall2D:
    """Constant-velocity Kalman over ball center (cx, cy); box size tracks last detection."""

    def __init__(self, process_noise: float = 1.0, meas_noise: float = 4.0):
        self.x = np.zeros(4)  # [cx, cy, vx, vy]
        self.P = np.eye(4) * 1000.0
        self.F = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], float)
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], float)
        self.Q = np.eye(4) * process_noise
        self.R = np.eye(2) * meas_noise
        self.initialized = False
        self.w = 0.0
        self.h = 0.0

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[:2]

    def update(self, z: np.ndarray, w: float, h: float):
        if not self.initialized:
            self.x[:2] = z
            self.x[2:] = 0.0
            self.initialized = True
            self.w, self.h = w, h
            return
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P
        self.w, self.h = w, h


def track_ball_kalman(
    detections_value,
    *,
    total_frames: int | None = None,
    process_noise: float = 1.0,
    meas_noise: float = 4.0,
) -> Result:
    """Build a per-frame ball box for EVERY frame via a constant-velocity Kalman filter.

    Returns ``Result(value={"frames": {frame_no: ball_box|None}})``. Frames before the first
    detection are None; from the first detection to ``total_frames`` every frame has a box
    (real detection keeps its confidence; predicted frames are ``confidence=0.0``).
    """
    frames_in = detections_value.get("frames", {}) if isinstance(detections_value, dict) else {}

    detected: dict[int, dict] = {}
    for f, boxes in frames_in.items():
        balls = [b for b in boxes if b.get("class") == BALL]
        if balls:
            detected[f] = max(balls, key=lambda x: x["confidence"])

    total_frames = max(0, int(total_frames or (max(frames_in) if frames_in else 0)))
    out: dict[int, dict | None] = {f: None for f in range(1, total_frames + 1)}
    if not detected:
        return Result.Ok({"frames": out}, feature="ball", detected=0, coverage=0.0, method="kalman")

    km = KalmanBall2D(process_noise, meas_noise)
    first = min(detected)
    for f in range(first, total_frames + 1):
        km.predict()
        if f in detected:
            b = detected[f]
            cx, cy = (b["x1"] + b["x2"]) / 2.0, (b["y1"] + b["y2"]) / 2.0
            km.update(np.array([cx, cy], float), b["x2"] - b["x1"], b["y2"] - b["y1"])
            out[f] = {"x1": b["x1"], "y1": b["y1"], "x2": b["x2"], "y2": b["y2"],
                      "confidence": b["confidence"]}
        else:
            cx, cy, w, h = km.x[0], km.x[1], km.w, km.h
            out[f] = {"x1": cx - w / 2, "y1": cy - h / 2, "x2": cx + w / 2, "y2": cy + h / 2,
                      "confidence": 0.0}

    covered = sum(1 for v in out.values() if v is not None)
    coverage = covered / total_frames if total_frames else 0.0
    return Result.Ok(
        {"frames": out}, feature="ball", detected=len(detected),
        coverage=round(coverage, 4), method="kalman",
    )
