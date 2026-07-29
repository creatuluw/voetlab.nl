# pitchkit/core — shared contracts (no feature logic)

The stable foundation every feature depends on. Dependency-light (numpy + opencv, lazy-imported).

## What's here
- **`result.py`** — `Result` dataclass: the universal **success indicator**. Every feature
  returns `Result.Ok(value, **meta)` / `Result.Fail(error, **meta)`; `bool(result)` reads success.
- **`provenance.py`** — `attach_provenance(event, source_frames, **refs)`: stamps every event
  with the frame(s) it came from. **Required** for all event-producing features.
- **`fixtures.py`** — footage-driven test harness: `load_sample_frames(n)`, `footage_meta()`,
  `dump_artifacts(feature, frames, data, fig)`. Default footage = `football-1.mp4`.

## How to use
```python
from pitchkit.core.result import Result
from pitchkit.core.provenance import attach_provenance
from pitchkit.core.fixtures import load_sample_frames, dump_artifacts

return Result.Ok({"x": 1}, feature="mine")          # success
return Result.Fail("no input", feature="mine")      # failure (flagged, not raised)
attach_provenance(event, source_frames=[42])         # event → traceable to frame 42
```

## When to use
- Writing a feature → return `Result`; if it emits events, call `attach_provenance`.
- Writing a feature test → load frames via `load_sample_frames`, dump via `dump_artifacts`.

## Quality & limitations
Stable by design — no CV logic, so it rarely changes. `dump_artifacts` writes the *first*
frame only (extend to a contact sheet if you need many).

## Tests
`tests/` — `test_result.py`, `test_provenance.py`, `test_fixtures.py` (footage tests skip
gracefully if `football-1.mp4` is absent).

## Not here yet
Nothing planned — this is the stable foundation.

## Original reference
No `src/` equivalent; these are new framework contracts.
