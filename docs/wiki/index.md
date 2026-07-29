---
okf_version: "0.1"
---

# Project Knowledge Wiki

<!-- wiki-nav:start -->
## Navigation map

Auto-generated detailed index of every docs/wiki/ concept — the map the LLM uses to locate information. 14 concept(s). Regenerated on init and on wiki_mark_synced. Generated 2026-07-29T21:28:43.088Z.

Each entry: `concept-id` (pass to wiki_get) — title — description.

### Core concepts

- `glossary` — Glossary — Key terms for this project.
- `overview` — Overview — What this project contains and its structure.

### Architecture

- `architecture/file-tree` — File tree — Annotated project file tree with per-entry function summaries.

### Pages

- `pages/TEMPLATES` — Page Templates — Reference templates for Concept, Entity, and Artifact pages. Follow these when using wiki_note_page.

### Rules

- `rules/gitignore-large-checkpoints-document-the-download-instead` — Gitignore large checkpoints, document the download instead — Guideline
- `rules/keep-wiki-ignore-in-sync-with-noise-directories` — Keep .wiki_ignore in sync with noise directories — When (re)generating `docs/wiki/architecture/file-tree.md`, ensure regenerable / noise
- `rules/per-frame-pipeline-stages-emit-throttled-progress-via-state-` — Per-frame pipeline stages emit throttled progress via state.progress — Stages with a per-frame loop emit progress events through the optional `state.progress` callback (a `Callable[[dict], None]`, default `None`). The runner always
- `rules/remove-all-references-when-deleting-a-wiki-concept` — Remove all references when deleting a wiki concept — Guideline

### Learnings

- `learnings/canonical-repo-location-and-gitignore-policy` — Canonical repo location and gitignore policy — The `voetlab` framework (working dir `voetlab.nl/`) is now hosted at
- `learnings/detect-ball-slice-size-vs-ball-recall-on-1080p` — detect_ball slice_size vs ball recall on 1080p — The `detect_ball` (SAHI) stage's speed is dominated by the slice count, which is set by
- `learnings/model-weights-are-hosted-at-voetlab-nl-models` — Model weights are hosted at voetlab.nl/models — voetlab's model weights are **large binaries that are not committed to git** — the
- `learnings/models-folder-is-ftp-deploy-bundle` — Models folder is an FTP deploy bundle, not the runtime source — The fact
- `learnings/reliability-signal-has-a-hardcoded-component` — Reliability signal has a hardcoded component — The `reliability` domain publishes a per-stat trust signal, but not all of its
- `learnings/tvcalib-calibration-checkpoint-is-gitignored-not-in-history` — TVCalib calibration checkpoint is gitignored, not in history — The fact
<!-- wiki-nav:end -->

An [OKF](https://github.com/earendil-works/okf) bundle documenting this project.

- [Overview](./overview.md) — What this project contains and its structure
- [File tree](./architecture/file-tree.md) — Complete project file listing
- [Glossary](./glossary.md) — Key terms for this project
- [Decisions](./decisions/) — Major decisions and direction shifts (ADRs)
- [Rules](./rules/) — Reusable heuristics, guidelines, and conventions
- [Pages](./pages/) — Concepts, entities, and artifacts of this project
- [Learnings](./learnings/) — Captured learnings and insights
- [Preferences](./preferences/) — Captured preferences and conventions
