"""F1 — Result success-indicator contract.

Red until `voetlab/core/result.py` exists; green once Result.Ok/Fail behave as the
universal success indicator every feature returns.
"""
from voetlab.core.result import Result


def test_ok_is_success():
    r = Result.Ok({"passes": 5}, feature="passes")
    assert r.ok is True
    assert bool(r) is True  # truthiness == success → pipeline branches on `if result:`
    assert r.value == {"passes": 5}
    assert r.error is None
    assert r.meta["feature"] == "passes"


def test_fail_is_failure():
    r = Result.Fail("no ball detections", feature="ball")
    assert r.ok is False
    assert bool(r) is False
    assert r.value is None
    assert r.error == "no ball detections"
    assert r.meta["feature"] == "ball"


def test_meta_defaults_empty():
    r = Result.Ok(1)
    assert r.meta == {}
