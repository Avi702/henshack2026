"""Generate human-readable form feedback from analysis results."""

from __future__ import annotations

import numpy as np

from ..schemas import AIFeedback, Issue

# ── thresholds (per-feature MSE) ────────────────────────────
# Squat features: [shoulder-hip-knee angle, other_hip-hip-knee angle, hip-knee-ankle angle]
_SQUAT_ISSUE_MAP = {
    0: ("HIP_ANGLE", "Hip angle (shoulder-hip-knee) deviates from expert pattern — check torso lean"),
    1: ("HIP_SHIFT", "Hip alignment (cross-hip angle) inconsistency — check for lateral shift"),
    2: ("KNEE_ANGLE", "Knee angle deviates from expert pattern — check depth and tracking"),
}

_BENCH_ISSUE_MAP = {
    0: ("ELBOW_FLARE", "Elbow angle deviation — possible excessive flare"),
    1: ("SHOULDER_POS", "Shoulder angle inconsistency — check scapular retraction"),
    2: ("BAR_PATH", "Bar path deviating from optimal diagonal"),
}

_DEADLIFT_ISSUE_MAP = {
    0: ("BACK_ROUND", "Back rounding detected — maintain neutral spine"),
    1: ("HIP_HINGE", "Hip hinge pattern off — initiate pull with hips"),
    2: ("BAR_DRIFT", "Bar drifting away from shins — keep bar close"),
}

_ISSUE_MAPS = {
    "squat": _SQUAT_ISSUE_MAP,
    "bench": _BENCH_ISSUE_MAP,
    "deadlift": _DEADLIFT_ISSUE_MAP,
}


def _severity(mse: float) -> str:
    if mse > 0.10:
        return "high"
    if mse > 0.05:
        return "medium"
    return "low"


def detect_issues(
    lift_type: str,
    per_feature_mse: np.ndarray,
    per_frame_mse: np.ndarray | None = None,
    feature_mse_threshold: float = 0.03,
) -> list[Issue]:
    """Identify form issues based on per-feature reconstruction error.

    Parameters
    ----------
    per_feature_mse : shape (T, F) — reconstruction error per feature per frame
    per_frame_mse : shape (T,) — overall MSE per frame (for finding worst frame)
    """
    issue_map = _ISSUE_MAPS.get(lift_type, {})
    issues: list[Issue] = []

    if per_feature_mse.size == 0:
        return issues

    # worst frame index (overall MSE or feature-mean)
    if per_frame_mse is not None and per_frame_mse.size > 0:
        worst_frame = int(per_frame_mse.argmax())
    else:
        worst_frame = int(per_feature_mse.mean(axis=1).argmax())

    for feat_idx, (code, msg) in issue_map.items():
        if feat_idx >= per_feature_mse.shape[1]:
            continue
        # Mean reconstruction error for this feature across all frames
        feat_mean_mse = float(per_feature_mse[:, feat_idx].mean())
        if feat_mean_mse > feature_mse_threshold:
            # Find the worst frame for THIS specific feature
            feat_worst = int(per_feature_mse[:, feat_idx].argmax())
            issues.append(Issue(
                code=code,
                severity=_severity(feat_mean_mse),
                message=msg,
                evidence_frame=feat_worst,
            ))

    return issues


def generate_feedback(
    lift_type: str,
    mse_mean: float | None,
    issues: list[Issue],
) -> AIFeedback:
    """Build a plain-text feedback summary (no LLM call in stub mode)."""
    if mse_mean is None:
        return AIFeedback(
            summary="Could not analyze form — no expert model loaded.",
            bullets=["Train the expert model first with neuralnet.py"],
        )

    if not issues:
        return AIFeedback(
            summary=f"Your {lift_type} form looks solid! MSE {mse_mean:.4f}.",
            bullets=["No major deviations from the expert pattern detected."],
        )

    bullets = [f"[{i.severity.upper()}] {i.message}" for i in issues]
    return AIFeedback(
        summary=f"Found {len(issues)} potential issue(s) in your {lift_type}.",
        bullets=bullets,
    )
