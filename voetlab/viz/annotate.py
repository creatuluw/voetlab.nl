"""Annotated-video renderer — burns voetlab analysis onto each source frame.

Reads the per-frame data produced by a ``voetlab.run()`` Result
(``result.value["data"]``: keys "detect"/"track"/"ball"/"teams") and overlays it onto a
re-read of the source clip, writing a browser-streamable ``annotated.mp4``.

Best-effort by contract: a missing key or a bad frame is skipped, never raised — the
analysis run that produced ``result`` must not fail because rendering did.

Data shapes (confirmed against the features that emit them):
  data["track"] = {"frames": {frame_no(1-indexed): [{"track_id","x1","y1","x2","y2","confidence"}]}}
  data["ball"]  = {"frames": {frame_no: {"x1","y1","x2","y2","confidence"} | None}}
  data["teams"] = {"teams": {track_id: "A"|"B"}}
(``detect`` is superseded by ``track`` for player drawing; we draw tracks, not raw boxes.)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Two distinct BGR team colors (A vivid, B chalk-white) + a fallback for unclassified tracks.
_TEAM_COLORS = {
    "A": (0, 0, 255),      # BGR vivid red
    "B": (235, 235, 230),  # BGR chalk white
}
_TEAM_FALLBACK = (0, 255, 255)  # BGR yellow — track present but no team assignment
_BALL_COLOR = (0, 255, 255)     # BGR yellow filled circle
_BALL_RADIUS = 6


def _data(result: Any) -> dict:
    """Pull ``result.value["data"]`` defensively (a Result OR a raw value dict). Empty on any miss."""
    value = getattr(result, "value", result)
    data = value.get("data") if isinstance(value, dict) else None
    return data if isinstance(data, dict) else {}


def _draw_label(img, text: str, x: int, y: int, color) -> None:
    """Draw ``text`` with a filled background rect for readability (in place)."""
    import cv2

    (tw, th), bl = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(img, (x, y - th - bl - 2), (x + tw + 2, y), color, -1)
    cv2.putText(img, text, (x + 1, y - bl - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 0, 0), 1, cv2.LINE_AA)


def annotate_video(result, source, out_path, *, fps=None, draw_ball=True):
    """Burn voetlab analysis onto each frame of ``source`` → write ``out_path`` (mp4).

    Args:
        result:    a ``voetlab.run()`` ``Result`` (or its ``value`` dict) — reads
                   ``data["track"|"ball"|"teams"]`` when present.
        source:    path/clip of the source video (re-read for fidelity).
        out_path:  where to write the annotated mp4.
        fps:       override output fps; defaults to the source's reported fps.
        draw_ball: draw the ball marker per frame when ``ball`` data is present.

    Returns:
        ``Path(out_path)`` on success, ``None`` if the video can't be opened/written.
        Never raises — rendering failures degrade to "no annotated video", not a failed run.
    """
    import cv2

    try:
        data = _data(result)
        track_frames = ((data.get("track") or {}).get("frames")) or {}
        ball = data.get("ball") or {}
        ball_frames = (ball.get("frames") or {}) if draw_ball else {}
        teams = ((data.get("teams") or {}).get("teams")) or {}

        cap = cv2.VideoCapture(str(source))
        if not cap.isOpened():
            return None
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        out_fps = float(fps) if fps else float(cap.get(cv2.CAP_PROP_FPS) or 0)
        if not w or not h or not out_fps:
            cap.release()
            return None

        # ponytail: fixed 'mp4v' fourcc — broadly streamable in browsers (Chrome/Firefox/Safari);
        # no audio passthrough (source clips are vision-only). Swap to 'avc1' if a target browser
        # ever refuses mp4v, and accept the codec-availability dependency that adds.
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), out_fps, (w, h))
        if not writer.isOpened():
            cap.release()
            return None

        frame_no = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_no += 1  # voetlab frames are 1-indexed
            try:
                for t in track_frames.get(frame_no, []):
                    x1, y1 = int(t["x1"]), int(t["y1"])
                    x2, y2 = int(t["x2"]), int(t["y2"])
                    color = _TEAM_COLORS.get(teams.get(t.get("track_id")), _TEAM_FALLBACK)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    tid = t.get("track_id")
                    if tid is not None:
                        _draw_label(frame, str(tid), x1, max(y1, 12), color)
                b = ball_frames.get(frame_no)
                if b:
                    cx, cy = int((b["x1"] + b["x2"]) / 2), int((b["y1"] + b["y2"]) / 2)
                    cv2.circle(frame, (cx, cy), _BALL_RADIUS, _BALL_COLOR, -1, cv2.LINE_AA)
            except Exception:
                # ponytail: a bad frame's overlay is skipped; the raw frame is still written
                pass
            writer.write(frame)

        cap.release()
        writer.release()
    except Exception:
        return None

    p = Path(out_path)
    return p if p.exists() and p.stat().st_size > 0 else None
