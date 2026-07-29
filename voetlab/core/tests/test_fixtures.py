"""F3 — footage harness + artifact dumping (canonical clip: football-1.mp4)."""
import json
from pathlib import Path

import pytest

from voetlab.core.fixtures import (
    DEFAULT_FOOTAGE,
    dump_artifacts,
    footage_meta,
    load_sample_frames,
)

HAS_FOOTAGE = Path(DEFAULT_FOOTAGE).exists()


def test_load_sample_frames():
    if not HAS_FOOTAGE:
        pytest.skip("football-1.mp4 not found at DEFAULT_FOOTAGE")
    frames = load_sample_frames(3)
    assert len(frames) == 3
    assert frames[0].shape[0] == 1080 and frames[0].shape[1] == 1920


def test_footage_meta():
    if not HAS_FOOTAGE:
        pytest.skip("football-1.mp4 not found at DEFAULT_FOOTAGE")
    meta = footage_meta()
    assert meta["frame_count"] > 0
    assert meta["fps"] > 0


def test_dump_artifacts_writes_files(tmp_path):
    import numpy as np

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    d = dump_artifacts("demo", frames=[frame], data={"x": 1, "list": [1, 2]}, out_root=tmp_path)
    assert (d / "annotated.png").exists()
    assert (d / "results.json").exists()
    payload = json.loads((d / "results.json").read_text())
    assert payload["x"] == 1 and payload["list"] == [1, 2]
