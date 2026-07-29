"""Provenance — trace every event back to the frame(s) it was captured from.

Every event-producing feature MUST call :func:`attach_provenance` so each event dict
carries a non-empty ``source_frames`` list (plus optional refs like ``track_ids`` or
bounding boxes). This is what lets you point at any event and answer "which frame(s)?".

Example::

    pass_event = attach_provenance(
        {"type": "pass", "from_id": 7, "to_id": 9},
        source_frames=[42, 43],
        track_ids=[7, 9],
    )
"""
from __future__ import annotations

from typing import Any, Iterable


def attach_provenance(event: dict, source_frames: Iterable[int], **refs: Any) -> dict:
    """Attach frame provenance (and optional refs) to ``event``; modify in place and return it.

    Args:
        event:         The event dict to annotate (mutated in place).
        source_frames: Frame index(es) the event was derived from. Must be non-empty.
        **refs:        Extra provenance refs (e.g. ``track_ids``, ``bbox``) attached verbatim.

    Returns:
        The same ``event`` dict, now carrying ``source_frames``.

    Raises:
        ValueError: if ``source_frames`` is empty (a frame-less event is meaningless).
    """
    frames = [int(f) for f in source_frames]
    if not frames:
        raise ValueError("source_frames must be non-empty — every event must trace to frame(s)")
    event["source_frames"] = frames
    for key, val in refs.items():
        event.setdefault(key, val)
    return event
