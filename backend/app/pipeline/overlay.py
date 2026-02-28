"""Draw skeleton with per-segment error coloring on video frames.

Angle errors map to specific body segments (both sides mirrored):
  Feature 0 — shoulder-hip-knee  → torso/back  (shoulder→hip)
  Feature 1 — other_hip-hip-knee → thigh       (hip→knee)
  Feature 2 — hip-knee-ankle     → shin        (knee→ankle)
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

from .pose import SKELETON, COCO_KPTS

log = logging.getLogger(__name__)

_CONF_THRES = 0.5
_COLOR_GOOD = (0, 200, 0)       # green  (BGR)
_COLOR_BAD = (0, 0, 255)        # red    (BGR)
_COLOR_NEUTRAL = (180, 180, 180) # gray for bones with no error data

# ── COCO keypoint indices ──────────────────────────────────
_L_SHOULDER, _R_SHOULDER = 5, 6
_L_HIP, _R_HIP = 11, 12
_L_KNEE, _R_KNEE = 13, 14
_L_ANKLE, _R_ANKLE = 15, 16

# Map each squat feature index to the skeleton EDGES it should color.
# Each entry is a list of (joint_a, joint_b) tuples — both sides.
_SQUAT_FEATURE_BONES: dict[int, list[tuple[int, int]]] = {
    # Feature 0: shoulder-hip-knee angle → color the BACK (torso segment)
    0: [(_L_SHOULDER, _L_HIP), (_R_SHOULDER, _R_HIP)],
    # Feature 1: other_hip-hip-knee angle → color the THIGH
    1: [(_L_HIP, _L_KNEE), (_R_HIP, _R_KNEE)],
    # Feature 2: hip-knee-ankle angle → color the SHIN
    2: [(_L_KNEE, _L_ANKLE), (_R_KNEE, _R_ANKLE)],
}

# Bones that are NOT colored by any feature (arms, shoulders, hips, head)
# These get drawn in neutral color.
_COLORED_BONES: set[tuple[int, int]] = set()
for bones in _SQUAT_FEATURE_BONES.values():
    for b in bones:
        _COLORED_BONES.add(b)


def _lerp_color(
    t: float,
    good: tuple[int, int, int] = _COLOR_GOOD,
    bad: tuple[int, int, int] = _COLOR_BAD,
) -> tuple[int, int, int]:
    """Interpolate between good (t=0) and bad (t=1)."""
    t = max(0.0, min(1.0, t))
    return (
        int(good[0] + (bad[0] - good[0]) * t),
        int(good[1] + (bad[1] - good[1]) * t),
        int(good[2] + (bad[2] - good[2]) * t),
    )


def _draw_bone(
    frame: np.ndarray,
    xy: np.ndarray,
    cf: np.ndarray,
    a: int,
    b: int,
    color: tuple[int, int, int],
    thickness: int = 3,
) -> None:
    if cf[a] > _CONF_THRES and cf[b] > _CONF_THRES:
        pt1 = (int(xy[a][0]), int(xy[a][1]))
        pt2 = (int(xy[b][0]), int(xy[b][1]))
        cv2.line(frame, pt1, pt2, color, thickness, cv2.LINE_AA)


def _draw_dot(
    frame: np.ndarray,
    xy: np.ndarray,
    cf: np.ndarray,
    j: int,
    color: tuple[int, int, int],
    radius: int = 4,
) -> None:
    if cf[j] > _CONF_THRES:
        cx, cy = int(xy[j][0]), int(xy[j][1])
        cv2.circle(frame, (cx, cy), radius, color, -1, cv2.LINE_AA)


def draw_skeleton_with_errors(
    frame: np.ndarray,
    kp: dict | None,
    feature_errors: np.ndarray | None = None,
    mse_threshold: float = 0.05,
    lift_type: str = "squat",
) -> np.ndarray:
    """Draw skeleton on *frame* with per-segment error coloring.

    Parameters
    ----------
    kp : keypoint dict with "xy" (17,2) and "conf" (17,)
    feature_errors : per-feature MSE for this frame, shape (F,). None = neutral.
    mse_threshold : error above this → fully red.
    """
    if kp is None:
        return frame

    xy, cf = kp["xy"], kp["conf"]

    if lift_type == "squat" and feature_errors is not None:
        feature_bones = _SQUAT_FEATURE_BONES
    else:
        feature_bones = {}

    # Build a color lookup for each bone that has error data
    bone_colors: dict[tuple[int, int], tuple[int, int, int]] = {}
    if feature_errors is not None and feature_bones:
        for feat_idx, bones in feature_bones.items():
            if feat_idx < len(feature_errors):
                err = float(feature_errors[feat_idx])
                t = err / mse_threshold if mse_threshold > 0 else 0.0
                color = _lerp_color(t)
                for bone in bones:
                    bone_colors[bone] = color

    # Draw all skeleton bones
    for a, b in SKELETON:
        key = (a, b)
        key_rev = (b, a)
        if key in bone_colors:
            color = bone_colors[key]
        elif key_rev in bone_colors:
            color = bone_colors[key_rev]
        else:
            color = _COLOR_NEUTRAL
        _draw_bone(frame, xy, cf, a, b, color)

    # Draw joint dots — colored by the worst adjacent bone error
    for j in range(len(COCO_KPTS)):
        # Find the max error among bones touching this joint
        best_color = _COLOR_NEUTRAL
        max_err = -1.0
        if feature_errors is not None:
            for feat_idx, bones in feature_bones.items():
                if feat_idx >= len(feature_errors):
                    continue
                for ba, bb in bones:
                    if j == ba or j == bb:
                        err = float(feature_errors[feat_idx])
                        if err > max_err:
                            max_err = err
                            t = err / mse_threshold if mse_threshold > 0 else 0.0
                            best_color = _lerp_color(t)
        _draw_dot(frame, xy, cf, j, best_color)

    return frame


def _draw_banner(
    frame: np.ndarray,
    text: str,
    color: tuple[int, int, int],
) -> None:
    """Draw a semi-transparent banner at the top of *frame*."""
    h, w = frame.shape[:2]
    banner_h = 40
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(
        frame, text, (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
    )


def annotate_frames(
    frames: list[np.ndarray],
    keypoints: list[dict | None],
    per_frame_mse: np.ndarray | None = None,
    per_feature_mse: np.ndarray | None = None,
    mse_threshold: float = 0.05,
    label: str | None = None,
    lift_type: str = "squat",
) -> list[np.ndarray]:
    """Return a copy of *frames* with per-segment error-colored skeleton overlay.

    *per_feature_mse* shape (T_poses, F) — one row per frame where a pose was found.
    *per_frame_mse* shape (T_poses,) — overall MSE per pose frame (for banner).
    """
    annotated: list[np.ndarray] = []
    mse_idx = 0

    for i, frame in enumerate(frames):
        out = frame.copy()
        kp = keypoints[i] if i < len(keypoints) else None

        feat_err = None
        banner = label or ""
        banner_color = _COLOR_NEUTRAL

        if kp is not None and per_frame_mse is not None and mse_idx < len(per_frame_mse):
            overall_err = float(per_frame_mse[mse_idx])
            banner_color = _COLOR_BAD if overall_err > mse_threshold else _COLOR_GOOD
            banner = f"MSE: {overall_err:.4f}"
            if label:
                banner = f"{label}  |  {banner}"

            if per_feature_mse is not None and mse_idx < len(per_feature_mse):
                feat_err = per_feature_mse[mse_idx]

            mse_idx += 1

        if banner:
            _draw_banner(out, banner, banner_color)

        draw_skeleton_with_errors(
            out, kp,
            feature_errors=feat_err,
            mse_threshold=mse_threshold,
            lift_type=lift_type,
        )
        annotated.append(out)

    log.info("annotate_frames: annotated %d frames", len(annotated))
    return annotated
