"""Read / write video files with OpenCV, with optional frame sampling."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

log = logging.getLogger(__name__)


def video_meta(video_path: str | Path) -> dict:
    """Return fps, frame size, and total frame count for a video file."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return {"fps": fps, "width": w, "height": h, "total_frames": total}


def read_frames(video_path: str | Path) -> list[np.ndarray]:
    """Return every BGR frame from *video_path*."""
    cap = cv2.VideoCapture(str(video_path))
    frames: list[np.ndarray] = []
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    log.info("read_frames: %d raw frames from %s", len(frames), video_path)
    return frames


def sample_frames(
    video_path: str | Path,
    *,
    target_fps: float = 3.0,
    max_frames: int = 30,
    resize_width: int = 640,
) -> tuple[list[np.ndarray], float, list[int]]:
    """Read *video_path* and return a down-sampled, resized list of frames.

    Returns
    -------
    frames : list[np.ndarray]
        BGR frames, resized so width == *resize_width* (aspect preserved).
    effective_fps : float
        The actual fps the returned frames represent.
    original_indices : list[int]
        Which frame numbers (0-based) in the source video were kept.
    """
    cap = cv2.VideoCapture(str(video_path))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # How many source frames to skip between samples
    step = max(1, round(src_fps / target_fps))

    frames: list[np.ndarray] = []
    indices: list[int] = []
    idx = 0

    while cap.isOpened() and len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            # Resize keeping aspect ratio
            h, w = frame.shape[:2]
            if w != resize_width:
                scale = resize_width / w
                new_h = int(h * scale)
                frame = cv2.resize(frame, (resize_width, new_h))
            frames.append(frame)
            indices.append(idx)
        idx += 1

    cap.release()
    effective_fps = target_fps if step > 1 else src_fps

    log.info(
        "sample_frames: %d/%d frames kept (step=%d, target_fps=%.1f, src_fps=%.1f)",
        len(frames), total, step, target_fps, src_fps,
    )
    return frames, effective_fps, indices


def write_video(
    frames: list[np.ndarray],
    out_path: str | Path,
    fps: float = 30.0,
) -> Path:
    """Write *frames* to an mp4 file at *out_path*."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
    for f in frames:
        writer.write(f)
    writer.release()
    log.info("write_video: %d frames -> %s (%.1f fps)", len(frames), out_path, fps)
    return out_path
