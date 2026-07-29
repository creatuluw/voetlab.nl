---
type: Rule
title: Keep .wiki_ignore in sync with noise directories
description: When (re)generating `docs/wiki/architecture/file-tree.md`, ensure regenerable / noise
tags: [wiki, file-tree, tooling]
timestamp: "2026-07-29T20:25:24.997Z"
---

# Keep .wiki_ignore in sync with noise directories

When (re)generating `docs/wiki/architecture/file-tree.md`, ensure regenerable / noise
directories are listed in `.wiki_ignore`, not just `.gitignore`. The two files serve
different purposes:

- `.gitignore` — what **git** ignores (version control).
- `.wiki_ignore` — what the **wiki file-tree annotator** walks when building the annotated tree page.

## Guideline

Before regenerating the file tree, add any path that would flood the tree with
hundreds of identical or machine-local entries. Currently this includes:

- `.git/` — the git object store; without exclusion the tree sprouts ~300
  indistinguishable `.git/objects/<hash>` entries.
- `tests/out/` — per-feature inspectable test artifacts, regenerated on every
  `pytest` run.

## Rationale

A skimmable, per-entry-annotated file tree is the whole point of the page. A
single `.git/` omission turns it into ~300 lines of hash noise that bury the
real source paths. The wiki annotator does not read `.gitignore`, so ignoring
`.git/` at the VCS level is not enough — `.wiki_ignore` is the lever.

## Related

- [[learnings/canonical-repo-location-and-gitignore-policy]] — covers what **git** ignores; this rule covers the wiki annotator's separate exclude list.
