---
type: Learning
title: Models folder is an FTP deploy bundle, not the runtime source
description: The fact
tags: [models, weights, devops, ftp, gitignore, deployment]
timestamp: "2026-07-29T20:48:27.924Z"
---

# Models folder is an FTP deploy bundle, not the runtime source

## The fact

There is a top-level **`models/`** folder at the repo root holding **every** weight
the framework needs as one uploadable bundle (~506 MB total):

| File | Runtime `meta` key |
|------|--------------------|
| `yolov8s.pt` | `meta["model_path"]` |
| `martinjolif_ball.pt` | `meta["ball_model_path"]` |
| `rajatdave_ball.pt` | `meta["ball_model_path"]` |
| `yaku_ball.pt` | `meta["ball_model_path"]` |
| `tvcalib_calib_train59.pt` | `meta["calib_checkpoint"]` |

**This folder is NOT the runtime source of truth.** The code still reads weights
from its original locations — `voetlab/models/` (detection) and
`voetlab/external/tvcalib/data/segment_localization/train_59.pt` (calibration),
all resolved via the `meta` path keys / `voetlab/paths.py`. `models/` is a
**duplicate copy** assembled purely so the weights can be FTP'd up as one bundle.

## What was done about it

- `/models/*.pt` added to `.gitignore` — the binaries are deploy assets, kept out
  of git (same reasoning as [[rules/gitignore-large-checkpoints-document-the-download-instead]]).
- `models/README.md` is **tracked** and documents the manifest, the runtime `meta`
  keys, and how to re-populate the folder — so the tree still tells you what's
  supposed to be there even though the `.pt` files aren't version-controlled.
- Upload: `mput models/*.pt` to FTP. Consume at deploy: point the `meta` keys (or
  `voetlab/paths.py`) at the downloaded location.

## Why this matters

- **"Why are the weights in two places?"** — `voetlab/models/` (+ tvcalib external)
  is what the runtime reads; `models/` is the FTP upload bundle. The duplication is
  deliberate, not stale duplication to delete.
- **"Why is `models/` gitignored but its README tracked?"** — same size logic as
  [[learnings/tvcalib-calibration-checkpoint-is-gitignored-not-in-history]]: a
  467 MB `.pt` can't live in git history; the README stays so the manifest is
  reproducible.

## Open question (deferred)

Whether `models/` should become the **single source of truth** the code reads from
(deprecating `voetlab/models/`, rewiring `paths.py` + `MANIFEST.in`) was raised as
an open question and **not decided**. Until then, treat the duplication as
intentional. See [[learnings/canonical-repo-location-and-gitignore-policy]] for the
broader gitignore policy.
