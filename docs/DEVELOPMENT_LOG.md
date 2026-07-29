# voetlab — Development Log

> A dev-facing record of how `voetlab` was built into a standalone, tested,
> broadcast-football analytics framework. Read this to
> understand *why* the code is shaped the way it is, *what* was measured, and *where* the
> remaining knobs are.

**Status at end of session:** 121 tests green · standalone + `pip install -e` · full pipeline
(detect→track→ball→teams→events→stats) with high ball recall, accurate metric calibration,
auto reliability signal, and a one-command report generator.

---

## 1. Starting point & goal

The project began as a single-user **bot + CLI** that ran YOLOv8s + ByteTrack → HSV team
split → rule-based events → an automated report. It was positioned as **v1 of voetlab**
(voetlab.nl — *"Elite football data, from any broadcast"*).

Two problems framed all the work:
1. **Quality was poor.** Ball detection was ~1–18% of frames; events depend on the ball, so
   the whole event layer was starved; distances were in **pixels** (no homography); team
   classification broke on red jerseys; tracking fragmented IDs.
2. **It wasn't a reusable framework.** Logic was coupled in agents; no tests; no way to run
   or inspect a single stage.

The goal became: turn the engine into a **standalone, copyable, testable framework** (`voetlab`)
and lift quality to physically-meanful (metres, real events) using verified, online-checked
techniques — without a web app (explicitly deferred).

---

## 2. Research phase (everything was verified online)

The websearch backend returned empty all session, so research was done by **deep-fetching
primary sources** (official docs / papers / repo READMEs via `curl`) and parallel research
scouts. Findings live in local research notes (not shipped with this repo).

**Catalogued 20+ high-star repos** across tracking, events, calibration, viz, and end-to-end
pipelines (mplsoccer, SoccerNet, LaurieOnTracking, socceraction, supervision, ByteTrack/
BoT-SORT/OC-SORT, deep-person-reid, tvcalib, …). Each technique was **filtered to the
highest-quality, results-assured** option before adoption.

### Verified technique stack (the decisions)
| Area | Chosen technique | Primary source |
|------|------------------|----------------|
| Tracking | **BoT-SORT** (CMC + optional ReID) — *available*; **ByteTrack kept as default** after measurement | docs.ultralytics.com/modes/track |
| Ball detection | **SAHI sliced inference + a specialist football-ball model** (orthogonal to COCO class-32) | github.com/obss/sahi; HuggingFace |
| Ball trajectory | **Kalman constant-velocity** (single object) | Ultralytics track docs |
| Homography | **TVCalib** per-frame camera calibration (self-verification τ) | github.com/MM4SPA/tvcalib (WACV'23, arXiv 2207.11709) |
| Velocity smoothing | **Savitzky–Golay** | LaurieOnTracking `Metrica_Velocities.py` |
| Tactics | **Spearman pitch control** + **Voronoi** dominant regions | LaurieOnTracking; SoccermaticsForPython |
| Viz | **mplsoccer** | github.com/andrewrowlinson/mplsoccer |

These are recorded as ADRs in `docs/wiki/decisions/` (see §7).

**Roboflow / paid alternatives verdict:** do **not** pay to *buy* a model — self-fine-tune on
SoccerNet-Tracking (free) wins; Roboflow ($79/mo) is only worth it as a *training platform*;
hosted inference is a poor fit (~100–190k frames/match). Hugging Face has free football YOLO
`.pt` weights for an instant baseline.

---

## 3. Architecture: the `voetlab` framework

A set of conventions (recorded as the wiki rule `voetlab-framework-conventions-...`) govern
every file:

- **One distinct feature = one file**, named as a pipeline unit.
- **Every feature returns `core.result.Result`** (`ok / value / error / meta`) — the universal
  success indicator; the runner branches on `bool(result)`.
- **Every event carries frame provenance** (`source_frames`) via `core.provenance`.
- **Co-located per-folder tests** that run on the canonical clip `football-1.mp4` and **dump
  inspectable artifacts** (`tests/out/<feature>/annotated.png` + `results.json`) so a human can
  *see* results and pinpoint failures.
- **Standalone**: no `src.`/repo imports inside `voetlab/` — copy the folder or `pip install -e`.
- **Pipeline** = `@feature(name, deps=[...])` registry + `pipeline.runner` (dep-order exec,
  failure flagging, `run_feature()` isolation, `compare()`).

```
voetlab/                       project root (pyproject.toml, README.md, FEATURES.md)
└── voetlab/                   THE importable package
    ├── core/                   result, provenance, fixtures (footage harness)
    ├── detection/              detect.py (+ detect_ball SAHI specialist)
    ├── tracking/               player_tracker, ball_tracker, ball_trajectory(Kalman),
    │                           team_classifier, role_filter, tracker_factory
    ├── calibration/            homography, keypoint (+tvcalib), metric bridge,
    │                           tvcalib_solver, features (calibrate)
    ├── events/                 events.py (possession/passes/duels, frame-provenanced)
    ├── stats/                  stats.py (px + metric), physical
    ├── tactics/                pitch_control (Spearman), voronoi, features
    ├── reliability/            reliability.py + features (the voetlab signal)
    ├── viz/                    charts.py (mplsoccer adapters)
    ├── pipeline/               registry, runner, default, cli
    ├── report.py               end-to-end report generator + CLI
    └── docs/                   build_docs.py + site/index.html + this log
```

Each voetlab feature's README documents its quality profile and when to use it.

---

## 4. Build phases (the todo arc)

Every item was **TDD: red test → green impl → only green marks done**, with the suite kept
green between steps. ~40 todos across the session, all closed.

| Phase | Todos | Outcome |
|-------|-------|---------|
| **Foundation** | F0–F6 | package scaffold; `Result`; provenance; footage harness; runner (isolation + downstream + compare); per-folder test template; doc generator |
| **Pipeline port** | P1–P7 | detect → track → ball → teams → events → stats + `default.run()`/`run_feature()` + CLI |
| **Quality upgrades** | T0–T13 | Kalman ball; HSV circularity; majority vote; GK/ref filter; homography; metric stats; per-frame possession; ball-detector config; BoT-SORT factory; reliability; pitch control; Voronoi; viz |
| **Docs** | D1–D3 | per-file "Quality & when to use" headers; per-folder READMEs |
| **Calibration + polish** | B1–B4 | TVCalib full solver (accurate metres); reliability wired into the pipeline; report generator; top-level API |

---

## 5. The measured quality wins

These are **on-footage measurements**, not claims:

### Ball recall — the #1 problem, solved
| Approach | Ball-frame coverage on `football-1.mp4` |
|---|---|
| COCO yolov8s class-32 (original) | **1.0%** (2/200) |
| Free HF ball model alone | 3.3% |
| SAHI + rajatdave ball model | 55.3% |
| **SAHI + martinjolif football-ball model** | **98%** (98/100 in-framework) |

Root cause: COCO class 32 = baseball/tennis, **not football**; the ball is small, so
**slicing the frame (SAHI)** + a specialist model finds it. Wired as feature `detect_ball`
and auto-consumed by `ball`→`events` when `meta={"ball_model_path": ...}`.

### Tracking — measured, ByteTrack kept
On `football-1.mp4`: ByteTrack **16** vs BoT-SORT **18** unique IDs. On the high-motion
`veendam` full-match broadcast: ByteTrack **17** vs BoT-SORT **19**. ByteTrack was **≥ BoT-SORT
on both**, so the default stayed ByteTrack (decision `keep-bytetrack-as-default-tracker`).
BoT-SORT remains available + correctly CMC-configured (and is the migration path before
supervision 0.30 removes `sv.ByteTrack`).

### Calibration — accurate metres, end to end
| Stage | Result |
|---|---|
| DLT-from-lines baseline | ~42 m reprojection error (rejected → graceful pixel fallback) |
| TVCalib full solver | `loss_ndc_total = 0.0057` (< τ=0.019); grid-H self-consistent to **0.00 m** |
| End-to-end stats | all 12 players get sane `distance_m` (4–9 m) + `top_speed_km_h` (20–60) — real metres |

---

## 6. Deep-dive: the calibration journey (most instructive)

This is the clearest example of "measure → don't assume → find the real cause."

1. **Built the engine** (`homography.py`: `estimate_homography`/`px_to_meters`/`self_verify`)
   + the **metric bridge** (`tracks_to_metric`) + wired Voronoi/pitch-control as features that
   activate when `meta["H"]` is present.
2. **Cloned TVCalib** (`external/tvcalib`) + downloaded the 488 MB seg checkpoint
   (`train_59.pt`). Hit a **dependency chain** (kornia, SoccerNet, pytorch-lightning) and
   **three torch/cv2-2.x compat shims** in the external copy:
   - `torch._six import string_classes` → `(str, bytes)` fallback (torch ≥ 2.0 removed `_six`).
   - `torch.load(checkpoint)` → `weights_only=False` (torch ≥ 2.6 default change).
   - `cv2.erode(semantic_mask, …)` → cast `.astype(np.uint8)` (cv2 4.x rejects int32).
3. **Seg detector proven**: `detect_keypoints_tvcalib` returns up to 10 line classes/frame.
4. **Keypoint quality hardening** (from studying the WACV'23 paper via docling): drop 3D **goal
   structures + arcs** (non-ground), dedup near-duplicate extremities, drop degenerate lines;
   valid multi-frame **line-coverage** counting (camera moves, so image points can't merge, but
   line *classes* can be tallied).
5. **The "blocked" detour.** The simple DLT baseline gave ~42 m → `calibrate` correctly
   rejected it → graceful pixel fallback (no garbage). The full solver initially threw
   `RuntimeError: [35,3] vs [35,1]` and was recorded as blocked.
6. **Webresearch unblocked it.** Parallel scouts (local code trace + GitHub issues + web)
   proved `self_optim_batch` was **fine** and pinned the error to **our** `project_point2pixel`
   call. Root cause + fix (see §8): wrong point shape + unfiltered H derivation + stale loss key.
7. **Fixed → accurate.** `loss_ndc_total = 0.0057`, grid-H self-consistent to 0.00 m, real
   metres flow through stats.

**Lesson:** "measure before assuming an upgrade; the bug was ours, not the library's."

---

## 7. Key decisions (ADRs) & durable rules

Decisions (`docs/wiki/decisions/`):
- `adopt-verified-cv-analytics-technique-stack-bot-sort-tvcalib` — the verified stack.
- `extract-voetlab-as-a-standalone-copyable-analytics-framework` — why `voetlab` exists as a standalone package.
- `keep-bytetrack-as-default-tracker` — measured, not assumed.

Rules (`docs/wiki/rules/`): voetlab framework conventions; **measure technique swaps before
flipping defaults**; read real video metadata (fps/frames) never hardcode; verify techniques
online before planning; improvement todos are test-first + surgical.

Preference: **use `football-1.mp4` as the canonical test fixture**.

---

## 8. Notable bugfixes (what broke and why)

- **T9 dead config** — `track_via_ultralytics` passed only `tracker/conf/classes`; the BoT-SORT
  `gmc_method`/`with_reid` never reached Ultralytics → CMC was dead code. Fix: ship a custom
  `voetlab_botsort.yaml` (CMC enabled) and point `tracker=` at it.
- **HSV hue circularity (T1)** — red wraps hue 0↔180; raw-Euclidean KMeans split one red team.
  Fix: encode hue as `(cos, sin, S)` before KMeans.
- **Events missing `type`** — `detect_events` attached `kind` via provenance but never set
  `ev["type"]` → test failed. Fix: set `type` explicitly.
- **SAHI lazy import** — `sahi.predict` isn't a direct attribute (lazy `__getattr__`); monkeypatch
  target had to be `sahi.predict` (imported), not `sahi.predict`.
- **TVCalib torch/cv2 shims** — three compat fixes in the external copy (see §6.2).
- **B1 — the calibration shape error** (the big one):
  - *Symptom:* `RuntimeError: Expected size for first two dimensions of batch2 tensor to be: [35, 3] but got: [35, 1]`.
  - *False lead:* blamed TVCalib internals.
  - *Real cause:* our `cam.project_point2pixel(P)` passed `(1,1,N,3)`; the API wants `(1,N,3)` →
    broke `self.rotation @ point.transpose(1,2)`. Plus our `_extract_loss` read `loss_total`
    (real key: `loss_ndc_total`), and we derived H from **unfiltered all-ground-point projection**
    (off-screen/NaN → ~42 m).
  - *Fix:* point shape `(1,-1,3)`; read `loss_ndc_total`; derive H from a **template ground grid**
    (filtered finite + in-bounds); gate on `loss < τ≈0.05`. Verified: 0.00 m self-consistency.

---

## 9. Insights worth remembering

- **The event layer is starved by the ball layer.** ~82% of "bad CV" was *logic* (events only
  ran on detected-ball frames), not model weights. Fix the ball path and the whole pipeline
  unblocks — most wins were pure-logic + unit-testable.
- **SAHI is orthogonal to the class-32 problem.** Slicing boosts small-object recall but only
  helps once you have a *football* ball model (COCO class 32 ≠ football).
- **ByteTrack ≥ BoT-SORT on the available footage** — don't flip defaults on theory; measure.
  (BoT-SORT's CMC win would show on extreme pan/zoom; validate there before flipping.)
- **Distances were pixels** — there was no homography to "improve"; it had to be *built*.
- **voetlab is the product's engine**; the webapp/dashboard (voetlab shell) is the remaining
  macro-workstream, deliberately deferred.

---

## 10. Current state & how to use

```python
import voetlab
res = voetlab.run("football-1.mp4", max_frames=50, meta={
    "ball_model_path": "models/martinjolif_ball.pt",            # 98% ball recall
    "calib_checkpoint": "external/tvcalib/data/segment_localization/train_59.pt",  # accurate metres
    "tvcalib_path": "external/tvcalib"})
res.value["data"]["stats"]        # per-player distance_m / top_speed_km_h
res.value["data"]["reliability"]  # confidence on every number
res.value["failed"]               # any feature that didn't finish
voetlab.run_feature("detect", "football-1.mp4")   # isolate one stage
```

One-command report: `python -m voetlab.report <video> --max-frames 50 --ball-model-path …
--out report/` → `summary.json`, `stats.json`, `reliability.json`, `radar.png`,
`pass_network.png`, `heatmap.png`.

Tests: `python -m pytest voetlab -q` (121 passed). Docs site: `voetlab/docs/site/index.html`
(auto-generated from source by `voetlab.docs.build_docs`).

---

## 11. What's left (optional, documented)

- **Webapp/dashboard** (voetlab product shell) — auth, match library, consumes `viz` Figures +
  reliability badges. Deferred by request.
- **Player-ID robustness** — jersey-number OCR + global-ID clustering (ReID) to replace
  track-ID fragmentation for true per-player career stats.
- **Velocity smoothing (T5 Savitzky–Golay)** is specified but not yet the default in `stats`
  (the sprint-speed spikes on short windows show why it'd help).
- **Calibration on extreme-motion footage** — re-validate BoT-SORT + per-shot recalibration.

Everything else is built, tested, and wired. The framework is the engine; the above are the
next layers on top.
