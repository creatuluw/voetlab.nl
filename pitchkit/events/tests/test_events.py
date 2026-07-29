"""P5 — events (possession/passes/tackles) with frame provenance.

Every event must carry non-empty `source_frames` (the "trace back to frames" requirement).
"""


def _player(tid, fx, fy):
    return {"track_id": tid, "x1": fx - 20, "y1": fy - 100, "x2": fx + 20, "y2": fy}


def _ball(cx, cy):
    return {"x1": cx - 5, "y1": cy - 5, "x2": cx + 5, "y2": cy + 5, "confidence": 0.8}


def test_pass_detected_with_provenance():
    from pitchkit.events.events import detect_events

    tracks = {"frames": {**{f: [_player(1, 100, 200)] for f in [1, 2, 3]},
                         **{f: [_player(2, 300, 200)] for f in [4, 5, 6]}}}
    ball = {"frames": {**{f: _ball(100, 200) for f in [1, 2, 3]},
                       **{f: _ball(300, 200) for f in [4, 5, 6]}}}
    teams = {"teams": {1: "A", 2: "A"}}
    res = detect_events(tracks, ball, teams)
    assert res.ok
    assert len(res.value["passes"]) >= 1
    p = res.value["passes"][0]
    assert p["from_team"] == "A" and p["to_team"] == "A"
    assert p["source_frames"] and p["source_frames"][0] in [4, 5, 6]


def test_tackle_turnover_has_provenance():
    from pitchkit.events.events import detect_events

    # both players present at the change frame, close together → tackle
    tracks = {"frames": {**{f: [_player(1, 100, 200)] for f in [1, 2, 3]},
                         **{f: [_player(1, 100, 200), _player(2, 120, 200)] for f in [4, 5, 6]}}}
    ball = {"frames": {**{f: _ball(100, 200) for f in [1, 2, 3]},
                       **{f: _ball(120, 200) for f in [4, 5, 6]}}}
    teams = {"teams": {1: "A", 2: "B"}}
    res = detect_events(tracks, ball, teams)
    assert res.ok
    assert len(res.value["tackles"]) >= 1
    t = res.value["tackles"][0]
    assert t["source_frames"]
    assert t["type"] == "tackle"


def test_no_ball_no_events():
    from pitchkit.events.events import detect_events

    res = detect_events({"frames": {1: [_player(1, 100, 200)]}}, {"frames": {1: None}}, {"teams": {1: "A"}})
    assert res.ok
    assert res.value["passes"] == [] and res.value["tackles"] == []
