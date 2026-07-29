# voetlab/pipeline — feature registry, runner, default graph, CLI

## What's here
- **`registry.py`** — `@feature(name, deps)` decorator + global registry; `registered()`.
- **`runner.py`** — `PipelineState` clipboard; `run(names, footage, meta)` executes features in
  **dependency order**, collects `Result`s, and **FLAGS failures without crashing**;
  `run_feature(name, ...)` isolates ONE feature; `compare(baseline, current)` diffs metrics.
- **`default.py`** — imports all features (so they register) + exposes `run(video)` / `run_feature()`.
- **`cli.py`** — `python -m voetlab.pipeline.cli <video> [--feature NAME] [--max-frames N]`.

## How to use
```python
from voetlab.pipeline.default import run, run_feature

res = run("football-1.mp4", max_frames=50)        # full pipeline: detect→track→ball→teams→events→stats
res.value["data"]["stats"]                        # terminal output
res.value["failed"]                               # any feature that did not finish
run_feature("detect", "football-1.mp4")           # isolate ONE stage
```
```bash
python -m voetlab.pipeline.cli football-1.mp4 --max-frames 50             # full run
python -m voetlab.pipeline.cli football-1.mp4 --feature detect            # isolate
```

## When to use
- `run()` → end-to-end analysis.
- `run_feature()` → develop / debug / inspect ONE feature in isolation.
- Add a new feature → decorate `@feature("name", deps=[...])`; it auto-joins the graph.

## How results carry downstream (important)
Each feature's `Result.value` lands in `state.data[name]`; the next feature reads
`state.get("upstream")`. A failed upstream leaves no value, so downstream features should
handle `state.get(x) is None` (the runner still completes and reports all failures).

## Quality & limitations
Stable core. `compare()` diffs two metric dicts today; a full before/after on real footage
is one CLI flag away once the upgrade features (T6/T8/T9) land.

## Tests
`tests/test_runner.py` (registry / runner / compare / isolation), `tests/test_default.py`
(wiring + an end-to-end smoke on `football-1.mp4`).

## Not here yet (planned)
- Before/after harness wired to baseline-vs-upgraded pipelines on footage.

## Original reference
Replaces ad-hoc orchestration with a dependency-ordered, isolated feature graph.
