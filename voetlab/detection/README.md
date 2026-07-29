# voetlab/detection — per-frame detection (pipeline entry point)

## What's here
- **`detect.py`** — `detect(video, ...) -> Result({"frames": {frame_no: [boxes]}})`: YOLO
  person + ball per frame. Helpers: `boxes_from_result()`, `annotate()`.
  Registered as feature **`"detect"`** (deps: none).

## How to use
```python
from voetlab.pipeline.default import run_feature
res = run_feature("detect", "football-1.mp4", meta={"max_frames": 50, "conf": 0.3})
boxes_by_frame = res.value["frames"]      # {1: [...], 2: [...], ...}
```
CLI: `python -m voetlab.pipeline.cli football-1.mp4 --feature detect --max-frames 50`

## When to use
Always the **first** pipeline stage. Inject `meta={"model": <fake>}` in unit tests to avoid
weight download. Lower `conf` for more recall (more false positives); raise `imgsz` via meta.

## Quality & limitations — **READ the `detect.py` header comment**
- GOOD: person detection (COCO class 0), high recall on broadcast footage.
- WEAK: the BALL — COCO class 32 = baseball/tennis, **not football** → ~18% frame coverage,
  which starves every ball-dependent downstream stat.
- Upgrade: **T8** (football-ball model + SAHI sliced inference) — same interface.

## Tests
`tests/test_detect.py` — mocked-YOLO unit tests (fast) + a real-footage smoke that dumps
`tests/out/detect/annotated.png`.

## Not here yet (planned)
- T8: football-ball detector + SAHI sliced inference for ball recall.

## Validated high-recall ball detection (T8) — the big win

COCO class-32 detects the ball on **~1%** of frames on `football-1.mp4`. **SAHI sliced
inference + a specialist football-ball model = 98%** (measured). Use:

```python
from voetlab.detection.detect import detect_ball_sahi
res = detect_ball_sahi("football-1.mp4", "models/martinjolif_ball.pt", conf=0.15, slice_size=512)
# res.value["frames"][f] = ball boxes (class normalized to BALL=32); res.meta["coverage"]
```
Get the model (free, ~5.5 MB):
```bash
curl -L https://huggingface.co/martinjolif/yolo-football-ball-detection/resolve/main/yolo-football-ball-detection.pt -o models/martinjolif_ball.pt
```
Also runnable as a pipeline feature: `run_feature("detect_ball", video, meta={"ball_model_path": ...})`.
Note: SAHI is N× inference/frame (slower); the recall gain is worth it for the ball.
