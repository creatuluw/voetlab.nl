"""P2 — player tracking (ByteTrack). Synthetic detections → consistent track ids."""
from voetlab.detection.detect import BALL, PERSON
from voetlab.tracking.player_tracker import track_players


def _box(x1, y1, x2, y2, cls=PERSON, conf=0.9):
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "class": cls, "confidence": conf}


def test_track_assigns_consistent_ids_across_frames():
    det = {"frames": {1: [_box(100, 100, 140, 200)], 2: [_box(102, 100, 142, 200)], 3: [_box(104, 102, 144, 202)]}}
    res = track_players(det)
    assert res.ok
    ids1 = {p["track_id"] for p in res.value["frames"][1]}
    ids3 = {p["track_id"] for p in res.value["frames"][3]}
    assert ids1 and ids1 == ids3  # same persisting box → same id


def test_track_skips_non_person():
    det = {"frames": {1: [_box(100, 100, 140, 200), _box(500, 500, 510, 510, BALL, 0.5)]}}
    res = track_players(det)
    assert res.ok
    tracked = res.value["frames"][1]
    assert len(tracked) == 1  # only the person is tracked, not the ball
    assert "track_id" in tracked[0]


def test_track_fail_on_empty():
    res = track_players({"frames": {}})
    assert not res.ok
