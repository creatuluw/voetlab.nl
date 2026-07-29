---
type: Learning
title: Package/import name is voetlab, product/domain is voetlab.nl
description: "After the rename, **two distinct names** exist for the same product and they must not be conflated:"
tags: [naming, packaging, rename]
timestamp: "2026-07-29T17:37:44.116Z"
---

# Package/import name is voetlab, product/domain is voetlab.nl

After the rename, **two distinct names** exist for the same product and they must not be conflated:

- **`voetlab`** — the **Python package/import name** and `pyproject.toml` package name (`name = "voetlab"`, `packages.find include = ["voetlab*"]`). Used in every `import voetlab`, module path, `__init__.py`, and the package directory `voetlab/`.
- **`voetlab.nl`** — the **product name and the domain** (the website the framework powers). Used in prose, docs, README headings, and the GitHub repo URL `https://github.com/creatuluw/voetlab.nl`.

## Why the split
A dot is not valid in a Python module/import name, so the code-facing name cannot be `voetlab.nl`. The cleanest mapping: drop the `.nl` for the import, keep the full domain for everything user/product-facing.

## Gotcha
When grepping/renaming, `voetlab.nl` and `voetlab` are different tokens. A naive find-replace of one to the other will either break imports (if `voetlab` → `voetlab.nl` lands in `.py`) or under-rename the product name (if `voetlab.nl` → `voetlab` lands in prose). Treat them as two intentional names: code uses `voetlab`, prose/product uses `voetlab.nl`.

## Also renamed in the same pass
- `PREDA` → `voetlab`, `statspreda.com` → `voetlab.nl`.
- Env vars `PITCHKIT_*` → `VOETLAB_*`; config `pitchkit_botsort.yaml` → `voetlab_botsort.yaml`.

## Source
- `pyproject.toml` — `name = "voetlab"`, package include
- `voetlab/__init__.py` — the import surface
- Repo URL `https://github.com/creatuluw/voetlab.nl`
