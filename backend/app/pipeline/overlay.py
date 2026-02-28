"""Draw skeleton + per-frame status on video frames."""

from __future__ import annotations

import logging

import cv2
import numpy as np

from .pose import SKELETON, COCO_KPTS

log = logging.getLogger(__name__)

_CONF_THRES = 0.5
_COLOR_GOOD = (0, 255, 0)      # green
_COLOR_BAD = (0, 0, 255)       # red
_COLOR_NEUTRAL = (255, 200, 0) # cyan-ish
_COLOR_EXPERT = (255, 165, 0)  # orange — reconstructed / expert overlay


def draw_skeleton(
    frame: np.ndarray,
    kp: dict | None,
    *,
    color: tuple[int, int, int] = _COLOR_GOOD,
    thickness: int = 2,
    dot_radius: int = 4,
) -> np.ndarray:
    """Draw keypoint dots and skeleton lines on *frame* (mutates in-place)."""
    if kp is None:
        return frame

    xy, cf = kp["xy"], kp["conf"]

    for a, b in SKELETON:
        if cf[a] > _CONF_THRES and cf[b] > _CONF_THRES:
            pt1 = (int(xy[a][0]), int(xy[a][1]))
            pt2 = (int(xy[b][0]), int(xy[b][1]))
            cv2.line(frame, pt1, pt2, color, thickness)

    for j in range(len(COCO_KPTS)):
        if cf[j] > _CONF_THRES:
            cx, cy = int(xy[j][0]), int(xy[j][1])
            cv2.circle(frame, (cx, cy), dot_radius, color, -1)

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
    mse_threshold: float = 0.05,
    label: str | None = None,
) -> list[np.ndarray]:
    """Return a copy of *frames* with skeleton overlay and form indicator.

    *keypoints* must be the same length as *frames*.
    *per_frame_mse* (if given) has one entry per frame **where a pose was found**,
    so we index it with a separate counter.
    """
    annotated: list[np.ndarray] = []
    mse_idx = 0

    for i, frame in enumerate(frames):
        out = frame.copy()
        kp = keypoints[i] if i < len(keypoints) else None

        # Determine colour and banner text based on MSE
        if kp is not None and per_frame_mse is not None and mse_idx < len(per_frame_mse):
            err = float(per_frame_mse[mse_idx])
            color = _COLOR_BAD if err > mse_threshold else _COLOR_GOOD
            banner = f"MSE: {err:.4f}"
            if label:
                banner = f"{label}  |  {banner}"
            mse_idx += 1
        else:
            color = _COLOR_NEUTRAL
            banner = label or ""

        if banner:
            _draw_banner(out, banner, color)

        draw_skeleton(out, kp, color=color)
        annotated.append(out)

    log.info("annotate_frames: annotated %d frames", len(annotated))
    return annotated
