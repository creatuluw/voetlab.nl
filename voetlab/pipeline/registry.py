"""Feature registry.

Features register as nodes — ``(name, deps, fn)`` — where ``fn(state) -> Result``.
The runner executes them in dependency order; downstream features read upstream
outputs from ``state``. This is the pluggable core of the framework.

Example::

    @feature("detect", deps=[])
    def detect(state: PipelineState) -> Result:
        ...
    @feature("track", deps=["detect"])
    def track(state) -> Result:
        boxes = state.get("detect")   # upstream output
        ...
"""
from __future__ import annotations

from typing import Callable, Sequence


class Feature:
    """A registered pipeline node."""

    __slots__ = ("name", "fn", "deps")

    def __init__(self, name: str, fn: Callable, deps: Sequence[str] = ()):
        self.name = name
        self.fn = fn
        self.deps = tuple(deps)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Feature({self.name!r}, deps={self.deps})"


# Global registry. Features register at import time (module-level @feature decorator).
_FEATURES: "dict[str, Feature]" = {}


def feature(name: str, deps: Sequence[str] = ()):
    """Decorator: register ``fn`` as feature ``name`` with optional upstream ``deps``."""

    def deco(fn: Callable):
        _FEATURES[name] = Feature(name, fn, deps)
        return fn

    return deco


def get_feature(name: str) -> Feature:
    return _FEATURES[name]


def registered() -> list[str]:
    return list(_FEATURES)


def all_features() -> "dict[str, Feature]":
    return dict(_FEATURES)
