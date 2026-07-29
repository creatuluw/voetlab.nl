"""Pipeline runner: dependency-order execution with shared state, failure flagging,
single-feature isolation, and a before/after ``compare()``.

Design points (matching the framework requirements):

* **Downstream visibility** — every feature's ``Result.value`` lands in
  ``state.data[name]``; downstream features read it via ``state.get(name)``. That is
  how results "carry on downstream".
* **Failure flagging** — a feature returning ``Result.Fail`` (or raising) is recorded
  in ``failed``; the run *continues* instead of crashing, so you can see every failure.
* **Single-feature isolation** — :func:`run_feature` runs exactly one node (optionally
  pre-filled with upstream ``data``) so you can inspect one feature's results in
  isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from pitchkit.core.result import Result
from pitchkit.pipeline.registry import _FEATURES


@dataclass
class PipelineState:
    """Shared clipboard threaded through a run.

    Attributes:
        footage: the video path / clip being analyzed.
        meta:    configuration (fps, conf, model paths, max_frames, ...).
        data:    upstream feature outputs, keyed by feature name (read via get()).
        results: every feature's full ``Result`` (ok/fail/error) for reporting.
    """

    footage: Any = None
    meta: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)

    def get(self, name: str, default: Any = None) -> Any:
        """Read an upstream feature's output value (None if it failed/absent)."""
        return self.data.get(name, default)


def _topo_order(names: list[str]) -> list[str]:
    order: list[str] = []
    seen: set[str] = set()
    visiting: set[str] = set()

    def visit(n: str) -> None:
        if n in seen:
            return
        if n in visiting:
            raise ValueError(f"dependency cycle involving feature {n!r}")
        if n not in _FEATURES:
            raise KeyError(f"unknown feature {n!r}")
        visiting.add(n)
        for dep in _FEATURES[n].deps:
            visit(dep)
        visiting.discard(n)
        seen.add(n)
        order.append(n)

    for n in names:
        visit(n)
    return order


def run(names: Optional[list[str]] = None, footage: Any = None, meta: Optional[dict] = None) -> Result:
    """Run features in dependency order, threading ``PipelineState``.

    Returns ``Result.Ok`` whose ``value`` is ``{"data", "failed", "results"}`` — the
    pipeline itself is considered to have run (even if some features failed); check
    ``value["failed"]`` for individual failures.
    """
    names = list(names) if names else list(_FEATURES)
    state = PipelineState(footage=footage, meta=dict(meta or {}))
    order = _topo_order(names)
    for name in order:
        try:
            res = _FEATURES[name].fn(state)
        except Exception as exc:  # a crashing feature is flagged, not fatal
            res = Result.Fail(f"{type(exc).__name__}: {exc}", feature=name)
        state.results[name] = res
        if res.ok:
            state.data[name] = res.value
    failed = [n for n, r in state.results.items() if not r.ok]
    return Result.Ok(
        value={
            "data": state.data,
            "failed": failed,
            "results": {k: {"ok": r.ok, "error": r.error} for k, r in state.results.items()},
        },
        features_run=order,
        failed=failed,
    )


def run_feature(
    name: str,
    footage: Any = None,
    meta: Optional[dict] = None,
    data: Optional[dict] = None,
) -> Result:
    """Run ONE feature in isolation.

    Pass ``data`` to pre-fill upstream outputs so a feature that declares deps can be
    exercised without re-running them (true isolation). Returns that feature's ``Result``.
    """
    if name not in _FEATURES:
        return Result.Fail(f"unknown feature: {name}", requested=name)
    state = PipelineState(footage=footage, meta=dict(meta or {}), data=dict(data or {}))
    try:
        return _FEATURES[name].fn(state)
    except Exception as exc:
        return Result.Fail(f"{type(exc).__name__}: {exc}", feature=name)


def compare(baseline: dict, current: dict) -> dict:
    """Diff two metric snapshots (e.g. baseline vs improved pipeline on the same footage).

    Returns ``{metric: {"baseline", "current", "delta"}}`` for numeric metrics.
    """
    out: dict = {}
    for key in sorted(set(baseline) | set(current)):
        b = baseline.get(key)
        c = current.get(key)
        delta = (c - b) if isinstance(b, (int, float)) and isinstance(c, (int, float)) else None
        out[key] = {"baseline": b, "current": c, "delta": delta}
    return out
