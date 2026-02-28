"""YOLOv8 pose estimation wrapper.

Extracts COCO-17 keypoints from each frame.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

# COCO 17-keypoint names (same order used by YOLOv8-pose)
COCO_KPTS = [
    "nose", "right_eye", "left_eye", "right_ear", "left_ear",
    "right_shoulder", "left_shoulder", "right_elbow", "left_elbow",
    "right_wrist", "left_wrist", "right_hip", "left_hip",
    "right_knee", "left_knee", "right_ankle", "left_ankle",
]

# Skeleton connections for drawing
SKELETON = [
    (5, 7), (7, 9),        # left arm
    (6, 8), (8, 10),       # right arm
    (5, 6),                # shoulders
    (5, 11), (6, 12),      # torso
    (11, 12),              # hips
    (11, 13), (13, 15),    # left leg
    (12, 14), (14, 16),    # right leg
    (0, 1), (0, 2),        # nose to eyes
    (1, 3), (2, 4),        # eyes to ears
]

# Default path inside backend/models/
_DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "yolov8n-pose.pt"

_model = None
_model_path_loaded: str | None = None


def get_model(model_path: str | Path | None = None):
    """Lazy-load the YOLOv8 pose model.

    Search order:
      1. *model_path* if provided
      2. ``backend/models/yolov8n-pose.pt``
      3. Ultralytics auto-download (``"yolov8n-pose.pt"``)
    """
    global _model, _model_path_loaded
    from ultralytics import YOLO

    resolved = str(model_path) if model_path else None

    # Re-use cached model if same path
    if _model is not None and resolved == _model_path_loaded:
        return _model

    if model_path and Path(model_path).exists():
        log.info("Loading YOLO pose model from %s", model_path)
        _model = YOLO(str(model_path))
    elif _DEFAULT_MODEL_PATH.exists():
        log.info("Loading YOLO pose model from %s", _DEFAULT_MODEL_PATH)
        _model = YOLO(str(_DEFAULT_MODEL_PATH))
    else:
        log.info("No local model found — Ultralytics will auto-download yolov8n-pose.pt")
        _model = YOLO("yolov8n-pose.pt")

    _model_path_loaded = resolved
    return _model


def extract_keypoints(
    frames: list[np.ndarray],
    model_path: str | Path | None = None,
) -> list[dict | None]:
    """Run pose estimation on each frame.

    Returns a list (one entry per frame).  Each entry is either ``None``
    (no person detected) or a dict::

        {
            "xy":   np.ndarray shape (17, 2),
            "conf": np.ndarray shape (17,),
        }

    Only the most-confident person per frame is returned.
    """
    model = get_model(model_path)
    results: list[dict | None] = []

    for i, frame in enumerate(frames):
        r = model(frame, verbose=False)[0]
        if r.keypoints is None or r.keypoints.xy.shape[0] == 0:
            results.append(None)
            continue

        xy = r.keypoints.xy.cpu().numpy()    # (people, 17, 2)
        cf = r.keypoints.conf.cpu().numpy()  # (people, 17)

        # pick the person with highest mean confidence
        best = int(cf.mean(axis=1).argmax())
        results.append({"xy": xy[best], "conf": cf[best]})

    poses_found = sum(1 for r in results if r is not None)
    log.info("extract_keypoints: %d/%d frames have a detected pose", poses_found, len(frames))
    return results
