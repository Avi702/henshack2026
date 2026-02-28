"""Top-level analysis orchestrator.

Ties together video I/O, pose estimation, feature extraction,
expert model inference, overlay rendering, and feedback generation.

Always produces an annotated video with skeleton overlay.
If an expert model checkpoint exists, also computes MSE scoring
and generates a side-by-side comparison video (X vs X_hat).
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import numpy as np

from ..schemas import (
    AIFeedback,
    AnalyzeResponse,
    Artifacts,
    DebugInfo,
    Issue,
    OverallVerdict,
)
from . import video_io, overlay, render
from .pose import extract_keypoints
from .features import extract as extract_features
from .expert_model import load_expert, compute_mse
from .feedback import detect_issues, generate_feedback

log = logging.getLogger(__name__)

# Directories for uploaded / output files
_ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
_INPUTS_DIR = _ARTIFACTS_DIR / "inputs"
_OUTPUTS_DIR = _ARTIFACTS_DIR / "outputs"

_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

# ── heuristic thresholds ────────────────────────────────────
_MSE_GOOD_THRESHOLD = 0.05   # below → good_form
_MSE_OVERLAY_THRESHOLD = 0.05  # per-frame red/green cutoff


def run(
    video_bytes: bytes,
    original_filename: str,
    lift_type: str,
    return_artifacts: bool = True,
) -> AnalyzeResponse:
    """Full analysis pipeline.

    1. Save uploaded video
    2. Sample frames (3 FPS, max 30, resize 640w)
    3. Run YOLOv8 pose estimation
    4. Extract lift-specific features
    5. (optional) Score against the expert autoencoder
    6. Annotate video + generate feedback
    """
    run_id = uuid.uuid4().hex[:12]
    log.info("[%s] === START  lift=%s  file=%s ===", run_id, lift_type, original_filename)

    # ── 1. persist upload ───────────────────────────────────
    ext = Path(original_filename).suffix or ".mp4"
    input_name = f"{run_id}{ext}"
    input_path = _INPUTS_DIR / input_name
    input_path.write_bytes(video_bytes)
    log.info("[%s] saved upload → %s (%d bytes)", run_id, input_path.name, len(video_bytes))

    # ── 2. sample frames ───────────────────────────────────
    frames, effective_fps, orig_indices = video_io.sample_frames(input_path)
    if not frames:
        log.warning("[%s] no frames decoded — aborting", run_id)
        return AnalyzeResponse(
            lift_type=lift_type,
            debug=DebugInfo(notes="could not read any frames from uploaded video"),
        )

    log.info("[%s] sampled %d frames @ %.1f fps", run_id, len(frames), effective_fps)

    # ── 3. pose estimation ─────────────────────────────────
    log.info("[%s] running YOLOv8 pose estimation …", run_id)
    keypoints = extract_keypoints(frames)
    poses_found = sum(1 for k in keypoints if k is not None)
    log.info("[%s] poses detected in %d / %d frames", run_id, poses_found, len(frames))

    # ── 4. feature extraction ──────────────────────────────
    log.info("[%s] extracting %s features …", run_id, lift_type)
    features = extract_features(lift_type, keypoints)
    log.info("[%s] feature matrix shape: %s", run_id, features.shape)

    # ── 5. expert scoring (if model exists) ────────────────
    model = load_expert(lift_type, models_dir=_MODELS_DIR)
    mse_mean: float | None = None
    per_frame_mse: np.ndarray | None = None
    per_feature_mse: np.ndarray | None = None
    reconstruction: np.ndarray | None = None

    if model is not None and features.shape[0] > 0:
        log.info("[%s] running expert autoencoder inference …", run_id)
        mse_mean, per_frame_mse, per_feature_mse, reconstruction = compute_mse(model, features)
        log.info("[%s] mse_mean=%.5f", run_id, mse_mean)
    elif model is None:
        log.info("[%s] no expert model found — skipping scoring", run_id)
    else:
        log.info("[%s] no valid poses → skipping scoring", run_id)

    # ── 6. issues + feedback ───────────────────────────────
    issues: list[Issue] = []
    if per_feature_mse is not None:
        issues = detect_issues(lift_type, per_feature_mse, per_frame_mse)
        log.info("[%s] detected %d issues", run_id, len(issues))

    fb = generate_feedback(lift_type, mse_mean, issues)

    # ── 7. overall verdict ─────────────────────────────────
    if mse_mean is None:
        verdict = OverallVerdict(label="unknown", confidence=0.0)
        score = None
    else:
        label = "good_form" if mse_mean < _MSE_GOOD_THRESHOLD else "bad_form"
        confidence = min(1.0, max(0.0, 1.0 - mse_mean))
        verdict = OverallVerdict(label=label, confidence=round(confidence, 3))
        score = round(max(0.0, 1.0 - mse_mean * 10), 2)

    # ── 8. artifacts ───────────────────────────────────────
    artifacts = Artifacts()
    if return_artifacts:
        # Always: annotated video with skeleton
        form_label = verdict.label.replace("_", " ").title() if mse_mean is not None else None
        annotated_frames = overlay.annotate_frames(
            frames, keypoints, per_frame_mse,
            per_feature_mse=per_feature_mse,
            mse_threshold=_MSE_OVERLAY_THRESHOLD,
            label=form_label,
            lift_type=lift_type,
        )
        ann_name = f"{run_id}_annotated.mp4"
        render.render_annotated_video(
            annotated_frames, _OUTPUTS_DIR / ann_name, fps=effective_fps,
        )
        artifacts.annotated_video_url = f"/artifacts/{ann_name}"
        log.info("[%s] annotated video → %s", run_id, ann_name)

        # Comparison video only when expert model was available
        if reconstruction is not None and per_frame_mse is not None:
            cmp_name = f"{run_id}_comparison.mp4"
            render.render_comparison_video(
                frames, keypoints,
                x_values=features,
                x_hat_values=reconstruction,
                per_frame_mse=per_frame_mse,
                per_feature_mse=per_feature_mse,
                lift_type=lift_type,
                output_path=_OUTPUTS_DIR / cmp_name,
                fps=effective_fps,
                mse_threshold=_MSE_OVERLAY_THRESHOLD,
            )
            artifacts.comparison_video_url = f"/artifacts/{cmp_name}"
            log.info("[%s] comparison video → %s", run_id, cmp_name)

    notes_parts = [
        f"model={'loaded' if model else 'missing'}",
        f"sampled_fps={effective_fps:.1f}",
        f"resize_w=640",
    ]

    log.info("[%s] === DONE ===", run_id)

    return AnalyzeResponse(
        lift_type=lift_type,
        overall=verdict,
        score=score,
        mse_mean=round(mse_mean, 5) if mse_mean is not None else None,
        issues=issues,
        artifacts=artifacts,
        ai_feedback=fb,
        debug=DebugInfo(
            frames_analyzed=len(frames),
            poses_found=poses_found,
            notes="; ".join(notes_parts),
        ),
    )
