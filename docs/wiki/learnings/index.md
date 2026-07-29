# Learnings

Captured non-obvious facts, gotchas, and behaviors about voetlab.

- [Model weights are hosted at voetlab.nl/models](./model-weights-are-hosted-at-voetlab-nl-models.md) — weights are large binaries not in git; download from https://voetlab.nl/models/ and pass via `meta` keys.
- [Models folder is an FTP deploy bundle, not the runtime source](./models-folder-is-ftp-deploy-bundle.md) — `models/` is the consolidated distribution bundle; the runtime reads via `paths.py` / `meta`, not this folder directly.
- [TVCalib calibration checkpoint is gitignored, not in history](./tvcalib-calibration-checkpoint-is-gitignored-not-in-history.md) — the ~488 MB `train_59.pt` is gitignored (over GitHub's 100 MB limit); download it separately.
- [detect_ball slice_size vs ball recall on 1080p](./detect-ball-slice-size-vs-ball-recall-on-1080p.md) — the SAHI `detect_ball` stage's speed is dominated by the slice count, set by `slice_size`.
- [Reliability signal has a hardcoded component](./reliability-signal-has-a-hardcoded-component.md) — `homography_conf` is hardcoded to 1.0 and `tracking_stability` is a proxy, not a true tracker-quality metric.
- [Canonical repo location and gitignore policy](./canonical-repo-location-and-gitignore-policy.md) — GitHub origin (creatuluw/voetlab.nl) and what `.gitignore` treats as regenerable.
