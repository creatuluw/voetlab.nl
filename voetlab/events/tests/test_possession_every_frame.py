"""T7 — possession is computed on EVERY frame when the ball is present every frame
(which the Kalman ball trajectory now guarantees), removing the old ~18% coverage bottleneck.
"""
from voetlab.events.events import detect_events


def _player(tid, fx, fy=200):
    return {"track_id": tid, "x1": fx - 20, "y1": fy - 100, "x2": fx + 20, "y2": fy}


def _ball(cx, cy=200):
    return {"x1": cx - 5, "y1": cy - 5, "x2": cx + 5, "y2": cy + 5, "confidence": 0.8}


def test_possession_covers_most_frames_when_ball_present_every_frame():
    n = 100
    tracks = {"frames": {f: [_player(1, 100, 200)] for f in range(1, n + 1)}}
    ball = {"frames": {f: _ball(100, 200) for f in range(1, n + 1)}}  # ball every frame
    res = detect_events(tracks, ball, {"teams": {1: "A"}})
    assert res.ok
    assert len(res.value["possession"]) >= int(n * 0.9)  # >90% of frames have a possession reading
