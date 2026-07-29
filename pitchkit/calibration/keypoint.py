"""T4 (detector half) — pitch landmark keypoints → homography point pairs.

The research finding: we do NOT need TVCalib's full camera-parameter solver. A segmentation
model (TVCalib ``train_59.pt``) → line-extremity points → pair each with its known IFAB
template metre coordinate → feed straight into ``estimate_homography`` (or DLT-from-lines via
``homography_from_keypoints``). The seg-model→extremity extraction needs the external tvcalib
setup (see wiki learning 'tvcalib-keypoint-detection-integration').

Quality & when to use
- GOOD: deterministic, exact pairing; the IFAB template is the standard pitch geometry.
- WEAK: needs a detector that names landmarks (TVCalib seg + extremity extraction); broadcast
  frames often show <4 usable lines, so sample several frames (see ``calibrate`` feature).
- When: call per camera shot (the ``calibrate`` feature samples frames), reuse the last good H.
"""
from __future__ import annotations

PITCH_M = (105.0, 68.0)

# Named IFAB pitch landmarks in metres (x = length 0-105, y = width 0-68).
TEMPLATE_POINTS = {
    "corner_0_0": (0.0, 0.0), "corner_105_0": (105.0, 0.0),
    "corner_0_68": (0.0, 68.0), "corner_105_68": (105.0, 68.0),
    "halfway_0": (52.5, 0.0), "halfway_68": (52.5, 68.0),
    "center": (52.5, 34.0),
    "lbox_near_t": (0.0, 13.84), "lbox_far_t": (16.5, 13.84),
    "lbox_near_b": (0.0, 54.16), "lbox_far_b": (16.5, 54.16),
    "rbox_near_t": (105.0, 13.84), "rbox_far_t": (88.5, 13.84),
    "rbox_near_b": (105.0, 54.16), "rbox_far_b": (88.5, 54.16),
    "penalty_left": (11.0, 34.0), "penalty_right": (94.0, 34.0),
}


def pairs_from_keypoints(image_by_name: dict, template: dict = TEMPLATE_POINTS):
    """Given detected landmarks {name: (x_px, y_px)}, return (image_pts, template_pts) lists
    of matched pairs (drops any name not in ``template``)."""
    img, tpl = [], []
    for name, px in image_by_name.items():
        if name in template:
            img.append((float(px[0]), float(px[1])))
            tpl.append(template[name])
    return img, tpl


def is_ground_line(name: str) -> bool:
    """A usable 2D pitch line: True unless it's a 3D goal structure, an arc/circle, or unknown.

    From the TVCalib study: goal crossbars/posts are elevated 3D objects and arcs aren't
    straight lines, so both corrupt a 2D ground-plane homography if kept.
    """
    return "unknown" not in name and not name.startswith("Goal") and not name.startswith("Circle")


def _dedup_points(pts, min_sep: float):
    """Greedy dedup of points closer than ``min_sep`` (same units as the points)."""
    kept = []
    for p in pts:
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > min_sep * min_sep for q in kept):
            kept.append(p)
    return kept


def filter_keypoints(kp, *, ground_only: bool = True, min_separation: float = 0.0, min_points: int = 2):
    """Quality-gate keypoints → cleaner, more reliable detections.

    - ``ground_only``: drop 3D goal structures, arcs, and unknowns (non-ground).
    - ``min_separation``: dedup near-duplicate extremity points within each line (>0).
    - ``min_points``: drop lines with fewer surviving points (a line needs >=2 to be useful).
    """
    out = {}
    for name, pts in kp.items():
        if ground_only and not is_ground_line(name):
            continue
        pts = [(float(x), float(y)) for (x, y) in pts]
        if min_separation > 0:
            pts = _dedup_points(pts, min_separation)
        if len(pts) >= min_points:
            out[name] = pts
    return out


def line_coverage(kp_list):
    """Multi-frame line coverage: ``{line_class: #frames it was detected in}``.

    Valid across frames because we count line CLASSES — the camera moves between frames, so
    image-space points cannot be merged, but a class seen in many frames is trustworthy.
    """
    from collections import Counter
    counts = Counter()
    for kp in kp_list:
        counts.update(kp.keys())
    return dict(counts)


def keypoint_summary(kp):
    """Diagnostic: ``{n_lines, n_ground_lines, classes}``."""
    return {
        "n_lines": len(kp),
        "n_ground_lines": sum(1 for k in kp if is_ground_line(k)),
        "classes": list(kp.keys()),
    }


def _load_tvcalib_model(checkpoint, device=None):
    """Load the TVCalib DeepLabV3 seg model (returns None if tvcalib/checkpoint unavailable)."""
    try:
        import sys
        import torch  # noqa: F401
        if not any("tvcalib" in p for p in sys.path):
            return None
        from tvcalib.inference import InferenceSegmentationModel
    except Exception:
        return None
    if not checkpoint:
        return None
    dev = device or ("cuda" if __import__("torch").cuda.is_available() else "cpu")
    try:
        return InferenceSegmentationModel(checkpoint, dev)
    except Exception:
        return None


def detect_keypoints_tvcalib(frame, *, checkpoint=None, device=None, model=None,
                             seg_w=455, seg_h=256, ground_only=True, min_separation=0.0,
                             min_points=2):
    """Run TVCalib seg → line-extremity extraction on one frame.

    Returns ``{line_class: [(x_img, y_img), ...]}`` in FULL-IMAGE pixels, or ``{}`` if
    unavailable. Pass a pre-loaded ``model`` (from ``_load_tvcalib_model``) to avoid reloading
    the 488 MB checkpoint per frame.
    """
    if model is None:
        model = _load_tvcalib_model(checkpoint, device)
        if model is None:
            return {}
    try:
        import torch
        import torchvision.transforms as T
        from PIL import Image
        from sn_segmentation.src.custom_extremities import generate_class_synthesis, get_line_extremities
    except Exception:
        return {}
    img = Image.fromarray(frame[:, :, ::-1])
    x = (T.Compose([T.Resize((seg_h, seg_w)), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])]
                  )(img).unsqueeze(0).to(model.device))
    with torch.no_grad():
        skel = model.inference(x)[0].cpu().numpy()
    synth = generate_class_synthesis(skel, radius=4)
    kp = get_line_extremities(synth, maxdist=30, width=seg_w, height=seg_h,
                              num_points_lines=4, num_points_circles=8)
    h0, w0 = frame.shape[:2]
    full = {k: [(float(p["x"]) * w0, float(p["y"]) * h0) for p in v] for k, v in kp.items()}
    # Guarantee better keypoints: drop non-ground classes, dedup, drop degenerate lines.
    return filter_keypoints(full, ground_only=ground_only, min_separation=min_separation,
                            min_points=min_points)


def homography_from_keypoints(kp, width: int, height: int):
    """Build a homography (IMAGE -> TEMPLATE) from TVCalib line keypoints via DLT-from-lines.

    ``kp`` = ``{line_class: [(x_img, y_img), ...]}`` in full-image pixels. Pairs each detected
    line with its SoccerPitch template line and solves DLT (needs the ``soccernet`` package).
    Returns ``np.ndarray`` 3x3 or ``None`` if <4 valid line correspondences.
    """
    import numpy as np
    from SoccerNet.Evaluation.utils_calibration import SoccerPitch

    from pitchkit.calibration.homography_lines import (
        estimate_homography_from_line_correspondences,
        normalization_transform,
    )

    field = SoccerPitch()
    line_matches, src_pts, target_pts = [], [], []
    for k, pts in kp.items():
        if ("unknown" in k or k.startswith("Goal") or k.startswith("Circle")
                or k not in field.line_extremities_keys or len(pts) < 2):
            continue
        p1 = np.array([pts[0][0], pts[0][1], 1.0])
        p2 = np.array([pts[1][0], pts[1][1], 1.0])
        src_pts.extend([p1[:2], p2[:2]])
        line = np.cross(p1, p2)
        if not np.all(np.isfinite(line)):
            continue
        line_pitch = field.get_2d_homogeneous_line(k)
        if line_pitch is None:
            continue
        line_matches.append((line_pitch, line))
        for key in field.line_extremities_keys[k]:
            target_pts.append(field.point_dict[key][:2])

    if len(line_matches) < 4:
        return None
    T1 = normalization_transform(target_pts)
    T2 = normalization_transform(src_pts)
    ok, H = estimate_homography_from_line_correspondences(line_matches, T1, T2)
    if not ok:
        return None
    return np.linalg.inv(H)  # image -> template (pixels -> pitch coords)


def detect_keypoints(frame, seg_model=None) -> dict:
    """Run a segmentation/keypoint model on ``frame`` → {landmark_name: (x_px, y_px)}.

    Without a ``seg_model`` this returns ``{}`` — the real TVCalib seg → line-extremity
    extraction is the ops integration (use ``detect_keypoints_tvcalib`` instead).
    """
    if seg_model is None:
        return {}
    raise NotImplementedError(
        "seg-model keypoint extraction is the ops integration; use detect_keypoints_tvcalib, "
        "or pass image_by_name to pairs_from_keypoints directly."
    )
