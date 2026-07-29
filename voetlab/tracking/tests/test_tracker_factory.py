"""T9 — tracker factory config (pure)."""
import pytest

from voetlab.tracking.tracker_factory import build_tracker


def test_botsort_has_cmc_and_ultralytics_engine():
    c = build_tracker("botsort")
    assert c["engine"] == "ultralytics"
    assert c["tracker"].endswith("voetlab_botsort.yaml")  # shipped CMC-enabled config
    assert c["gmc_method"] == "sparseOptFlow"  # camera-motion compensation for pan/zoom


def test_shipped_botsort_yaml_has_cmc_enabled():
    from voetlab.tracking.tracker_factory import _BOTSORT_YAML
    txt = _BOTSORT_YAML.read_text()
    assert "gmc_method: sparseOptFlow" in txt  # the dead-code bug fix — CMC actually applied
    assert "with_reid: false" in txt


def test_reid_flag():
    assert build_tracker("botsort", reid=True)["with_reid"] is True
    assert build_tracker("botsort")["with_reid"] is False


def test_bytetrack_uses_supervision():
    assert build_tracker("bytetrack")["engine"] == "supervision"


def test_unknown_tracker_raises():
    with pytest.raises(ValueError):
        build_tracker("nope")
