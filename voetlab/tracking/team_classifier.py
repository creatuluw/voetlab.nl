"""P4 — team classification (KMeans k=2 on median HSV torso color).

Consumes the ``track`` feature's person tracks + the source video frames; assigns each
``track_id`` to team ``"A"`` or ``"B"``. Registered as feature ``"teams"`` (deps: ``["track"]``).

HSV hue-circularity + per-track majority vote = T1/T2, later.
"""
# === Quality & when to use (for devs / LLMs) ===
# What:  classify_teams() — KMeans k=2 on median HSV torso color; extract_torso_hsv().
# Does:  maps each track_id → "A"/"B" (feature "teams"); consumes "track"; needs the VIDEO.
# GOOD:  unsupervised 2-team split when kits are two clearly different colors; no roster.
# WEAK:  (1) hue is CIRCULAR so red (hue ~0 and ~180) splits wrongly; (2) k=2 can't also
#        separate GKs + referees; (3) no per-track majority vote → a player's label can
#        flip frame to frame.
# When:  feature "teams", after "track"; inject frame_source= in tests (no real video).
# Upgrade: T1 hue cos/sin + k>=4, T2 per-track majority vote, T3 GK/referee filter.

from __future__ import annotations

from typing import Callable, Iterable

import numpy as np

from voetlab.core.result import Result
from voetlab.pipeline.registry import feature
from voetlab.pipeline.runner import PipelineState


def extract_torso_hsv(frame, box: dict) -> list[float] | None:
    """Median (H, S) of the torso core band of ``box`` on ``frame`` (None if unusable)."""
    import cv2

    h0, w0 = frame.shape[:2]
    x, y = int(box["x1"]), int(box["y1"])
    w, h = int(box["x2"] - box["x1"]), int(box["y2"] - box["y1"])
    tt, tb = y + int(h * 0.2), y + int(h * 0.5)
    tl, tr = x + int(w * 0.2), x + int(w * 0.8)
    tt, tb = max(0, tt), min(h0, tb)
    tl, tr = max(0, tl), min(w0, tr)
    if tl >= tr or tt >= tb:
        return None
    crop = frame[tt:tb, tl:tr]
    if crop.size == 0 or crop.shape[0] < 3 or crop.shape[1] < 3:
        return None
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    return [float(np.median(hsv[:, :, 0])), float(np.median(hsv[:, :, 1]))]


def stabilize_team_labels(per_frame_teams: dict) -> dict:
    """Per-track MAJORITY vote: collapse flickering frame-level team labels to one per track (T2).

    Input: ``{track_id: [team_label_per_frame, ...]}``. Ties broken deterministically (insertion order).
    """
    from collections import Counter

    out = {}
    for tid, labels in per_frame_teams.items():
        out[tid] = Counter(labels).most_common(1)[0][0] if labels else None
    return out


def _default_frame_source(video, max_frame: int):
    """Yield (frame_no, frame) by reading the video sequentially up to ``max_frame``."""
    import cv2

    cap = cv2.VideoCapture(video)
    f = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        f += 1
        if f > max_frame:
            break
        yield f, frame
    cap.release()


def _hue_circular(hs):
    """Map [H(0-180), S] → [cos, sin, S] so wrapped hues (red ~0 and ~180) cluster together."""
    ang = 2.0 * np.pi * hs[0] / 180.0
    return [float(np.cos(ang)), float(np.sin(ang)), float(hs[1])]


def cluster_teams_hsv(samples, k: int = 2, circular: bool = True) -> list[int]:
    """KMeans on HSV samples. circular=True (default) fixes the red-jersey hue wrap (T1)."""
    from sklearn.cluster import KMeans

    samples = np.asarray(samples, dtype=float)
    feats = [_hue_circular(s) if circular else [s[0], s[1]] for s in samples]
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(feats)
    return [int(x) for x in km.labels_]


def classify_teams(
    video,
    tracks_value,
    *,
    sample_frames: int = 100,
    frame_source: Iterable | None = None,
    k: int = 2,
) -> Result:
    """Assign each track_id to a team via KMeans on median torso HSV.

    ``frame_source`` is injectable: an iterable of ``(frame_no, frame)`` so tests don't
    need real video.
    """
    from sklearn.cluster import KMeans

    frames_in = tracks_value.get("frames", {}) if isinstance(tracks_value, dict) else {}

    track_colors: dict[int, list[list[float]]] = {}
    src = frame_source if frame_source is not None else _default_frame_source(video, sample_frames)
    for f, frame in src:
        if f > sample_frames:
            break
        for t in frames_in.get(f, []):
            c = extract_torso_hsv(frame, t)
            if c:
                track_colors.setdefault(t["track_id"], []).append(c)

    if len(track_colors) < k:
        return Result.Fail(f"not enough tracks with usable color ({len(track_colors)})", feature="teams")

    ids = list(track_colors)
    mean_colors = np.array([np.median(track_colors[i], axis=0) for i in ids])
    labels = cluster_teams_hsv(mean_colors, k=k, circular=True)  # T1: circular hue encoding
    mapping = {ids[i]: ("A" if labels[i] == 0 else "B") for i in range(len(ids))}

    return Result.Ok({"teams": mapping}, feature="teams", tracks=len(ids), k=k)


@feature("teams", deps=["track"])
def _teams_feature(state: PipelineState) -> Result:
    tracks = state.get("track")
    if not tracks:
        return Result.Fail("upstream track missing", feature="teams")
    meta = state.meta or {}
    return classify_teams(state.footage, tracks, sample_frames=meta.get("sample_frames", 100))
