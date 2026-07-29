---
type: System Overview
title: Overview
description: What this project contains and its structure.
timestamp: "2026-07-29T17:16:52.594Z"
---

# Overview

**voetlab** is a standalone, copyable football video-analytics framework written in Python
(3.10+). Broadcast video goes in; player and ball detection, multi-object tracking, pitch
calibration, event detection, physical and tactical stats, a per-stat reliability signal, and
charts come out. It is the engine behind **voetlab.nl** — a product that turns
broadcast footage into trustworthy match analytics. voetlab is a separate, self-contained
package you can either
`pip install -e .` or copy folder-for-folder into another project (no repo-specific imports).

The project is organized around three invariants, enforced everywhere: **one distinct feature
per file**, grouped into a **folder per domain** (`core`, `detection`, `tracking`,
`calibration`, `events`, `stats`, `tactics`, `reliability`, `viz`, `pipeline`); **every feature
returns a `core.result.Result`** success-indicator so `bool(result)` reads success and a failing
stage is *flagged, never crashed*; and **every event carries frame provenance** via
`core.provenance`, so any pass/tackle/interception traces back to the exact footage frame. Each
feature file also has a co-located **footage-driven test** that runs on the canonical clip
`football-1.mp4` and dumps inspectable artifacts under `tests/out/<feature>/`.

Execution is a **dependency-ordered pipeline runner** (`voetlab/pipeline/`). Features register
with `@feature(name, deps=[...])`; the runner topologically orders them, threads a shared
`PipelineState` clipboard, collects each `Result`, and isolates failures so the whole run still
completes. `voetlab.run(video)` runs the default graph end-to-end; `voetlab.run_feature(name,
video)` isolates a single stage; `compare(baseline, current)` diffs metric snapshots for
before/after analysis. The top-level API is the thin re-export in `voetlab/__init__.py`.

The repository root mixes four concerns: the **`voetlab/` package** itself (41 source modules +
their tests), **`docs/`** (a from-scratch build guide, a development log, a raw session
transcript, a generated self-contained HTML site, and this OKF knowledge wiki), **`tests/`**
(repo-level smoke tests plus sample output artifacts), and **project metadata** (`pyproject.toml`,
the editable-install `voetlab.egg-info/`, `FEATURES.md` auto-manifest, `llms.txt` LLM brief,
and `README.md`). High-recall ball detection (SAHI + a specialist model, ~98% vs ~1% for COCO)
and accurate metric calibration (the TVCalib full camera solver → real metres) are opt-in via
`meta` knobs; without them the pipeline degrades gracefully (pixels instead of metres, standard
YOLO ball). The full suite is `python -m pytest voetlab -q` → 121 tests.
