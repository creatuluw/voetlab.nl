---
type: Learning
title: TVCalib calibration checkpoint is gitignored, not in history
description: The fact
tags: [git, gitignore, calibration, tvcalib, devops]
timestamp: "2026-07-29T20:40:54.898Z"
---

# TVCalib calibration checkpoint is gitignored, not in history

## The fact

`voetlab/external/tvcalib/data/segment_localization/train_59.pt` is a
**~467 MB** calibration checkpoint. It **exceeds GitHub's 100 MB hard file
limit**, so it can never be committed with a plain `git add` — a push
containing it fails outright.

## What was done about it

The entire `voetlab/external/tvcalib/data/` directory was added to
`.gitignore` (with a comment pointing to `docs/BUILD_FROM_SCRATCH.md` Phase 14,
where the checkpoint is downloaded). The checkpoint still lives on disk and the
code still references it via `meta["calib_checkpoint"]` — it is just not
version-controlled.

## Why this matters

- **"Why isn't `train_59.pt` in the repo?"** — because it's 467 MB and would
  fail the push. Get it via BUILD_FROM_SCRATCH.md Phase 14.
- **"Why did a `commit and push all` skip `external/`?"** — same reason. The
  lazy `git add -A` had to exclude this one dir.
- The upgrade path to bring it under version control is **Git LFS**
  (`git lfs track "*.pt"`), deferred until reproducible CI needs it.

See [[rules/gitignore-large-checkpoints-document-download-instead]] for the
general convention.
