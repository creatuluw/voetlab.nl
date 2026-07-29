"""T13 — viz adapters return matplotlib Figures (headless Agg backend)."""
import matplotlib.figure

from pitchkit.viz.charts import heatmap, pass_network, radar


def test_heatmap_returns_figure():
    fig = heatmap([(60, 40), (70, 40), (60, 40), (65, 42)])
    assert isinstance(fig, matplotlib.figure.Figure)


def test_pass_network_returns_figure():
    fig = pass_network({1: (40, 30), 2: (60, 30), 3: (50, 50)}, [(1, 2), (1, 2), (3, 1)])
    assert isinstance(fig, matplotlib.figure.Figure)


def test_radar_returns_figure():
    fig = radar(["Speed", "Pass", "Shot"], [5, 7, 3], [0, 0, 0], [10, 10, 10])
    assert isinstance(fig, matplotlib.figure.Figure)
