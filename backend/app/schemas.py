"""Pydantic models for the /analyze/video response."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── sub-models ──────────────────────────────────────────────

class OverallVerdict(BaseModel):
    label: Literal["good_form", "bad_form", "unknown"] = "unknown"
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class Issue(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    message: str
    evidence_frame: int


class Artifacts(BaseModel):
    annotated_video_url: Optional[str] = None
    comparison_video_url: Optional[str] = None


class AIFeedback(BaseModel):
    summary: str = ""
    bullets: list[str] = Field(default_factory=list)


class DebugInfo(BaseModel):
    frames_analyzed: int = 0
    poses_found: int = 0
    notes: str = ""


# ── top-level response ─────────────────────────────────────

class AnalyzeResponse(BaseModel):
    lift_type: str
    overall: OverallVerdict = Field(default_factory=OverallVerdict)
    score: Optional[float] = None
    mse_mean: Optional[float] = None
    issues: list[Issue] = Field(default_factory=list)
    artifacts: Artifacts = Field(default_factory=Artifacts)
    ai_feedback: AIFeedback = Field(default_factory=AIFeedback)
    debug: DebugInfo = Field(default_factory=DebugInfo)


class CoachingRequest(BaseModel):
    lift_type: str
    overall_label: str = "unknown"
    score: Optional[float] = None
    mse_mean: Optional[float] = None
    issues: list[dict] = Field(default_factory=list)
    ai_feedback_summary: str = ""
    ai_feedback_bullets: list[str] = Field(default_factory=list)


class CoachingResponse(BaseModel):
    coaching: str
