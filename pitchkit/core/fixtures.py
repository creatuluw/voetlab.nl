"""Footage-driven test harness + artifact dumping.

Canonical test footage: ``football-1.mp4`` (override with the ``PITCHKIT_FOOTAGE`` env
var, or place ``./football-1.mp4`` in the project root). Every feature's footage test
calls :func:`dump_artifacts` so a human can *see* results and pinpoint where to improve.

This module depends only on numpy + opencv (lazy-imported) — it stays out of the hot path.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

DEFAULT_FOOTAGE: str = os.environ.get("PITCHKIT_FOOTAGE", "football-1.mp4")

# Artifacts land under <pitchkit-project>/tests/out/<feature>/
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../pitchkit/
DEFAULT_OUT: Path = Path(os.environ.get("PITCHKIT_OUT", _PROJECT_ROOT / "tests" / "out"))


def load_sample_frames(n: int, path: str = DEFAULT_FOOTAGE, start: int = 0):
    """Read up to ``n`` BGR frames from ``path`` starting at frame index ``start``."""
    import cv2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FileNotFoundError(f"cannot open footage: {path!r}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    frames = []
    for _ in range(n):
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    return frames


def footage_meta(path: str = DEFAULT_FOOTAGE) -> dict[str, Any]:
    """Return {fps, frame_count, width, height} for ``path``."""
    import cv2

    cap = cv2.VideoCapture(path)
    meta = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    cap.release()
    return meta


def dump_artifacts(
    feature: str,
    frames=None,
    data: Optional[dict] = None,
    fig=None,
    out_root: Path | str = DEFAULT_OUT,
) -> Path:
    """Write inspectable artifacts for ``feature`` under ``<out_root>/<feature>/``.

    - ``frames``: list of BGR arrays → the first is saved as ``annotated.png``.
    - ``data``:   dict → ``results.json`` (JSON-serializable; uses ``default=str``).
    - ``fig``:    a matplotlib Figure → ``figure.png``.

    Returns the feature output directory. Open it to SEE what a feature produced.
    """
    d = Path(out_root) / feature
    d.mkdir(parents=True, exist_ok=True)

    if frames:
        import cv2

        cv2.imwrite(str(d / "annotated.png"), frames[0])

    if data is not None:
        (d / "results.json").write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    if fig is not None:
        fig.savefig(str(d / "figure.png"), dpi=100, bbox_inches="tight")

    return d
