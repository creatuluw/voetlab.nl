"""F2 — frame provenance: every event traces back to the frame(s) it came from."""
import pytest

from pitchkit.core.provenance import attach_provenance


def test_attaches_source_frames():
    e = attach_provenance({"type": "pass", "from_id": 7, "to_id": 9}, source_frames=[42, 43])
    assert e["source_frames"] == [42, 43]
    assert e["type"] == "pass"  # original fields preserved


def test_rejects_empty_source_frames():
    with pytest.raises(ValueError):
        attach_provenance({"type": "pass"}, source_frames=[])


def test_extra_refs_attached():
    e = attach_provenance({"type": "tackle"}, source_frames=[10], track_ids=[3, 4], note="duel")
    assert e["source_frames"] == [10]
    assert e["track_ids"] == [3, 4]
    assert e["note"] == "duel"


def test_returns_same_dict_in_place():
    ev = {"type": "pass"}
    out = attach_provenance(ev, source_frames=[1])
    assert out is ev  # modifies in place AND returns it
