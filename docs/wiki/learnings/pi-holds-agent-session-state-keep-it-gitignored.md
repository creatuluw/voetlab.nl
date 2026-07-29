---
type: Learning
title: .pi/ holds agent session state — keep it gitignored
description: `.pi/` (at the repo root) is **agent-harness session state** — e.g. `.pi/todos/` JSON files holding the session's todo lists. It is local tooling state, not pro
tags: [gitignore, tooling, agent-state, rename]
timestamp: "2026-07-29T17:37:44.116Z"
---

# .pi/ holds agent session state — keep it gitignored

`.pi/` (at the repo root) is **agent-harness session state** — e.g. `.pi/todos/` JSON files holding the session's todo lists. It is local tooling state, not product content.

## Why it must stay untracked
Session todos get written with verbatim task text. During the pitchkit → voetlab rename, the per-feature `.pi/todos/*.json` files still contained `pitchkit` / `mult-agents` text long after the codebase was clean, which would have silently violated the "no old-brand references" goal if tracked.

## What was done
Added `.pi/` to `.gitignore` and `git rm --cached`'d the tracked copies (local files kept). This complements [[canonical-repo-location-and-gitignore-policy]] — like the other ignored paths, it is machine/session-local state, not source.

## Gotcha
If you ever verify "no references to brand X remain" with `git grep`, remember tracked-only tools won't see `.pi/`. Use a plain filesystem grep if you want to know whether the agent state still echoes old names — but don't commit fixes into `.pi/`; it's throwaway.
