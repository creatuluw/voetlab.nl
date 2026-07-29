"""P4 — team classification (HSV KMeans). Synthetic two-color frames → two teams."""
import numpy as np

from voetlab.tracking.team_classifier import classify_teams, extract_torso_hsv


def _two_color_frame():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[:, :100] = (200, 0, 0)   # left half = blue (BGR)
    frame[:, 100:] = (0, 0, 200)   # right half = red (BGR)
    return frame


def _track(tid, x1):
    return {"track_id": tid, "x1": x1, "y1": 10, "x2": x1 + 50, "y2": 120}


def test_two_teams_split_by_color():
    tracks = {"frames": {1: [_track(1, 10), _track(2, 110)]}}  # t1 on blue, t2 on red
    res = classify_teams("video", tracks, sample_frames=1, frame_source=[(1, _two_color_frame())])
    assert res.ok
    teams = res.value["teams"]
    assert teams[1] != teams[2]  # different colors → different teams


def test_extract_torso_hsv_returns_hue():
    h = extract_torso_hsv(_two_color_frame(), _track(1, 10))  # blue region
    assert h is not None and len(h) == 2


def test_fail_when_too_few_tracks():
    res = classify_teams("video", {"frames": {1: [_track(1, 10)]}}, sample_frames=1,
                         frame_source=[(1, _two_color_frame())])
    assert not res.ok  # need >=2 tracks to form 2 teams
