"""T1 — HSV hue circularity fix for team classification.

Red wraps around hue (H≈0 AND H≈180 in OpenCV). Raw-Euclidean KMeans splits one red team
into two clusters; circular (cos/sin) encoding clusters them together.
"""
from pitchkit.tracking.team_classifier import cluster_teams_hsv


def test_circular_hue_clusters_wrapped_red():
    # [H, S]: two reds at opposite hue ends + two blues
    samples = [[5, 200], [175, 200], [110, 200], [112, 200]]
    labels = cluster_teams_hsv(samples, circular=True)
    assert labels[0] == labels[1], "wrapped reds (H=5 and H=175) must cluster together"
    assert labels[2] == labels[3], "blues must cluster together"
    assert labels[0] != labels[2]


def test_linear_huv_dims_used_when_disabled():
    samples = [[5, 200], [175, 200], [110, 200], [112, 200]]
    labels = cluster_teams_hsv(samples, circular=False)  # legacy linear behaviour
    assert len(labels) == 4  # still produces a label per sample
