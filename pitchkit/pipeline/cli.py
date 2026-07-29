"""CLI: ``python -m pitchkit.pipeline.cli <video> [--feature NAME] [--max-frames N]``.

Runs the full pipeline by default, or a single feature in isolation with ``--feature``.
Dumps a ``results.json`` summary to ``pitchkit/tests/out/<tag>/`` for inspection.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pitchkit.core.fixtures import dump_artifacts
from pitchkit.pipeline import default


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pitchkit")
    p.add_argument("video", help="path to match video")
    p.add_argument("--feature", default=None,
                   help="run a single feature in isolation (e.g. detect, track, events, stats)")
    p.add_argument("--max-frames", type=int, default=None)
    p.add_argument("--sample-frames", type=int, default=None, help="frames used by team classification")
    p.add_argument("--out", default=None, help="artifact output dir (default: pitchkit/tests/out)")
    args = p.parse_args(argv)

    meta: dict = {}
    if args.max_frames is not None:
        meta["max_frames"] = args.max_frames
    if args.sample_frames is not None:
        meta["sample_frames"] = args.sample_frames

    if args.feature:
        res = default.run_feature(args.feature, args.video, meta=meta)
        tag = args.feature
    else:
        res = default.run(args.video, meta=meta)
        tag = "pipeline"

    payload = {"ok": res.ok, "error": res.error, "meta": res.meta, "value": res.value}
    out_dir = dump_artifacts(tag, data=payload, out_root=args.out) if args.out else dump_artifacts(tag, data=payload)
    print(f"[pitchkit] {tag}: ok={res.ok} -> {out_dir / 'results.json'}")

    if not res.ok:
        print(f"[pitchkit] FAILED: {res.error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
