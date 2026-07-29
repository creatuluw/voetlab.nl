"""T3 — referee/goalkeeper role filter. Synthetic tracks (no footage)."""
from voetlab.core.result import Result
from voetlab.pipeline.registry import get_feature
from voetlab.pipeline.runner import run_feature
from voetlab.tracking.role_filter import classify_roles


def _t(track_id, x1, y1, x2, y2, conf=0.9):
    return {"track_id": track_id, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "confidence": conf}


def _tracks_with(*track_specs):
    """Build {"frames": {f: [boxes]}} from per-track (track_id, centroid_xs) specs.

    Each spec is (track_id, [centroid_x, ...]); a box of fixed height/width is centered on
    each centroid_x, one entry per frame. All tracks share the same frame range.
    """
    n_frames = max(len(spec[1]) for spec in track_specs)
    frames: dict[int, list[dict]] = {}
    for f in range(1, n_frames + 1):
        frames[f] = []
        for tid, xs in track_specs:
            if f <= len(xs):
                cx = xs[f - 1]
                frames[f].append(_t(tid, cx - 40, 200, cx + 40, 400))
    return {"frames": frames}


def test_classify_gk_referee_player():
    # GK: glued to the left edge (centroid ~120, well within the 12% band → 0.12*1920≈230).
    # Referee: roams full width across all 10 frames (spread 100→1820 = 1720 ≫ 0.5*1920).
    # Player: hovers mid-pitch (centroid ~950, small spread, never in an edge band).
    tracks = _tracks_with(
        (1, [120] * 10),                              # left-edge → gk
        (2, [100 + i * 191 for i in range(10)]),      # 100..1819 → referee
        (3, [950 + (i % 3) for i in range(10)]),      # ~950 mid → player
    )
    res = classify_roles(tracks)
    assert isinstance(res, Result) and res.ok
    roles = res.value["roles"]
    assert roles[1] == "gk"
    assert roles[2] == "referee"
    assert roles[3] == "player"
    # diagnostics carry the per-role counts + the width the thresholds used
    assert res.meta["goalkeepers"] == 1
    assert res.meta["referees"] == 1
    assert res.meta["players"] == 1
    assert res.meta["tracks"] == 3
    assert res.meta["width"] == 1920


def test_classify_right_edge_gk():
    # A keeper on the RIGHT edge band should also classify as gk (symmetry check).
    tracks = _tracks_with((7, [1810] * 8))  # 1810 ≥ 1920-230 → right edge
    res = classify_roles(tracks)
    assert res.ok and res.value["roles"][7] == "gk"


def test_classify_fail_on_empty():
    assert not classify_roles({"frames": {}}).ok
    assert not classify_roles({}).ok


def test_width_override_changes_bands():
    # At width=1000 the edge band is 120px; a centroid at 200 is no longer "edge" → player,
    # whereas at default 1920 (edge 230) the same centroid stays a GK.
    tracks = _tracks_with((5, [200] * 8))
    assert classify_roles(tracks, width=1000).value["roles"][5] == "player"
    assert classify_roles(tracks).value["roles"][5] == "gk"


def test_roles_feature_registered_and_isolated():
    # The @feature("roles", deps=["track"]) wrapper reads state.get("track").
    assert get_feature("roles").deps == ("track",)
    tracks = _tracks_with(
        (1, [120] * 10),
        (2, [100 + i * 191 for i in range(10)]),
        (3, [950 + (i % 3) for i in range(10)]),
    )
    res = run_feature("roles", data={"track": tracks})  # true isolation: deps pre-filled
    assert res.ok
    assert res.value["roles"] == {1: "gk", 2: "referee", 3: "player"}
