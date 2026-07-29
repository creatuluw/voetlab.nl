# models/ — consolidated weights for FTP distribution

This folder holds **every model weight and checkpoint voetlab needs**, in one place,
so it can be uploaded wholesale to an FTP server (or any static host) and fetched at
deploy time. The files here are **large binaries** — they are git-ignored (see
`.gitignore` → `/models/*.pt`) and intentionally NOT committed; this README is the only
tracked file, so the set is documented and reproducible even though the bytes live on FTP.

**Canonical download host:** https://voetlab.nl/models/ — the project's mirror of every
weight below. Fetch into this folder (or into wherever your `meta` keys point).

## Manifest

| File | Size | Purpose | Runtime key | Source |
|------|------|---------|-------------|--------|
| `yolov8s.pt` | ~22 MB | Default YOLO detector (persons + ball), COCO classes | `meta["model_path"]` (default `"yolov8s.pt"`) | [Ultralytics YOLOv8s](https://github.com/ultralytics/assets/releases) |
| `martinjolif_ball.pt` | ~5 MB | **Primary** high-recall football-ball model for SAHI (~98% ball-frame recall) | `meta["ball_model_path"]` | [HF: martinjolif/yolo-football-ball-detection](https://huggingface.co/martinjolif/yolo-football-ball-detection/resolve/main/yolo-football-ball-detection.pt) |
| `rajatdave_ball.pt` | ~6 MB | Alternate football-ball model (SAHI) | `meta["ball_model_path"]` | vendored alternate ball model |
| `yaku_ball.pt` | ~6 MB | Alternate football-ball model (SAHI) | `meta["ball_model_path"]` | vendored alternate ball model |
| `tvcalib_calib_train59.pt` | ~467 MB | TVCalib full-camera calibration checkpoint (segment_localization `train_59.pt`) | `meta["calib_checkpoint"]` | [MM4SPA/tvcalib](https://github.com/MM4SPA/tvcalib) `data/segment_localization/` |

**Total: ~506 MB.**

## Where the code reads these

The package resolves its own default locations in `voetlab/paths.py`
(`voetlab/models/*` for detection, `voetlab/external/tvcalib/data/.../train_59.pt` for
calibration). At runtime, paths are **overridable via `meta` keys** (see the table above),
so a deployment that downloads this folder from FTP just points those keys here, e.g.:

```python
voetlab.run(video, meta={
    "model_path":      "models/yolov8s.pt",
    "ball_model_path": "models/martinjolif_ball.pt",
    "calib_checkpoint":"models/tvcalib_calib_train59.pt",
    "tvcalib_path":    "external/tvcalib",   # the TVCalib source repo (code, not weights)
})
```

> The TVCalib **source** (the `external/tvcalib/` repo, code only — its 467 MB data dir is
> git-ignored) is separate from the weights and is not part of this FTP bundle.

## Re-populating this folder

Preferred — download from the canonical host:

```bash
curl -L -o models/yolov8s.pt               https://voetlab.nl/models/yolov8s.pt
curl -L -o models/martinjolif_ball.pt      https://voetlab.nl/models/martinjolif_ball.pt
curl -L -o models/rajatdave_ball.pt        https://voetlab.nl/models/rajatdave_ball.pt
curl -L -o models/yaku_ball.pt             https://voetlab.nl/models/yaku_ball.pt
curl -L -o models/tvcalib_calib_train59.pt https://voetlab.nl/models/tvcalib_calib_train59.pt
```

Or copy back from the package's vendored copy (offline):

```bash
# detection weights
cp voetlab/models/*.pt models/
# calibration checkpoint
cp voetlab/external/tvcalib/data/segment_localization/train_59.pt models/tvcalib_calib_train59.pt
```

## Uploading to FTP

Upload the contents of this folder (`mput models/*.pt`) to your FTP server, then have your
deploy script download them into the same relative paths (or set the `meta` keys to the
download location). Keep the filenames stable — the runtime keys reference them by name.
