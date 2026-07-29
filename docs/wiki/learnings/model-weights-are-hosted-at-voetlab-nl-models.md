---
type: Learning
title: Model weights are hosted at voetlab.nl/models
description: voetlab's model weights are **large binaries that are not committed to git** — the
tags: [models, weights, deployment, download, devops, voetlab.nl]
timestamp: "2026-07-29T21:28:24.516Z"
---

# Model weights are hosted at voetlab.nl/models

voetlab's model weights are **large binaries that are not committed to git** — the
calibration checkpoint alone is ~488 MB (over GitHub's 100 MB file limit). They live in a
consolidated `models/` folder at the repo root (git-ignored: `.gitignore` → `/models/*.pt`;
only `models/README.md` is tracked) and are mirrored on the project's static host for
download.

## Canonical download host — VERIFIED WORKING

**https://voetlab.nl/models/** — confirmed serving every weight (HTTP 200, correct sizes):

| File | Size | Runtime key | Purpose |
|------|------|-------------|---------|
| `yolov8s.pt` | ~21.5 MB | `meta["model_path"]` | Default YOLO detector (persons + ball) |
| `martinjolif_ball.pt` | ~5.3 MB | `meta["ball_model_path"]` | High-recall SAHI football-ball model (~98%) |
| `rajatdave_ball.pt` | ~6.1 MB | `meta["ball_model_path"]` | Alternate ball model |
| `yaku_ball.pt` | ~6.0 MB | `meta["ball_model_path"]` | Alternate ball model |
| `tvcalib_calib_train59.pt` | ~488 MB | `meta["calib_checkpoint"]` | TVCalib calibration checkpoint → metres |

```bash
for f in yolov8s.pt martinjolif_ball.pt tvcalib_calib_train59.pt; do
  curl -L -o "models/$f" "https://voetlab.nl/models/$f"
done
```

> ⚠️ When this was verified, the served `tvcalib_calib_train59.pt` was ~543 KB smaller than
> the local copy — possibly a truncated FTP upload. Re-upload if `torch.load` fails on it.

## Why voetlab.nl and NOT te9.dev

The weights were first tried on `te9.dev/voetlab/models/`, which **404s**: `te9.dev` is served
by a **SvelteKit/Node app** (apex → AWS Global Accelerator; `www.te9.dev` → `Server:
railway-hikari`, i.e. Railway.app). Neither is a static-file host, so files FTP'd to
`/public_html/te9.dev/...` on disk are not web-accessible — the app returns its own 404.

`voetlab.nl` (and `www.voetlab.nl`) DNS → `92.205.3.167`, an **Apache** shared-host box that
serves the `/models/` path directly (200 + correct `Content-Length`, range support). That is
why the canonical URL is `voetlab.nl/models/`.

## Why it matters

Anyone (dev or LLM) running the full pipeline must fetch weights from the host — they are
neither `pip install`ed nor pulled from git. Without `ball_model_path` the run degrades to
~1–18% ball recall; without `calib_checkpoint` it stays in pixels (no metres). Documented in
`README.md` (## Models & weights), `llms.txt` (## Model weights), and `models/README.md`.

## Runtime resolution

The package resolves its own default locations in `voetlab/paths.py`
(`voetlab/models/*`, `voetlab/external/tvcalib/data/.../train_59.pt`), but every weight is
**overridable via `meta` keys**, so a deployment that downloads from the host just points
those keys at the download location.
