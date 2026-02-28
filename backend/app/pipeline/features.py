"""Extract biomechanical features from raw keypoints.

Each lift type maps 17 raw COCO keypoints to a small set of
meaningful angles / distances that the autoencoder was trained on.

Feature counts must match ``LIFT_CONFIGS`` in neuralnet.py:
  squat    -> 4  (knee_angle, hip_angle, spine_angle, bar_path_x)
  bench    -> 3  (elbow_angle, shoulder_angle, bar_path_diag)
  deadlift -> 3  (back_rounding, hip_hinge, bar_shin_dist)
"""

from __future__ import annotations

import math

import numpy as np

# ── keypoint index shortcuts ────────────────────────────────
_R_SHOULDER, _L_SHOULDER = 5, 6
_R_ELBOW, _L_ELBOW = 7, 8
_R_WRIST, _L_WRIST = 9, 10
_R_HIP, _L_HIP = 11, 12
_R_KNEE, _L_KNEE = 13, 14
_R_ANKLE, _L_ANKLE = 15, 16
_NOSE = 0


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at vertex *b* formed by segments ba and bc, in degrees."""
    ba = a - b
    bc = c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def _midpoint(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a + b) / 2.0


# ── per-lift extractors ────────────────────────────────────

def squat_features(xy: np.ndarray) -> np.ndarray:
    """Return 4 features: knee_angle, hip_angle, spine_angle, bar_path_x."""
    mid_hip = _midpoint(xy[_R_HIP], xy[_L_HIP])
    mid_shoulder = _midpoint(xy[_R_SHOULDER], xy[_L_SHOULDER])
    mid_knee = _midpoint(xy[_R_KNEE], xy[_L_KNEE])
    mid_ankle = _midpoint(xy[_R_ANKLE], xy[_L_ANKLE])

    knee_angle = _angle(mid_hip, mid_knee, mid_ankle)
    hip_angle = _angle(mid_shoulder, mid_hip, mid_knee)
    spine_angle = _angle(xy[_NOSE], mid_shoulder, mid_hip)
    bar_path_x = float(mid_shoulder[0])  # x-coord as proxy for bar

    return np.array([knee_angle, hip_angle, spine_angle, bar_path_x], dtype=np.float32)


def bench_features(xy: np.ndarray) -> np.ndarray:
    """Return 3 features: elbow_angle, shoulder_angle, bar_path_diag."""
    mid_shoulder = _midpoint(xy[_R_SHOULDER], xy[_L_SHOULDER])
    mid_elbow = _midpoint(xy[_R_ELBOW], xy[_L_ELBOW])
    mid_wrist = _midpoint(xy[_R_WRIST], xy[_L_WRIST])
    mid_hip = _midpoint(xy[_R_HIP], xy[_L_HIP])

    elbow_angle = _angle(mid_shoulder, mid_elbow, mid_wrist)
    shoulder_angle = _angle(mid_hip, mid_shoulder, mid_elbow)
    bar_path_diag = float(np.linalg.norm(mid_wrist - mid_shoulder))

    return np.array([elbow_angle, shoulder_angle, bar_path_diag], dtype=np.float32)


def deadlift_features(xy: np.ndarray) -> np.ndarray:
    """Return 3 features: back_rounding, hip_hinge, bar_shin_dist."""
    mid_shoulder = _midpoint(xy[_R_SHOULDER], xy[_L_SHOULDER])
    mid_hip = _midpoint(xy[_R_HIP], xy[_L_HIP])
    mid_knee = _midpoint(xy[_R_KNEE], xy[_L_KNEE])
    mid_ankle = _midpoint(xy[_R_ANKLE], xy[_L_ANKLE])
    mid_wrist = _midpoint(xy[_R_WRIST], xy[_L_WRIST])

    back_rounding = _angle(xy[_NOSE], mid_shoulder, mid_hip)
    hip_hinge = _angle(mid_shoulder, mid_hip, mid_knee)
    bar_shin_dist = float(np.linalg.norm(mid_wrist - mid_ankle))

    return np.array([back_rounding, hip_hinge, bar_shin_dist], dtype=np.float32)


EXTRACTORS = {
    "squat": squat_features,
    "bench": bench_features,
    "deadlift": deadlift_features,
}


def extract(lift_type: str, keypoints_seq: list[dict]) -> np.ndarray:
    """Convert a sequence of keypoint dicts to a (T, F) feature matrix.

    *keypoints_seq* contains dicts with ``"xy"`` arrays (shape 17×2).
    Frames with ``None`` are skipped.
    """
    fn = EXTRACTORS[lift_type]
    rows = [fn(kp["xy"]) for kp in keypoints_seq if kp is not None]
    if not rows:
        return np.empty((0, len(EXTRACTORS[lift_type](np.zeros((17, 2))))))
    return np.stack(rows)
