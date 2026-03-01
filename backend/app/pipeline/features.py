"""Extract biomechanical features from raw keypoints.

Each lift type maps 17 raw COCO keypoints to a small set of
meaningful angles that the autoencoder was trained on.

Feature counts must match ``LIFT_CONFIGS`` in neuralnet.py:
  squat    -> 3  (shoulder-hip-knee, other_hip-hip-knee, hip-knee-ankle)
  bench    -> 3  (elbow_angle, shoulder_angle, bar_path_diag)
  deadlift -> 3  (back_rounding, hip_hinge, bar_shin_dist)

Squat extraction uses closer-side detection (matching body_tracking.py)
rather than midpoint averaging, so the features match training data.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.interpolate import interp1d

log = logging.getLogger(__name__)

# ── keypoint index shortcuts ────────────────────────────────
_R_SHOULDER, _L_SHOULDER = 5, 6
_R_ELBOW, _L_ELBOW = 7, 8
_R_WRIST, _L_WRIST = 9, 10
_R_HIP, _L_HIP = 11, 12
_R_KNEE, _L_KNEE = 13, 14
_R_ANKLE, _L_ANKLE = 15, 16
_NOSE = 0

_CONF_THRES = 0.5
_EMA_ALPHA = 0.2
_RATIO_DEADZONE = 0.06


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at vertex *b* formed by segments ba and bc, in degrees."""
    ba = a - b
    bc = c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def _midpoint(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a + b) / 2.0


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _seg_len(xy: np.ndarray, conf: np.ndarray, i: int, j: int) -> float | None:
    """Pixel distance between keypoints i and j, or None if low confidence."""
    if conf[i] > _CONF_THRES and conf[j] > _CONF_THRES:
        return _dist(xy[i], xy[j])
    return None


def _detect_closer_side(
    xy: np.ndarray,
    conf: np.ndarray,
    ema_diff: float,
) -> tuple[str | None, float]:
    """Determine which body side is closer to the camera using limb pixel lengths.

    Mirrors the logic in body_tracking.py: compare upper-arm and thigh lengths
    on each side, use EMA smoothing with a deadzone.

    Returns (side_name_or_None, updated_ema_diff).
    """
    left_upper_arm = _seg_len(xy, conf, _L_SHOULDER, _L_ELBOW)
    right_upper_arm = _seg_len(xy, conf, _R_SHOULDER, _R_ELBOW)
    left_thigh = _seg_len(xy, conf, _L_HIP, _L_KNEE)
    right_thigh = _seg_len(xy, conf, _R_HIP, _R_KNEE)

    left_segs = [v for v in (left_upper_arm, left_thigh) if v is not None]
    right_segs = [v for v in (right_upper_arm, right_thigh) if v is not None]

    if not left_segs or not right_segs:
        return None, ema_diff

    left_scale = float(np.mean(left_segs))
    right_scale = float(np.mean(right_segs))

    ratio_diff = (left_scale - right_scale) / max(left_scale, right_scale)
    ema_diff = (1 - _EMA_ALPHA) * ema_diff + _EMA_ALPHA * ratio_diff

    # If both sides are visible and the difference is below the deadzone, 
    # default to the side that was already being tracked if possible, or just pick one.
    if abs(ema_diff) < _RATIO_DEADZONE:
        return "left" if ema_diff >= 0 else "right", ema_diff
    elif ema_diff > 0:
        return "left", ema_diff
    else:
        return "right", ema_diff


# ── per-lift extractors ────────────────────────────────────

# Side-indexed keypoint mapping (matches body_tracking.py IDX dict)
_SIDE_IDX = {
    "l_shoulder": _L_SHOULDER, "r_shoulder": _R_SHOULDER,
    "l_hip": _L_HIP,           "r_hip": _R_HIP,
    "l_knee": _L_KNEE,         "r_knee": _R_KNEE,
    "l_ankle": _L_ANKLE,       "r_ankle": _R_ANKLE,
}


def _get_pt(xy: np.ndarray, conf: np.ndarray, idx: int) -> np.ndarray | None:
    if conf[idx] > _CONF_THRES:
        return xy[idx].astype(np.float32)
    return None


def squat_features_for_frame(
    xy: np.ndarray,
    conf: np.ndarray,
    closest_side: str | None,
) -> np.ndarray | None:
    """Extract 3 squat angles for one frame using the closer side.

    Features (matching body_tracking.py training data):
      [0] shoulder -> hip -> knee  (angle at hip)
      [1] other_hip -> hip -> knee (angle at hip)
      [2] hip -> knee -> ankle     (angle at knee)

    Returns None if the side can't be determined or key joints are missing.
    """
    if closest_side is None:
        return None

    side_prefix = "l_" if closest_side == "left" else "r_"
    other_prefix = "r_" if closest_side == "left" else "l_"

    shoulder = _get_pt(xy, conf, _SIDE_IDX[side_prefix + "shoulder"])
    hip = _get_pt(xy, conf, _SIDE_IDX[side_prefix + "hip"])
    knee = _get_pt(xy, conf, _SIDE_IDX[side_prefix + "knee"])
    ankle = _get_pt(xy, conf, _SIDE_IDX[side_prefix + "ankle"])
    other_hip = _get_pt(xy, conf, _SIDE_IDX[other_prefix + "hip"])

    # All three angles require hip and knee at minimum
    if hip is None or knee is None:
        return None

    ang1 = _angle(shoulder, hip, knee) if shoulder is not None else np.nan
    ang2 = _angle(other_hip, hip, knee) if other_hip is not None else np.nan
    ang3 = _angle(hip, knee, ankle) if ankle is not None else np.nan

    return np.array([ang1, ang2, ang3], dtype=np.float32)


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


# ── simple extractors (bench / deadlift use midpoints) ─────
_SIMPLE_EXTRACTORS = {
    "bench": bench_features,
    "deadlift": deadlift_features,
}


def extract(lift_type: str, keypoints_seq: list[dict]) -> np.ndarray:
    """Convert a sequence of keypoint dicts to a (T, F) feature matrix.

    *keypoints_seq* contains dicts with ``"xy"`` (17x2) and ``"conf"`` (17,)
    arrays.  Entries may be ``None`` (no pose detected that frame).

    For squats, uses closer-side detection matching body_tracking.py.
    For bench/deadlift, uses midpoint averaging.
    """
    if lift_type == "squat":
        return _extract_squat(keypoints_seq)

    fn = _SIMPLE_EXTRACTORS[lift_type]
    rows = [fn(kp["xy"]) for kp in keypoints_seq if kp is not None]
    if not rows:
        return np.empty((0, 3), dtype=np.float32)
    return np.stack(rows)


# ── inference preprocessing (match training pipeline) ────────

def _interpolate_nans(features: np.ndarray) -> np.ndarray:
    """Replace NaN values in each column via linear interpolation."""
    out = features.copy()
    for col in range(out.shape[1]):
        data = out[:, col]
        nans = np.isnan(data)
        if nans.all():
            data[:] = 0.0
        elif nans.any():
            valid = np.where(~nans)[0]
            data[nans] = np.interp(np.where(nans)[0], valid, data[valid])
    return out


def phase_anchor_for_inference(
    features: np.ndarray,
    total_frames: int = 100,
) -> tuple[np.ndarray, int]:
    """Interpolate NaNs and phase-anchor to *total_frames* (hole at midpoint).

    Returns (anchored_features, hole_idx_in_raw).
    """
    clean = _interpolate_nans(features)
    T = clean.shape[0]

    hole_idx = int(np.argmin(clean[:, 0]))
    if hole_idx < 5 or hole_idx > T - 5:
        log.warning("phase_anchor: hole_idx=%d unreliable (T=%d), falling back to T//2", hole_idx, T)
        hole_idx = T // 2

    half = total_frames // 2
    descent = clean[: hole_idx + 1, :]
    ascent = clean[hole_idx:, :]

    t_desc = np.linspace(0, 1, len(descent))
    t_asc = np.linspace(0, 1, len(ascent))
    t_target = np.linspace(0, 1, half)

    anchored_desc = interp1d(t_desc, descent, axis=0, kind="linear")(t_target)
    anchored_asc = interp1d(t_asc, ascent, axis=0, kind="linear")(t_target)

    anchored = np.vstack((anchored_desc, anchored_asc)).astype(np.float32)
    return anchored, hole_idx


def map_mse_to_original(
    mse_anchored: np.ndarray,
    T_raw: int,
    hole_idx: int,
    total_frames: int = 100,
) -> np.ndarray:
    """Map phase-anchored MSE back to the original frame count.

    Works for both per_frame (100,) and per_feature (100, F) arrays.
    """
    half = total_frames // 2

    # For each raw frame, compute its position in the anchored sequence
    raw_positions = np.zeros(T_raw)
    for i in range(T_raw):
        if i <= hole_idx:
            raw_positions[i] = i / max(hole_idx, 1) * (half - 1)
        else:
            remaining = max(T_raw - 1 - hole_idx, 1)
            raw_positions[i] = half + (i - hole_idx) / remaining * (half - 1)

    anchored_idx = np.arange(total_frames, dtype=np.float64)

    if mse_anchored.ndim == 1:
        return np.interp(raw_positions, anchored_idx, mse_anchored)

    # Per-feature: (100, F) → (T_raw, F)
    result = np.zeros((T_raw, mse_anchored.shape[1]))
    for f in range(mse_anchored.shape[1]):
        result[:, f] = np.interp(raw_positions, anchored_idx, mse_anchored[:, f])
    return result


def _extract_squat(keypoints_seq: list[dict]) -> np.ndarray:
    """Squat extraction with closer-side detection and EMA smoothing."""
    rows: list[np.ndarray] = []
    ema_diff = 0.0

    for i, kp in enumerate(keypoints_seq):
        if kp is None:
            log.warning("extract_squat: Frame %d has no keypoints", i)
            continue

        xy = kp["xy"]     # (17, 2)
        conf = kp["conf"]  # (17,)

        closest_side, ema_diff = _detect_closer_side(xy, conf, ema_diff)
        if closest_side is None:
            log.warning("extract_squat: Frame %d missing side detection. Diff=%s, Conf(Avg)=%.2f", i, ema_diff, float(np.mean(conf)))

        feats = squat_features_for_frame(xy, conf, closest_side)

        if feats is not None:
            rows.append(feats)
        else:
            log.warning("extract_squat: Frame %d failed feature extraction for side %s. Conf values: %s", i, closest_side, np.round(conf, 2))

    if not rows:
        return np.empty((0, 3), dtype=np.float32)
    return np.stack(rows)
