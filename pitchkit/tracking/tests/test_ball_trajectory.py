"""T6 — Kalman constant-velocity ball trajectory (upgrade over linear interp).

Beats the linear `track_ball` on (a) coverage — it predicts a position on EVERY frame from
the first detection to the end (linear only fills *between* two detections), and (b) noise
smoothing. Same output contract as `track_ball` (synthetic points marked confidence=0.0).
"""
import numpy as np

from pitchkit.tracking.ball_trajectory import track_ball_kalman


def _ball(cx, cy, conf=0.8):
    return {"x1": cx - 5, "y1": cy - 5, "x2": cx + 5, "y2": cy + 5, "class": 32, "confidence": conf}


def test_kalman_full_coverage_including_after_last_detection():
    # detections only on frames 1..5, but total_frames=20 → Kalman predicts 6..20
    det = {"frames": {f: [_ball(f * 10, 100)] for f in range(1, 6)}}
    res = track_ball_kalman(det, total_frames=20)
    assert res.ok
    fr = res.value["frames"]
    assert all(fr[f] is not None for f in range(1, 21)), "Kalman must cover every frame 1..20"
    assert res.meta["coverage"] == 1.0
    assert res.meta["method"] == "kalman"


def test_kalman_beats_linear_coverage():
    from pitchkit.tracking.ball_tracker import track_ball

    det = {"frames": {1: [_ball(100, 100)], 10: [_ball(190, 100)]}}
    lin = track_ball(det, total_frames=20)
    kal = track_ball_kalman(det, total_frames=20)
    assert kal.meta["coverage"] > lin.meta["coverage"]  # linear misses 11..20


def test_kalman_tracks_true_motion_better_than_raw():
    rng = np.random.RandomState(0)
    true = [10 * f for f in range(20)]               # true linear motion
    meas = [t + rng.randn() * 6 for t in true]        # noisy measurements
    det = {"frames": {f + 1: [_ball(meas[f], 100)] for f in range(20)}}
    res = track_ball_kalman(det, total_frames=20, meas_noise=16.0)
    centers = [(res.value["frames"][f]["x1"] + res.value["frames"][f]["x2"]) / 2 for f in range(1, 21)]
    rmse_kal = float(np.sqrt(np.mean([(c - t) ** 2 for c, t in zip(centers, true)])))
    rmse_raw = float(np.sqrt(np.mean([(m - t) ** 2 for m, t in zip(meas, true)])))
    assert rmse_kal < rmse_raw  # Kalman is closer to the true trajectory than raw noise


def test_kalman_empty_returns_ok_zero_coverage():
    res = track_ball_kalman({"frames": {}}, total_frames=10)
    assert res.ok and res.meta["coverage"] == 0.0
