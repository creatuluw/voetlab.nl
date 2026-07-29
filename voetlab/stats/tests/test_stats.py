"""P6 — physical + aggregate stats (port of analytics_agent)."""


def _p(tid, fx, fy):
    return {"track_id": tid, "x1": fx - 20, "y1": fy - 100, "x2": fx + 20, "y2": fy}


def test_physical_stats_for_moving_player():
    from voetlab.stats.stats import compute_stats

    tracks = {"frames": {1: [_p(1, 100, 200)], 2: [_p(1, 110, 200)], 3: [_p(1, 120, 200)]}}
    teams = {"teams": {1: "A"}}
    events = {"possession": [], "passes": [], "tackles": [], "interceptions": []}
    res = compute_stats(tracks, teams, events, fps=25)
    assert res.ok
    st = res.value["players"][1]
    assert st["distance_px"] > 0
    assert st["top_speed_px_s"] > 0


def test_possession_aggregates_to_team():
    from voetlab.stats.stats import compute_stats

    tracks = {"frames": {1: [_p(1, 100, 200)], 2: [_p(1, 100, 200)]}}
    teams = {"teams": {1: "A"}}
    events = {
        "possession": [{"frame": 1, "track_id": 1, "team": "A", "distance": 5.0},
                       {"frame": 2, "track_id": 1, "team": "A", "distance": 5.0}],
        "passes": [], "tackles": [], "interceptions": [],
    }
    res = compute_stats(tracks, teams, events, fps=25)
    assert res.ok
    assert res.value["players"][1]["possession_frames"] == 2
    assert res.value["teams"]["A"]["possession_frames"] == 2
