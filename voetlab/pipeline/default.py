"""P7 — default pipeline wiring + single-feature isolation.

Importing this module registers every feature (their ``@feature`` decorators run), so
``run(video)`` executes the full detect→track→ball→teams→events→stats chain in dependency
order, threading results through ``PipelineState``. ``run_feature(name, video)`` isolates
one feature so you can inspect its results alone.
"""
from __future__ import annotations

from typing import Callable, Optional

from voetlab.core.result import Result
from voetlab.pipeline import runner

# Importing the feature modules registers them (module-level @feature decorator).
from voetlab.detection import detect as _detect  # noqa: F401
from voetlab.tracking import player_tracker as _player_tracker  # noqa: F401
from voetlab.tracking import ball_tracker as _ball_tracker  # noqa: F401
from voetlab.tracking import team_classifier as _team_classifier  # noqa: F401
from voetlab.events import events as _events  # noqa: F401
from voetlab.stats import stats as _stats  # noqa: F401
from voetlab.calibration import features as _calib_features  # noqa: F401  (registers "calibrate")
from voetlab.tactics import features as _tactics_features  # noqa: F401  (registers voronoi/pitch_control)
from voetlab.reliability import features as _reliability_features  # noqa: F401  (registers "reliability")

DEFAULT_FEATURES = ["detect", "track", "ball", "teams", "events", "stats", "reliability"]


def run(video, *, max_frames: Optional[int] = None, meta: Optional[dict] = None,
        features: Optional[list[str]] = None,
        progress: Optional[Callable[[dict], None]] = None) -> Result:
    """Run the full pipeline (or a feature subset) over ``video``.

    ``progress`` is an optional ``callable(event: dict) -> None`` forwarded to the runner;
    it receives stage/frame events (see ``voetlab.pipeline.runner.run``). Default ``None``
    keeps the original zero-overhead behavior.

    Returns ``Result`` whose ``value`` is ``{"data", "failed", "results"}`` — each
    feature's output is in ``value["data"][name]``; failed features are in ``value["failed"]``.
    """
    m = dict(meta or {})
    if max_frames is not None:
        m["max_frames"] = max_frames
    names = list(features) if features else list(DEFAULT_FEATURES)
    # When a specialist ball model is supplied, run the high-recall detect_ball before "ball"
    # so events/stats consume ~98%-coverage ball data instead of COCO class-32 (~1%).
    if m.get("ball_model_path") and "ball" in names and "detect_ball" not in names:
        names.insert(names.index("ball"), "detect_ball")
    # When a calibration checkpoint is supplied, run "calibrate" before the metric features so
    # state.meta["H"] is set and stats/voronoi/pitch_control produce meters + tactical output.
    if m.get("calib_checkpoint") and "calibrate" not in names:
        for tgt in ("stats", "voronoi", "pitch_control"):
            if tgt in names:
                names.insert(names.index(tgt), "calibrate")
                break
        else:
            names.append("calibrate")
    return runner.run(names=names, footage=video, meta=m, progress=progress)


def run_feature(name: str, video, *, meta: Optional[dict] = None,
                progress: Optional[Callable[[dict], None]] = None) -> Result:
    """Run ONE feature in isolation (optionally pre-fill upstream via ``meta``)."""
    return runner.run_feature(name, footage=video, meta=dict(meta or {}), progress=progress)
