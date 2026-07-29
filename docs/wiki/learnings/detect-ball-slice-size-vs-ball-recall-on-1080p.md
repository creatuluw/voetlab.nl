---
type: Learning
title: detect_ball slice_size vs ball recall on 1080p
description: The `detect_ball` (SAHI) stage's speed is dominated by the slice count, which is set by
tags: [detection, sahi, ball, performance, recall]
timestamp: "2026-07-29T21:13:06.246Z"
---

# detect_ball slice_size vs ball recall on 1080p

The `detect_ball` (SAHI) stage's speed is dominated by the slice count, which is set by
`slice_size` against the frame resolution. Measured on `football-1.mp4` (1920x1080), 40 frames,
martinjolif ball model, SAHI overlap 0.2:

| slice_size | slices | ms/frame | ball-rate (conf 0.15) | ball-rate (conf 0.10) |
|------------|--------|-----------|------------------------|------------------------|
| 512 (old)  | 15     | ~258      | 100%                   | 100%                   |
| 640        | 8      | ~163      | 78%                    | 90%                    |
| 768 (new)  | 6      | ~133      | 92%                    | 98%                    |
| 960        | 6      | ~150      | 85%                    | 95%                    |
| 1280       | 2      | —         | ~50%                   | —                      |

**Chosen default: `slice_size=768, conf=0.10`** — 6 slices (was 15), ~1.9x faster, ball-rate
held at ~98% (within the 10% recall budget). Two non-obvious facts:

1. **Why conf must drop to 0.10 as slices grow:** a 1920x1080 broadcast frame's ball is small;
   at larger `slice_size` the ball occupies a smaller fraction of each patch, so the model's
   confidence dips below the old 0.15 threshold and the ball is dropped. The specialist
   martinjolif model has high precision, so 0.10 adds essentially no false positives (box count
   stays ~104 vs baseline ~113).

2. **The "2–4 slices" target is NOT reachable on 1080p:** square-slice SAHI grids for 1920x1080
   step 15 → 12 → 8 → 6 → 2 (there is no 4-slice config). The 2-slice grid (slice_size>=1280)
   collapses ball recall to ~50% — the ball becomes too small per patch to detect. So 6 slices
   (768) is the recall-preserving floor.

Ceiling (also in the `# ponytail:` comment in detect.py): do not raise `slice_size` past 960
without re-measuring recall, and keep `conf <= 0.10` once slices grow. Both knobs stay
controllable via `meta["slice_size"]` / `meta["conf"]`. SAHI auto-collapses to a single
full-frame slice when `slice_size >= max(H, W)`, so genuinely small frames need no special
"skip-slicing" code.

Source: `voetlab/detection/detect.py` (`detect_ball_sahi`, `_run_sahi`).
