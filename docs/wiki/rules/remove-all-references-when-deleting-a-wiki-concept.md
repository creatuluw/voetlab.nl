---
type: Rule
title: Remove all references when deleting a wiki concept
description: Guideline
tags: [wiki, maintenance, okf]
timestamp: "2026-07-29T17:42:45.375Z"
---

# Remove all references when deleting a wiki concept

## Guideline

When deleting a wiki concept (any `.md` under `decisions/`, `learnings/`, `rules/`,
`pages/`), also remove **every reference to its slug** — otherwise you ship dangling links
that break navigation and link-checking.

## Where references hide in this setup

- `docs/wiki/index.md` — the Navigation map bullets (`concept-id — title — description`).
- `docs/wiki/<folder>/index.md` — per-folder index bullets (e.g. `learnings/index.md`,
  `decisions/index.md`).
- `docs/wiki/changelog/YYYY-MM.jsonl` — the entry that logged the concept's creation.
- `[[slug]]` wikilinks inside sibling concept bodies.

## How to do it

1. Note the exact slug(s) being removed.
2. Grep repo-wide for each slug (not just `docs/wiki/`).
3. Delete the `.md` file(s).
4. Strip the matching bullets/lines/entries from index + changelog.
5. Re-grep to confirm **zero matches** before committing.

## Why

Deleting only the `.md` leaves index bullets and changelog lines pointing at files that no
longer exist — the OKF link-check (`wiki_validate`) flags these as broken links (W4) and the
navigation map becomes misleading. Cleaning up at deletion time is far cheaper than hunting
dangling refs later.
