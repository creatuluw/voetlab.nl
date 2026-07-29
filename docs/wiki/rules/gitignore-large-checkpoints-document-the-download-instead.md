---
type: Rule
title: Gitignore large checkpoints, document the download instead
description: Guideline
tags: [git, gitignore, devops, models]
timestamp: "2026-07-29T20:40:54.897Z"
---

# Gitignore large checkpoints, document the download instead

## Guideline

Never `git add` model checkpoints or binary weights that are large (roughly
tens of MB or more), and **never** anything over **GitHub's 100 MB hard file
limit** — a single oversized file makes the whole `git push` fail. Instead:

1. Add the asset's directory to `.gitignore`, with a comment naming what it is
   and pointing to the download step.
2. Document the download command in `docs/BUILD_FROM_SCRATCH.md` (the relevant
   Phase), so the tree stays reproducible without the binary in history.

## When it applies

Whenever you're about to stage vendored models, calibration checkpoints, or any
third-party binary asset — e.g. the TVCalib `train_59.pt`, YOLO `.pt` weights.
This is a *different* `.gitignore` category from the regenerable
build/test-artifact ignores (see
[[learnings/canonical-repo-location-and-gitignore-policy]]): these files are
**not** reproducible from the tree, they are excluded purely on **size**.

## Rationale

Committing a 467 MB `.pt` into git history would (a) fail the push outright at
GitHub's 100 MB ceiling, and (b) bloat the repo permanently even if it
succeeded. A `.gitignore` line + a download pointer in the build guide is the
smallest working solution: the asset lives on disk, the code still references
it, but it is not version-controlled.

## Upgrade path

If a checkpoint genuinely needs to be under version control (reproducible CI,
no manual download), the proper path is **Git LFS** (GitHub: 1 GB free):

```bash
git lfs install
git lfs track "*.pt"
git add .gitattributes
git add <the-checkpoint.pt>
```

Only adopt LFS when the manual-download workflow actually hurts — until then,
gitignore + download doc wins on simplicity.
