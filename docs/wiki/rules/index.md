# Rules

_Reusable heuristics, guidelines, and conventions will be listed here._
- [Keep .wiki_ignore in sync with noise directories](./keep-wiki-ignore-in-sync-with-noise-directories.md) - When (re)generating `docs/wiki/architecture/file-tree.md`, ensure regenerable / noise
- [Per-frame pipeline stages emit throttled progress via state.progress](./per-frame-pipeline-stages-emit-throttled-progress-via-state-.md) - Stages with a per-frame loop emit progress events through the optional `state.progress` callback (a `Callable[[dict], None]`, default `None`). The runner always
