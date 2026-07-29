# Rules

Reusable heuristics, guidelines, and conventions for voetlab.

- [Gitignore large checkpoints, document the download instead](./gitignore-large-checkpoints-document-the-download-instead.md) — never commit >100 MB weights; exclude them and document the download URL.
- [Keep .wiki_ignore in sync with noise directories](./keep-wiki-ignore-in-sync-with-noise-directories.md) — when (re)generating `docs/wiki/architecture/file-tree.md`, ensure regenerable/noise dirs are excluded.
- [Per-frame pipeline stages emit throttled progress via state.progress](./per-frame-pipeline-stages-emit-throttled-progress-via-state-.md) — stages with a per-frame loop emit progress through the optional `state.progress` callback.
- [Remove all references when deleting a wiki concept](./remove-all-references-when-deleting-a-wiki-concept.md) — strip every slug reference (indexes, changelog, wikilinks) so no dangling links ship.
- [Verify FTP-uploaded model weights by byte size before trusting them](./verify-ftp-uploaded-model-weights-by-byte-size-before-trusti.md) - Guideline
