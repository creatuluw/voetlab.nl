"""T10 — reliability signal (per-stat confidence from measurable CV-quality signals)."""
from pitchkit.reliability.reliability import compute_reliability


def _ball(frames_conf):
    # frames_conf: list of (frame_no, confidence) ; confidence 0.0 = interpolated
    return {"frames": {f: {"x1": 1, "y1": 1, "x2": 2, "y2": 2, "confidence": c} for f, c in frames_conf}}


def test_ball_coverage_and_composite():
    # 100 frames: 18 real ball detections, 82 interpolated
    real = [(f, 0.8) for f in range(1, 19)]
    interp = [(f, 0.0) for f in range(19, 101)]
    ball = _ball(real + interp)
    tracks = {"frames": {f: [{"track_id": (f % 30) + 1}] for f in range(1, 101)}}  # 30 unique ids
    res = compute_reliability(ball, tracks, total_frames=100)
    v = res.value
    assert v["ball_coverage"] == 0.18                      # the honest ~18% number
    assert v["interpolation_ratio"] > 0.8                  # most of the ball track is synthetic
    assert v["n_tracks"] == 30
    assert v["tracking_stability"] < 1.0                   # 30 ids > 22 expected → fragmented
    assert v["composite_for_ball_events"] <= v["ball_coverage"] + 1e-9


def test_high_quality_input_scores_well():
    # ball real on every frame, exactly 22 tracks, homography perfect
    ball = _ball([(f, 0.9) for f in range(1, 23)])
    tracks = {"frames": {f: [{"track_id": i} for i in range(1, 23)] for f in range(1, 23)}}
    res = compute_reliability(ball, tracks, total_frames=22, homography_conf=1.0)
    v = res.value
    assert v["ball_coverage"] == 1.0
    assert v["tracking_stability"] == 1.0
    assert v["composite_for_physical"] == 1.0
