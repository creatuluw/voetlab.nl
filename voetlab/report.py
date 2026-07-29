"""End-to-end report: run the pipeline → stats.json + reliability.json + viz figures.

CLI: ``python -m voetlab.report <video> [--max-frames N] [--out DIR] [--ball-model-path P]``
Python: ``voetlab.report("football-1.mp4", "out", max_frames=50, meta={...})``
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

from voetlab.core.result import Result


def report(video, out_dir, *, max_frames: Optional[int] = None, meta: Optional[dict] = None,
           features: Optional[list[str]] = None, progress: Optional[Callable[[dict], None]] = None,
           result: Optional[Result] = None):
    """Run the full pipeline on ``video`` and write a report folder.

    Writes ``summary.json``, ``stats.json``, ``reliability.json`` and (best-effort) viz
    figures ``radar.png`` / ``pass_network.png`` / ``heatmap.png``. Returns ``(Result, Path)``.

    Pass ``result=`` to reuse an already-computed pipeline ``Result`` (no re-run) — the iii
    worker calls ``voetlab.run()`` with a progress callback, then hands the ``Result`` here
    so the GPU-heavy pipeline runs exactly once. ``features``/``progress`` are forwarded to
    ``run()`` only when ``result`` is None.
    """
    from voetlab.pipeline.default import run

    res = result if result is not None else run(video, max_frames=max_frames, meta=meta,
                                                 features=features, progress=progress)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = res.value.get("data", {}) if res.ok else {}
    summary = {
        "ok": res.ok,
        "failed": (res.value.get("failed") if res.ok else [res.error]),
        "features_run": res.meta.get("features_run"),
    }
    if (stats := data.get("stats")) is not None:
        (out / "stats.json").write_text(json.dumps(stats, indent=2, default=str))
    if (rel := data.get("reliability")) is not None:
        (out / "reliability.json").write_text(json.dumps(rel, indent=2, default=str))
    fig_errors = _write_figures(data, out)
    if fig_errors:
        summary["figure_errors"] = fig_errors
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return res, out


def _avg_positions(track):
    sums: dict = {}
    for pl in (track or {}).get("frames", {}).values():
        for p in pl:
            tid = p["track_id"]
            x = (p["x1"] + p["x2"]) / 2.0
            y = p["y2"]
            d = sums.setdefault(tid, [0.0, 0.0, 0])
            d[0] += x
            d[1] += y
            d[2] += 1
    return {tid: (s[0] / s[2], s[1] / s[2]) for tid, s in sums.items() if s[2]}


def _write_figures(data, out):
    import matplotlib.pyplot as plt

    from voetlab.viz.charts import heatmap, pass_network, radar

    errors = {}
    stats = data.get("stats") or {}
    players = stats.get("players", {})

    # radar — always possible from per-player stats (the reliable figure)
    try:
        if players:
            params = ["distance_px", "top_speed_px_s", "passes_made", "possession_frames"]
            rows = [(pid, [float(p.get(k, 0)) for k in params]) for pid, p in players.items()]
            highs = [max((r[1][i] for r in rows), default=1.0) or 1.0 for i in range(len(params))]
            top = max(rows, key=lambda r: r[1][0])
            fig = radar(params, top[1], [0.0] * len(params), highs)
            fig.savefig(out / "radar.png", dpi=80, bbox_inches="tight")
            plt.close(fig)
    except Exception as exc:  # noqa: BLE001
        errors["radar"] = f"{type(exc).__name__}: {exc}"

    # pass network + heatmap — positions are pixel; normalize to the statsbomb pitch
    # (approximate unless calibration provided a real homography).
    try:
        avg = _avg_positions(data.get("track"))
        if avg:
            xs = [p[0] for p in avg.values()]
            ys = [p[1] for p in avg.values()]
            w = max(xs) or 1.0
            h = max(ys) or 1.0
            norm = {tid: (x / w * 120.0, y / h * 80.0) for tid, (x, y) in avg.items()}
            passes = (data.get("events") or {}).get("passes", [])
            if passes:
                fig = pass_network(norm, [(p["from_track_id"], p["to_track_id"]) for p in passes])
                fig.savefig(out / "pass_network.png", dpi=80, bbox_inches="tight")
                plt.close(fig)
            fig = heatmap(list(norm.values()))
            fig.savefig(out / "heatmap.png", dpi=80, bbox_inches="tight")
            plt.close(fig)
    except Exception as exc:  # noqa: BLE001
        errors["spatial"] = f"{type(exc).__name__}: {exc}"
    return errors


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(prog="voetlab.report")
    ap.add_argument("video")
    ap.add_argument("--out", default="voetlab_report")
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--ball-model-path", default=None)
    ap.add_argument("--calib-checkpoint", default=None)
    ap.add_argument("--tvcalib-path", default="external/tvcalib")
    a = ap.parse_args(argv)
    meta = {"tvcalib_path": a.tvcalib_path}
    if a.ball_model_path:
        meta["ball_model_path"] = a.ball_model_path
    if a.calib_checkpoint:
        meta["calib_checkpoint"] = a.calib_checkpoint
    res, out = report(a.video, a.out, max_frames=a.max_frames, meta=meta)
    print(f"[voetlab.report] ok={res.ok} -> {out / 'summary.json'}")
    return 0 if res.ok else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
