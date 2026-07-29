---
type: Decision
title: "Brand rename: strip product/old-repo names, keep open-source dep & prior-art names"
description: Context
tags: [rename, branding, attribution]
status: accepted
timestamp: "2026-07-29T17:37:44.116Z"
---

# Brand rename: strip product/old-repo names, keep open-source dep & prior-art names

## Context
Task: rename the app from `pitchkit` (and `PREDA`/`statspreda.com`) to **voetlab** / **voetlab.nl**, and remove/replace all references to *other repos and brands*. The codebase is peppered with third-party names — TVCalib, mplsoccer, ultralytics/YOLO, SAHI, ByteTrack/BoTSORT, SoccerNet, supervision — because the project builds on or integrates them.

## The choice
**Strip** everything that is a product, brand, or pointer to the *old prototype repo*:
- Package/import `pitchkit` → `voetlab`; `PREDA` → `voetlab`; `statspreda.com` → `voetlab.nl`.
- `src/...` "Ported from" provenance lines in ~16 feature files + READMEs (old prototype repo paths).
- Other-tool references in dev docs: a Telegram bot, a Groq report, `mult-agents-football-match-analyzer`, `research_preda_v1_gaps/` folders.
- The deleted `docs/SESSION_TRANSCRIPT.jsonl` (1 MB raw build log saturated with old-repo refs; recoverable from commit `2627a2b`).

**Keep** everything that is a legitimate open-source dependency, prior-art attribution, or the repo's own URL: TVCalib, mplsoccer, ultralytics/YOLO, SAHI, ByteTrack/BoTSORT, SoccerNet, supervision, and `https://github.com/creatuluw/voetlab.nl`.

## Alternatives considered
- **Strip everything including dep/prior-art names.** Rejected: would delete accurate attribution and break links to real dependencies the code imports. The user's intent ("other repos/brands") is about *competing product / old-prototype* identity, not open-source building blocks.
- **Keep provenance `src/` lines as history.** Rejected: they named the old private prototype repo and contradicted the new standalone, copyable identity.

## Rationale
The boundary is **competing/old-product identity vs. open-source building blocks**. A football-analytics repo that silently drops "built on TVCalib / mplsoccer / YOLO" loses both credit and discoverability for no benefit. The product/brand and old-prototype-repo identifiers, by contrast, are pure noise once the rename lands.

## Consequences
- A future brand sweep can apply the same rule: strip product/brand/old-repo tokens; keep dep + prior-art + own-URL.
- If product direction ever wants full white-label scrubbing of third-party names, that is a separate, deliberate decision — say the word.
