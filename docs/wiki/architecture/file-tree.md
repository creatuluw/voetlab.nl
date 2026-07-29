---
type: Artifact
title: File tree
description: Annotated project file tree with per-entry function summaries.
timestamp: "2026-07-29T20:21:57.442Z"
---

# File tree — generated 2026-07-29T17:47:57.540Z
# Respects .wiki_ignore exclusions.
# [description] — shorthand summary of each file's function

.
├── .git/ — the Git repository metadata, refs, hooks, and content-addressed object store (config/HEAD/index/COMMIT_EDITMSG; refs/heads/main + remotes/origin/main; sample hooks; logs/reflog). The hundreds of .git/objects/<xx>/<hash> entries are loose Git objects (blobs/trees/commits keyed by SHA-1) plus pack/ and info/ — content-addressed history that changes every commit, so not annotated individually.
├── .pi/ — pi coding-agent session/config state for this project (git-ignored, machine-local).
├── .pytest_cache/ — pytest's run cache (git-ignored, regenerable).
├── docs/ — project documentation: build guide, dev log, generated HTML site, and the OKF wiki.
│   ├── site/ — the generated, self-contained HTML reference site.
│   │   └── index.html — single-page voetlab docs site (sidebar nav, search, collapsible per-feature cards, dark mode) emitted by voetlab/docs/build_docs.py.
│   ├── wiki/ — the OKF knowledge wiki bundle (this tree).
│   │   ├── architecture/ — architecture artifacts.
│   │   │   └── file-tree.md — the full annotated project file tree with per-entry [description] placeholders (this document).
│   │   ├── changelog/ — month-bucketed wiki changelog append-logs.
│   │   │   └── 2026-07.jsonl — JSONL changelog entries recording wiki edits made in 2026-07.
│   │   ├── decisions/ — Architecture Decision Records (major decisions/direction shifts).
│   │   │   └── index.md — index listing all decision concepts (currently empty/seed).
│   │   ├── learnings/ — captured non-obvious facts and gotchas.
│   │   │   ├── canonical-repo-location-and-gitignore-policy.md — records the GitHub origin and what .gitignore treats as regenerable.
│   │   │   ├── index.md — index of all learnings.
│   │   │   └── reliability-signal-has-a-hardcoded-component.md — notes that homography_conf is hardcoded to 1.0 and tracking_stability is a proxy.
│   │   ├── pages/ — Concept / Entity / Artifact pages for the project.
│   │   │   ├── TEMPLATES.md — reference templates for writing Concept, Entity, and Artifact pages.
│   │   │   ├── artifacts/ — Artifact-type pages (deliverables: diagrams, reports, specs).
│   │   │   │   └── index.md — index of artifact pages.
│   │   │   ├── concepts/ — Concept-type pages (abstract ideas, definitions, patterns).
│   │   │   │   └── index.md — index of concept pages.
│   │   │   ├── entities/ — Entity-type pages (concrete named things: endpoints, services, modules).
│   │   │   │   └── index.md — index of entity pages.
│   │   │   └── index.md — top-level index of all pages.
│   │   ├── preferences/ — captured coding-style/tool conventions.
│   │   │   └── index.md — index of preferences.
│   │   ├── rules/ — reusable heuristics, guidelines, conventions.
│   │   │   ├── index.md — index of rules.
│   │   │   └── remove-all-references-when-deleting-a-wiki-concept.md — rule: strip all slug references when deleting a wiki concept.
│   │   ├── glossary.md — project glossary (term → definition table).
│   │   ├── index.md — wiki home: navigation map of every concept + section links.
│   │   ├── last_updated.md — timestamp marker showing when the wiki was last synced to the code.
│   │   ├── log.md — wiki activity log.
│   │   ├── overview.md — project overview (system-structure summary).
│   │   ├── wiki-viewer.html — standalone HTML viewer for browsing the wiki.
│   │   └── wiki.js — JavaScript powering the wiki viewer.
│   ├── BUILD_FROM_SCRATCH.md — ordered, TDD-locked todos to reproduce the exact voetlab framework (target: 121 tests green).
│   └── DEVELOPMENT_LOG.md — dev-facing record of how the framework was built: phases, measured quality wins, decisions, and bugfixes.
├── tests/ — top-level integration/acceptance tests (distinct from the per-domain feature tests).
│   ├── __pycache__/ — compiled bytecode cache for tests/ (git-ignored).
│   ├── out/ — inspectable artifacts dumped by footage-driven tests (git-ignored, regenerated each run).
│   │   ├── detect/ — artifacts from the top-level detection smoke test.
│   │   │   ├── annotated.png — an annotated sample frame showing detected boxes.
│   │   │   └── results.json — detection results JSON for the smoke test.
│   │   └── pipeline/ — artifacts from the top-level pipeline smoke test.
│   │       └── results.json — pipeline run results JSON.
│   ├── __init__.py — marks tests/ as a Python package.
│   └── test_imports.py — smoke test asserting import voetlab and the public API (run, run_feature) are importable.
├── voetlab/ — the framework package itself; standalone, copyable, no repo-specific imports.
│   ├── __pycache__/ — compiled bytecode cache for the package root (git-ignored).
│   ├── calibration/ — broadcast-pixel → real-world-metres homography domain.
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located footage/unit tests for the calibration domain.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks the calibration tests as a package.
│   │   │   ├── test_calibrate.py — tests the calibrate feature wiring and its DLT fallback path.
│   │   │   ├── test_homography.py — pure-engine tests for the cv2 homography engine + self_verify.
│   │   │   ├── test_homography_from_keypoints.py — tests estimating H from keypoint point pairs.
│   │   │   ├── test_homography_lines.py — DLT-from-line-correspondences tests.
│   │   │   ├── test_keypoint.py — tests keypoint pairing/filtering/coverage helpers.
│   │   │   └── test_keypoint_quality.py — tests keypoint-set quality gating.
│   │   ├── __init__.py — marks calibration/ as a package.
│   │   ├── features.py — the registered calibrate feature: samples frames, runs TVCalib (τ=0.05) with DLT fallback (reproj < 15 m), publishes H.
│   │   ├── homography_lines.py — pure-numpy DLT homography from line correspondences (SoccerNet baseline).
│   │   ├── homography.py — pure cv2 homography engine: estimate_homography (RANSAC), warp_points, px_to_meters, self_verify; IFAB PITCH_M = (105, 68).
│   │   ├── keypoint.py — pitch-landmark keypoints → homography point pairs; named IFAB template points, ops integration, coverage/quality helpers.
│   │   ├── metric.py — the bridge: warps each player's feet through H per frame into metric-space coords.
│   │   ├── README.md — calibration domain docs (TVCalib solver + DLT fallback, quality, limitations).
│   │   └── tvcalib_solver.py — the accurate path: runs TVCalib's full camera solver (AdamW, ~2000 steps) to derive H and loss.
│   ├── core/ — shared, dependency-light foundation contracts (no CV logic).
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located tests for the core contracts.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks core tests as a package.
│   │   │   ├── test_fixtures.py — tests the footage test harness (skips gracefully if footage absent).
│   │   │   ├── test_provenance.py — tests that events are stamped with source_frames.
│   │   │   └── test_result.py — tests the Result success indicator (Ok/Fail/bool()).
│   │   ├── __init__.py — marks core/ as a package.
│   │   ├── fixtures.py — footage-driven test harness: load_sample_frames, footage_meta, dump_artifacts (default footage football-1.mp4).
│   │   ├── provenance.py — attach_provenance(event, source_frames, **refs); required for all event-producing features.
│   │   ├── README.md — core domain docs (Result, provenance, fixtures).
│   │   └── result.py — the universal Result dataclass (Ok/Fail/ok/value/error/meta); bool(result) reads success.
│   ├── detection/ — per-frame detection domain (pipeline entry point).
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located detection tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks detection tests as a package.
│   │   │   ├── test_detect_ball.py — tests the high-recall SAHI ball detector.
│   │   │   ├── test_detect.py — mocked-YOLO unit tests + real-footage smoke dumping tests/out/detect/annotated.png.
│   │   │   ├── test_sahi.py — tests SAHI sliced-inference behavior/config.
│   │   │   └── test_vision_config.py — tests vision/SAHI configuration plumbing.
│   │   ├── __init__.py — marks detection/ as a package.
│   │   ├── detect.py — detect feature: YOLO person+ball per frame; helpers boxes_from_result, annotate; also detect_ball_sahi (T8 high-recall ball path).
│   │   └── README.md — detection domain docs (YOLO detection + validated SAHI detect_ball).
│   ├── docs/ — the documentation generator package.
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located tests for the docs generator.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks docs tests as a package.
│   │   │   └── test_docs.py — tests that build_docs parses features and emits manifest + HTML.
│   │   ├── __init__.py — marks the docs generator as a package.
│   │   └── build_docs.py — F6 generator: scans feature .py files, emits FEATURES.md manifest and docs/site/index.html.
│   ├── events/ — on-ball event detection domain.
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located event tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks events tests as a package.
│   │   │   ├── test_events.py — synthetic scenarios asserting passes/tackles + non-empty provenance.
│   │   │   └── test_possession_every_frame.py — tests per-frame possession determination.
│   │   ├── __init__.py — marks events/ as a package.
│   │   ├── events.py — events feature: possession/passes/tackles/interceptions, each carrying source_frames.
│   │   └── README.md — events domain docs.
│   ├── pipeline/ — feature registry, runner, default graph, and CLI.
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located pipeline tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks pipeline tests as a package.
│   │   │   ├── test_default.py — tests default wiring + end-to-end smoke on football-1.mp4.
│   │   │   └── test_runner.py — tests registry, dependency-order runner, isolation, and compare.
│   │   ├── __init__.py — marks pipeline/ as a package.
│   │   ├── cli.py — CLI entry point: python -m voetlab.pipeline.cli <video> [--feature NAME] [--max-frames N].
│   │   ├── default.py — imports all features (so they register) + exposes run(video) / run_feature(); defines DEFAULT_FEATURES.
│   │   ├── README.md — pipeline domain docs (registry, runner, default graph, CLI).
│   │   ├── registry.py — @feature(name, deps) decorator + global registry; registered().
│   │   └── runner.py — PipelineState clipboard + run (dep-order, failure flagging) + run_feature (isolation) + compare (metric diff).
│   ├── reliability/ — per-stat confidence (the voetlab "reliability signal").
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located reliability tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks reliability tests as a package.
│   │   │   ├── test_reliability_feature.py — tests the registered reliability feature wrapper.
│   │   │   └── test_reliability.py — asserts honest ball coverage, interpolation ratio, fragmentation flagging, composite propagation.
│   │   ├── __init__.py — marks reliability/ as a package.
│   │   ├── features.py — the registered reliability feature (deps: ball, track); in DEFAULT_FEATURES.
│   │   ├── README.md — reliability domain docs (signal inputs, composites, limitations).
│   │   └── reliability.py — compute_reliability(...) producing ball coverage, interpolation ratio, tracking stability, homography conf, and composites.
│   ├── stats/ — physical and event-aggregate statistics (terminal stage).
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located stats tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks stats tests as a package.
│   │   │   ├── test_metric_stats.py — tests metric-space (metres/km·h) stats via homography.
│   │   │   └── test_stats.py — synthetic moving-track test for distance/speed + possession aggregation.
│   │   ├── __init__.py — marks stats/ as a package.
│   │   ├── README.md — stats domain docs.
│   │   └── stats.py — stats feature: per-player/per-team distance, top speed, sprints, pass/tackle/possession counts.
│   ├── tactics/ — pitch control and Voronoi territory (pure functions).
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located tactics tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks tactics tests as a package.
│   │   │   ├── test_metric_and_features.py — tests the tactics feature wrappers and metric conversion.
│   │   │   ├── test_pitch_control.py — synthetic-position tests for the Spearman pitch-control surface.
│   │   │   └── test_voronoi.py — tests dominant-region tessellation and team area ratio.
│   │   ├── __init__.py — marks tactics/ as a package.
│   │   ├── features.py — T11/T12 feature wrappers reading pixel tracks + H, converting to metric, computing tactics.
│   │   ├── pitch_control.py — T11 Spearman pitch-control: per-cell P(team A controls) from time-to-reach influence.
│   │   ├── README.md — tactics domain docs (pitch control + Voronoi; status, metric dependency).
│   │   └── voronoi.py — T12 Voronoi/dominant-region tessellation via cKDTree rasterization.
│   ├── tests/ — cross-domain package-level tests (e.g. the report generator).
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   └── test_report.py — tests the end-to-end report generator (voetlab.report).
│   ├── tracking/ — player/ball tracking, team classification, roles.
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located tracking tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks tracking tests as a package.
│   │   │   ├── test_ball_prefers_detect_ball.py — tests that the ball path prefers SAHI detect_ball output when available.
│   │   │   ├── test_ball_tracker.py — tests linear ball interpolation behavior.
│   │   │   ├── test_ball_trajectory.py — tests the Kalman constant-velocity ball trajectory (T6).
│   │   │   ├── test_player_tracker.py — tests ByteTrack player tracking over detection boxes.
│   │   │   ├── test_role_filter.py — tests referee/goalkeeper role heuristics (T3).
│   │   │   ├── test_team_circular.py — tests circular-hue team classification (T1).
│   │   │   ├── test_team_classifier.py — tests KMeans k=2 HSV torso team classification.
│   │   │   ├── test_team_stabilizer.py — tests per-track majority-vote team stabilization (T2).
│   │   │   └── test_tracker_factory.py — tests the ByteTrack/BoT-SORT tracker factory (T9).
│   │   ├── __init__.py — marks tracking/ as a package.
│   │   ├── ball_tracker.py — ball feature: linear ball interpolation; synthetic points marked confidence=0.0.
│   │   ├── ball_trajectory.py — T6 constant-velocity Kalman ball trajectory (pure numpy); ball_method="kalman".
│   │   ├── player_tracker.py — track feature: ByteTrack player tracking over person boxes.
│   │   ├── README.md — tracking domain docs (player/ball trackers, Kalman, teams, roles, factory).
│   │   ├── role_filter.py — T3 roles feature: pure bbox-centroid heuristics → player/gk/referee.
│   │   ├── team_classifier.py — teams feature: KMeans k=2 on median HSV torso color (T1 circular hue, T2 majority vote).
│   │   ├── tracker_factory.py — T9 tracker factory: ByteTrack (supervision) or BoT-SORT/OC-SORT (ultralytics model.track).
│   │   └── voetlab_botsort.yaml — BoT-SORT config used by the ultralytics tracker path.
│   ├── viz/ — mplsoccer chart adapters (dashboard chart engine).
│   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   ├── tests/ — co-located viz tests.
│   │   │   ├── __pycache__/ — compiled bytecode cache (git-ignored).
│   │   │   ├── __init__.py — marks viz tests as a package.
│   │   │   └── test_charts.py — each adapter returns a matplotlib.figure.Figure (headless).
│   │   ├── __init__.py — marks viz/ as a package.
│   │   ├── charts.py — T13 mplsoccer adapters: heatmap, pass_network, radar → matplotlib Figures.
│   │   └── README.md — viz domain docs (adapters, headless rendering, limitations).
│   ├── __init__.py — package root; exposes __version__ and top-level run / run_feature convenience API.
│   └── report.py — end-to-end report generator + CLI: runs the pipeline → summary.json, stats.json, reliability.json, and best-effort chart PNGs.
├── .gitignore — ignores regenerable build/test artifacts (__pycache__/, .pytest_cache/, tests/out/, *.egg-info/) and machine-local state (.pi/).
├── .wiki_ignore — paths excluded from wiki staleness detection / file-tree generation (node_modules, dist, build, caches, .pi/, etc.).
├── FEATURES.md — auto-generated feature manifest: one row per feature file (folder/file/summary).
├── llms.txt — machine-facing summary for LLMs: overview, entry points, and doc links.
├── pyproject.toml — PEP 621 project metadata: name, version, deps, optional [vision]/[viz]/[dev] extras, setuptools build config.
└── README.md — human-facing entry point: quickstart, install, layout, and framework conventions.
