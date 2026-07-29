---
type: System Overview
title: Overview
description: What this project contains and its structure.
timestamp: "2026-07-29T20:21:57.442Z"
---

# Overview

**voetlab** is a standalone, copyable football video-analytics framework written in Python
(3.10+). It turns broadcast football video into structured analytics: player and ball
detection, multi-object tracking, pitch calibration, on-ball events, physical and tactical
statistics, a per-stat reliability signal, and charts. It is the engine behind
**voetlab.nl** and is shipped as a self-contained package — `pip install -e .` or simply copy
the inner `voetlab/` folder into any project and `import voetlab`. The top-level `README.md`
and `llms.txt` are the human- and machine-facing entry points; `pyproject.toml` declares the
minimal core dependencies (numpy, opencv-python, scipy, scikit-learn, filterpy) with optional
`[vision]` (ultralytics + supervision), `[viz]` (matplotlib + mplsoccer), and `[dev]`
(pytest) extras.

The code lives entirely under `voetlab/`, organized as **one distinct feature per file, one
folder per domain**. The domains form a pipeline: `core/` (shared contracts — the `Result`
success indicator, frame provenance, footage test harness) → `detection/` (YOLO person+ball
detection, plus a high-recall SAHI ball detector) → `tracking/` (player/ball trackers, Kalman
ball trajectory, team classifier, role filter, tracker factory) → `calibration/` (homography
engine, keypoints, DLT-from-lines, and the accurate TVCalib full camera solver that yields
real metres) → `events/` (possession, passes, tackles, interceptions) → `stats/` (physical
and aggregate stats) → `tactics/` (Spearman pitch control, Voronoi territory) →
`reliability/` (per-stat confidence) → `viz/` (mplsoccer charts). The `pipeline/` package
wires these into a dependency-ordered, isolated runner with graceful failure, and `report.py`
provides a one-command JSON+charts report generator.

The project is built test-first: 121 tests, with **every feature file carrying a co-located
footage-driven test** that runs on a canonical `football-1.mp4` clip and dumps inspectable
artifacts to `tests/out/`. Two key conventions run through the whole codebase: every feature
returns a `core.result.Result` (so `bool(result)` reads success and a failing feature is
flagged, never crashes the run), and every event carries frame provenance (`source_frames`).
High-recall ball detection (SAHI + a specialist model, ~98% vs ~1–18% for stock COCO) and
accurate metric calibration (TVCalib full solver) are opt-in via `meta` keys; without them the
pipeline degrades gracefully to pixels and standard YOLO detection.

Documentation is extensive and tracked under `docs/`: `README.md` / `FEATURES.md` (install +
auto-generated feature manifest), `DEVELOPMENT_LOG.md` (how it was built — phases, measured
quality wins, bugfixes), `BUILD_FROM_SCRATCH.md` (ordered TDD-locked todos to reproduce the
framework exactly), `site/index.html` (a self-contained reference HTML site), and the
`docs/wiki/` OKF knowledge bundle holding decisions, rules, learnings, preferences, glossary,
and an annotated architecture file tree. Build/test artifacts (`__pycache__/`,
`.pytest_cache/`, `tests/out/`, `*.egg-info/`) and the pi harness state (`.pi/`) are
git-ignored as regenerable or machine-local.

## Major subsystems

- **core** — `Result` success indicator, frame provenance, footage test harness.
- **detection** — YOLO detection + the validated high-recall `detect_ball` (SAHI).
- **tracking** — player/ball trackers, Kalman trajectory, team classifier, role filter, tracker factory.
- **calibration** — homography engine, keypoints, TVCalib solver → metres.
- **events** — possession/passes/tackles, every event frame-provenanced.
- **stats** — physical + aggregate stats (pixels + metres when calibrated).
- **tactics** — pitch control + Voronoi (activate when calibrated).
- **reliability** — per-stat confidence (the voetlab signal).
- **viz** — mplsoccer chart adapters.
- **pipeline** — registry, runner (isolation + downstream + compare), default graph, CLI.
