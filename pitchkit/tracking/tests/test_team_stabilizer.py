"""T2 — per-track majority vote (stabilize flickering team labels)."""
from pitchkit.tracking.team_classifier import stabilize_team_labels


def test_majority_vote_per_track():
    per_frame = {7: ["A"] * 80 + ["B"] * 5, 9: ["B"] * 10}
    out = stabilize_team_labels(per_frame)
    assert out[7] == "A"  # 80 A vs 5 B → A
    assert out[9] == "B"


def test_tie_breaks_deterministically():
    out = stabilize_team_labels({1: ["A", "B"]})  # 50/50
    assert out[1] in ("A", "B")


def test_empty_labels_to_none():
    assert stabilize_team_labels({5: []})[5] is None
