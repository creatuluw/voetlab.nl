"""F4 — pipeline registry + runner: dep-order exec, failure flagging, single-feature
isolation, downstream threading, and before/after compare.

These tests use uniquely-named throwaway features (f4_*) and explicit `names=` so they
never clobber real feature registrations.
"""
import pytest

from voetlab.core.result import Result
from voetlab.pipeline import registry, runner


def test_register_and_topo_order():
    @registry.feature("f4_c", deps=["f4_a", "f4_b"])
    def c(state):
        return Result.Ok("C")

    @registry.feature("f4_b", deps=["f4_a"])
    def b(state):
        return Result.Ok("B")

    @registry.feature("f4_a")
    def a(state):
        return Result.Ok("A")

    res = runner.run(names=["f4_c", "f4_b", "f4_a"], footage=None)
    assert res.ok
    order = res.meta["features_run"]
    assert order.index("f4_a") < order.index("f4_b") < order.index("f4_c")
    assert res.value["data"]["f4_c"] == "C"


def test_failure_flagged_not_fatal():
    @registry.feature("f4_fa")
    def a(state):
        return Result.Fail("boom", feature="f4_fa")

    @registry.feature("f4_fb", deps=["f4_fa"])
    def b(state):
        if state.get("f4_fa") is None:  # upstream failed → no value
            return Result.Fail("upstream f4_fa missing", feature="f4_fb")
        return Result.Ok("B")

    res = runner.run(names=["f4_fa", "f4_fb"], footage=None)
    assert res.ok  # the pipeline itself completes
    assert set(res.value["failed"]) == {"f4_fa", "f4_fb"}


def test_downstream_reads_upstream():
    @registry.feature("f4_da")
    def a(state):
        return Result.Ok(7)

    @registry.feature("f4_db", deps=["f4_da"])
    def b(state):
        return Result.Ok(state.get("f4_da") * 2)

    res = runner.run(names=["f4_da", "f4_db"], footage=None)
    assert res.value["data"]["f4_db"] == 14  # b consumed a's output via state.get()


def test_run_feature_isolation():
    @registry.feature("f4_iso")
    def a(state):
        return Result.Ok("only-a")

    res = runner.run_feature("f4_iso", footage=None)
    assert res.ok and res.value == "only-a"


def test_run_feature_unknown():
    res = runner.run_feature("definitely_not_registered_xyz")
    assert not res.ok
    assert "unknown feature" in res.error


def test_compare_diff():
    d = runner.compare({"ball_coverage": 0.18, "events": 12}, {"ball_coverage": 0.62, "events": 41})
    assert d["ball_coverage"]["delta"] == pytest.approx(0.44)
    assert d["events"]["delta"] == 29
