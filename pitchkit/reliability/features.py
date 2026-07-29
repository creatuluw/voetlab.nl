"""Reliability feature — per-stat confidence from ball/track quality signals.

Registered as feature "reliability" (deps: ball, track). Surfaces the PREDA "reliability
signal on every number" automatically in every pipeline run.
"""
from __future__ import annotations

from pitchkit.core.result import Result
from pitchkit.pipeline.registry import feature
from pitchkit.pipeline.runner import PipelineState
from pitchkit.reliability.reliability import compute_reliability


@feature("reliability", deps=["ball", "track"])
def _reliability_feature(state: PipelineState) -> Result:
    ball = state.get("ball")
    track = state.get("track")
    if not ball or not track:
        return Result.Fail("reliability needs upstream ball + track", feature="reliability")
    meta = state.meta or {}
    total = meta.get("total_frames") or len(ball.get("frames", {}))
    return compute_reliability(ball, track, total_frames=max(1, total))
