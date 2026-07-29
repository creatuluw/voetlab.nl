"""T12 — Voronoi / dominant-region territory tests.

Synthetic 11-v-11; no models, no footage. Validates coverage (sum ≈ pitch area),
territory dominance (spread team > clustered team), and ratio bounds.
"""

from voetlab.tactics.voronoi import dominant_regions, team_area_ratio

PITCH = (105.0, 68.0)


def _team(team, xs, ys):
    return [{"x": x, "y": y, "team": team} for x, y in zip(xs, ys)]


def test_total_area_approximates_pitch_area():
    # 11 v 11 spread across the whole pitch
    a = _team("A", [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 52], [34] * 11)
    b = _team(
        "B",
        [5, 15, 25, 35, 45, 55, 65, 75, 85, 95, 50],
        [10, 20, 30, 40, 50, 60, 15, 25, 45, 55, 34],
    )
    res = dominant_regions(a + b, pitch_m=PITCH, step=1.0)
    total = sum(res["areas_m2"].values())
    pitch_area = PITCH[0] * PITCH[1]
    assert abs(total - pitch_area) / pitch_area < 0.02
    assert abs(res["total_m2"] - pitch_area) / pitch_area < 0.02


def test_clustered_team_has_smaller_area_than_spread_team():
    # Team A: 11 players clustered in a tight bunch on the left half
    a = _team(
        "A",
        [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 34],
    )
    # Team B: 11 players spread evenly across the whole pitch
    b = _team(
        "B",
        [20 + i * 8 for i in range(11)],          # x: 20..100
        [10 + (i % 5) * 12 for i in range(11)],    # y: 10..58
    )
    res = dominant_regions(a + b, pitch_m=PITCH, step=1.0)
    assert res["areas_m2"]["A"] < res["areas_m2"]["B"]


def test_team_area_ratio_in_unit_interval():
    a = _team("A", [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 52], [34] * 11)
    b = _team(
        "B",
        [5, 15, 25, 35, 45, 55, 65, 75, 85, 95, 50],
        [10, 20, 30, 40, 50, 60, 15, 25, 45, 55, 34],
    )
    r = team_area_ratio(a + b, pitch_m=PITCH)
    assert 0.0 <= r <= 1.0
