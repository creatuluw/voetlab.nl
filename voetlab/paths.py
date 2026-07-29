"""Resolved paths to the model weights vendored inside the voetlab package.

The weights ship with the framework (declared as package data in pyproject.toml), so
installing voetlab installs them too. Everything resolves relative to this file, so it
works for both editable (``pip install -e``) and wheel installs.

Vendored assets:
  models/yolov8s.pt                                  — default YOLO detector
  models/martinjolif_ball.pt                         — high-recall football-ball model (SAHI)
  models/{rajatdave,yaku}_ball.pt                    — alternate ball models
  external/tvcalib/                                  — TVCalib repo (sn_segmentation + solver)
  external/tvcalib/data/segment_localization/train_59.pt — calibration checkpoint
"""
from __future__ import annotations

from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent

models_dir: Path = _PKG_DIR / "models"
external_dir: Path = _PKG_DIR / "external"
tvcalib_dir: Path = external_dir / "tvcalib"

yolo_model_path: Path = models_dir / "yolov8s.pt"
ball_model_path: Path = models_dir / "martinjolif_ball.pt"
calib_checkpoint: Path = tvcalib_dir / "data" / "segment_localization" / "train_59.pt"


def status() -> dict[str, bool]:
	"""Report which vendored assets are present (handy for /healthz-style diagnostics)."""
	return {
		"yolo": yolo_model_path.is_file(),
		"ball_model": ball_model_path.is_file(),
		"tvcalib": tvcalib_dir.is_dir(),
		"calib_checkpoint": calib_checkpoint.is_file(),
	}
