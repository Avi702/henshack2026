"""Write annotated and comparison videos."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

from .video_io import write_video

log = logging.getLogger(__name__)

# Feature display names per lift type
_FEATURE_NAMES = {
    "squat": ["Knee", "Hip", "Spine", "Bar X"],
    "bench": ["Elbow", "Shoulder", "Bar Diag"],
    "deadlift": ["Back", "Hip Hinge", "Bar-Shin"],
}


def render_annotated_video(
    frames: list[np.ndarray],
    output_path: str | Path,
    fps: float = 30.0,
) -> Path:
    """Encode *frames* to mp4 at *output_path* and return the path."""
    return write_video(frames, output_path, fps=fps)


def _draw_feature_chart(
    width: int,
    height: int,
    x_values: np.ndarray,
    x_hat_values: np.ndarray,
    feature_names: list[str],
    current_frame: int,
) -> np.ndarray:
    """Render a small chart panel comparing X vs X_hat per feature."""
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    T, F = x_values.shape
    if T < 2 or F == 0:
        return canvas

    margin_top = 20
    margin_bot = 20
    margin_lr = 15
    row_h = (height - margin_top - margin_bot) // F

    for fi in range(F):
        y_off = margin_top + fi * row_h
        plot_h = row_h - 10
        plot_w = width - 2 * margin_lr

        # Normalise both series to the same range
        all_vals = np.concatenate([x_values[:, fi], x_hat_values[:, fi]])
        lo, hi = float(all_vals.min()), float(all_vals.max())
        span = hi - lo if hi - lo > 1e-6 else 1.0

        label = feature_names[fi] if fi < len(feature_names) else f"F{fi}"
        cv2.putText(canvas, label, (margin_lr, y_off + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        def _to_pt(t_idx: int, val: float) -> tuple[int, int]:
            px = margin_lr + int(t_idx / max(T - 1, 1) * plot_w)
            py = y_off + 15 + plot_h - int((val - lo) / span * plot_h)
            return (px, py)

        # Draw X (user) in green, X_hat (expert) in orange
        for t in range(T - 1):
            cv2.line(canvas, _to_pt(t, x_values[t, fi]), _to_pt(t + 1, x_values[t + 1, fi]),
                     (0, 255, 0), 1)
            cv2.line(canvas, _to_pt(t, x_hat_values[t, fi]), _to_pt(t + 1, x_hat_values[t + 1, fi]),
                     (0, 165, 255), 1)

        # Draw current-frame indicator line
        if 0 <= current_frame < T:
            cx = margin_lr + int(current_frame / max(T - 1, 1) * plot_w)
            cv2.line(canvas, (cx, y_off + 15), (cx, y_off + 15 + plot_h), (255, 255, 255), 1)

    # Legend at bottom
    cv2.putText(canvas, "You", (margin_lr, height - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
    cv2.putText(canvas, "Expert", (margin_lr + 50, height - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 165, 255), 1)

    return canvas


def render_comparison_video(
    frames: list[np.ndarray],
    keypoints: list[dict | None],
    x_values: np.ndarray,
    x_hat_values: np.ndarray,
    per_frame_mse: np.ndarray,
    lift_type: str,
    output_path: str | Path,
    fps: float = 3.0,
    mse_threshold: float = 0.05,
) -> Path:
    """Create a side-by-side video: annotated frame | feature chart (X vs X_hat).

    Left panel: the original frame with skeleton overlay.
    Right panel: line chart of user features vs expert reconstruction.
    """
    from .overlay import draw_skeleton, _draw_banner

    feature_names = _FEATURE_NAMES.get(lift_type, [f"F{i}" for i in range(x_values.shape[1])])

    combined: list[np.ndarray] = []
    mse_idx = 0

    for i, frame in enumerate(frames):
        left = frame.copy()
        kp = keypoints[i] if i < len(keypoints) else None

        if kp is not None and mse_idx < len(per_frame_mse):
            err = float(per_frame_mse[mse_idx])
            color = (0, 0, 255) if err > mse_threshold else (0, 255, 0)
            draw_skeleton(left, kp, color=color)
            _draw_banner(left, f"MSE: {err:.4f}", color)
            chart_frame = mse_idx
            mse_idx += 1
        else:
            draw_skeleton(left, kp, color=(255, 200, 0))
            chart_frame = 0

        h, w = left.shape[:2]
        chart_w = w  # same width as left panel
        chart = _draw_feature_chart(chart_w, h, x_values, x_hat_values, feature_names, chart_frame)

        side_by_side = np.hstack([left, chart])
        combined.append(side_by_side)

    log.info("render_comparison_video: %d combined frames -> %s", len(combined), output_path)
    return write_video(combined, output_path, fps=fps)
