"""F0 — standalone package import smoke test.

Red until `voetlab/` exists; green once the package + all domain subpackages import.
Run: `python -m pytest voetlab/tests/test_imports.py -q`
"""
import importlib

import pytest

SUBPACKAGES = [
    "core",
    "detection",
    "tracking",
    "calibration",
    "events",
    "stats",
    "tactics",
    "reliability",
    "viz",
    "pipeline",
]


def test_top_level_import():
    import voetlab

    assert hasattr(voetlab, "__version__")
    assert voetlab.__version__


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackages_import(name):
    importlib.import_module(f"voetlab.{name}")
