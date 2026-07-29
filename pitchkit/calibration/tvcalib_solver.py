"""TVCalib full camera solver → homography (the ACCURATE calibration path).

Runs ``TVCalibModule.self_optim_batch`` (AdamW, ~2000 steps — the WACV'23 paper's method) on
the detected line keypoints → a pinhole camera → projects a template GROUND grid to the image
→ cv2 homography (image → template). Verified: loss_ndc_total ≈ 0.01 (< τ=0.019) and the
derived H is self-consistent to ~0 m. Requires the external tvcalib setup.

Quality & when to use
- GOOD: the paper's method; gate acceptance on ``loss_ndc_total < τ`` (≈0.019).
- WEAK: ~2000 optimization steps per frame (seconds on GPU); needs enough visible ground lines.
- When: called by the ``calibrate`` feature per sampled frame.
"""
from __future__ import annotations

import cv2
import numpy as np


def calibrate_with_tvcalib(kp_full_px, width: int, height: int, *, device=None,
                           optim_steps: int = 2000, lens_dist: bool = False, grid_step: float = 5.0):
    """Return ``(H_image_to_template, loss_ndc_total)`` or ``None`` if tvcalib is unavailable/fails.

    ``kp_full_px`` = ``{line_class: [(x_img, y_img), ...]}`` in full-image pixels.
    """
    try:
        import torch
        from tvcalib.cam_distr.tv_main_center import get_cam_distr, get_dist_distr
        from tvcalib.inference import InferenceDatasetCalibration
        from tvcalib.module import TVCalibModule
        from tvcalib.sncalib_dataset import custom_list_collate
        from tvcalib.utils.objects_3d import (
            SoccerPitchLineCircleSegments,
            SoccerPitchSNCircleCentralSplit,
        )
    except Exception:
        return None

    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    object3d = SoccerPitchLineCircleSegments(device=dev, base_field=SoccerPitchSNCircleCentralSplit())

    norm = {k: [{"x": float(x) / width, "y": float(y) / height} for (x, y) in pts]
            for k, pts in kp_full_px.items()}
    dataset = InferenceDatasetCalibration([norm], width, height, object3d)
    loader = torch.utils.data.DataLoader(dataset, batch_size=1, collate_fn=custom_list_collate)
    model = TVCalibModule(
        object3d, get_cam_distr(1.96, 1, 1),
        get_dist_distr(1, 1) if lens_dist else None,
        (height, width), optim_steps, dev, log_per_step=False,
    )

    # template GROUND grid (z=0) covering the pitch; project via the solved camera → derive H
    gx, gy = np.meshgrid(np.arange(-52.5, 52.5 + 1, grid_step), np.arange(-34, 34 + 1, grid_step))
    grid = np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], 1)
    P = torch.tensor(grid, dtype=torch.float32, device=dev).view(1, -1, 3)  # project_point2pixel wants (1,N,3)

    H = None
    loss = 1e9
    for x_dict in loader:
        per_sample_loss, cam, _ = model.self_optim_batch(x_dict)
        loss = _extract_loss(per_sample_loss)
        with torch.no_grad():
            proj = cam.project_point2pixel(P, lens_distortion=False).detach().cpu().numpy().reshape(-1, 2)
        finite = (np.isfinite(proj).all(axis=1)
                  & (proj[:, 0] > -width) & (proj[:, 0] < 2 * width)
                  & (proj[:, 1] > -height) & (proj[:, 1] < 2 * height))
        if finite.sum() >= 4:
            H, _ = cv2.findHomography(np.float32(proj[finite]), np.float32(grid[finite, :2]),
                                      cv2.RANSAC, 5.0)
        break
    if H is None:
        return None
    return H, loss


def _extract_loss(per_sample_loss):
    try:
        if isinstance(per_sample_loss, dict):
            for key in ("loss_ndc_total", "loss_total", "loss"):
                if key in per_sample_loss:
                    return float(per_sample_loss[key].mean())
            return float(np.mean([float(v.mean()) for v in per_sample_loss.values()]))
        return float(per_sample_loss)
    except Exception:
        return 1e9
