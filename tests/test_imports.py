"""F0 — standalone package import smoke test.

Red until `pitchkit/` exists; green once the package + all domain subpackages import.
Run: `python -m pytest pitchkit/tests/test_imports.py -q`
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
    import pitchkit

    assert hasattr(pitchkit, "__version__")
    assert pitchkit.__version__


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackages_import(name):
    importlib.import_module(f"pitchkit.{name}")
