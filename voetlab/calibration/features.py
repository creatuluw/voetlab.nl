"""Calibration feature — TVCalib solver (primary, accurate) → H; DLT fallback.

Samples several frames, loads the seg model ONCE, runs the full TVCalib camera solver per
frame, and accepts the lowest-``loss_ndc_total`` H below τ≈0.05 (the paper uses 0.019). Falls
back to the DLT-from-lines baseline (gated by reprojection error) if the solver is unavailable.
Publishes ``H`` to ``state.meta["H"]`` so metric features (stats/voronoi/pitch_control) emit
metres + tactical output. Requires the external tvcalib setup (see wiki learning
'tvcalib-keypoint-detection-integration').
"""
from __future__ import annotations

import sys

from voetlab.core.result import Result
from voetlab.pipeline.registry import feature
from voetlab.pipeline.runner import PipelineState

# TVCalib self-verification threshold on the optimization loss (paper τ≈0.019; we accept a
# little more headroom for broadcast keypoints).
SOLVER_LOSS_TAU = 0.05


def _is_ground_line(k, field) -> bool:
    return ("unknown" not in k and not k.startswith("Goal") and not k.startswith("Circle")
            and k in field.line_extremities_keys)


@feature("calibrate")
def _calibrate_feature(state: PipelineState) -> Result:
    meta = state.meta or {}
    ckpt = meta.get("calib_checkpoint")
    if not ckpt:
        return Result.Fail("calibrate needs meta['calib_checkpoint']", feature="calibrate")
    tvp = meta.get("tvcalib_path", "external/tvcalib")
    if not any("tvcalib" in p for p in sys.path):
        sys.path.insert(0, tvp)

    import cv2
    import numpy as np
    from SoccerNet.Evaluation.utils_calibration import SoccerPitch

    from voetlab.calibration.keypoint import (
        _load_tvcalib_model,
        detect_keypoints_tvcalib,
        homography_from_keypoints,
    )
    from voetlab.calibration.tvcalib_solver import calibrate_with_tvcalib

    model = _load_tvcalib_model(ckpt)
    if model is None:
        return Result.Fail("tvcalib model unavailable (check checkpoint + deps)", feature="calibrate")
    field = SoccerPitch()

    def reproj_err(H, kp):  # used only for the DLT fallback
        errs = []
        for k, pts in kp.items():
            if not _is_ground_line(k, field) or len(pts) < 2:
                continue
            for i, key in enumerate(field.line_extremities_keys[k][:2]):
                if i >= len(pts):
                    break
                tp = field.point_dict[key][:2]
                got = H @ np.array([pts[i][0], pts[i][1], 1.0])
                got = got / got[2]
                errs.append(float(np.hypot(got[0] - tp[0], got[1] - tp[1])))
        return float(np.mean(errs)) if errs else 1e9

    cap = cv2.VideoCapture(state.footage)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idxs = (np.linspace(0, max(0, total - 1), num=12).astype(int) if total > 0 else [0])
    best_solver = None  # (loss, H, lines)
    best_dlt = None     # (err, H, lines)
    for idx in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue
        kp = detect_keypoints_tvcalib(frame, model=model)
        if not kp:
            continue
        solved = calibrate_with_tvcalib(kp, frame.shape[1], frame.shape[0])
        if solved is not None:
            H, loss = solved
            if loss < SOLVER_LOSS_TAU and (best_solver is None or loss < best_solver[0]):
                best_solver = (loss, H, list(kp.keys()))
                if loss < 0.02:  # converged well; stop early
                    break
            continue
        # solver unavailable → DLT fallback
        H = homography_from_keypoints(kp, frame.shape[0], frame.shape[1])
        if H is None:
            continue
        err = reproj_err(H, kp)
        if err < 15.0 and (best_dlt is None or err < best_dlt[0]):
            best_dlt = (err, H, list(kp.keys()))
    cap.release()

    if best_solver is not None:
        loss, H, lines = best_solver
        state.meta["H"] = H
        return Result.Ok({"H": H.tolist(), "lines": lines, "method": "tvcalib_solver",
                          "solver_loss": round(float(loss), 5)},
                         feature="calibrate", n_lines=len(lines))
    if best_dlt is not None:
        err, H, lines = best_dlt
        state.meta["H"] = H
        return Result.Ok({"H": H.tolist(), "lines": lines, "method": "dlt_fallback",
                          "reproj_error_m": round(err, 3)},
                         feature="calibrate", n_lines=len(lines))
    return Result.Fail("calibration failed (no frame produced a verifiable homography)",
                       feature="calibrate")
