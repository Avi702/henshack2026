"""Gemini API integration for AI coaching suggestions."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import google.generativeai as genai

log = logging.getLogger(__name__)


def _load_api_key() -> str:
    """Read GEMINI_API_KEY from env or project .env.local file."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    env_file = Path(__file__).resolve().parents[2] / ".env.local"
    project_env = Path(__file__).resolve().parents[3] / ".env.local"
    for p in (env_file, project_env):
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return ""


_API_KEY = _load_api_key()


def get_coaching(
    lift_type: str,
    overall_label: str,
    score: float | None,
    mse_mean: float | None,
    issues: list[dict],
    ai_feedback_summary: str,
    ai_feedback_bullets: list[str],
) -> str:
    """Call Gemini to generate personalized coaching advice."""
    if not _API_KEY:
        return "Set the GEMINI_API_KEY environment variable to enable AI coaching suggestions."

    genai.configure(api_key=_API_KEY)

    issues_text = ""
    if issues:
        for iss in issues:
            issues_text += f"  - [{iss.get('severity', '?').upper()}] {iss.get('message', '')}\n"
    else:
        issues_text = "  No major issues detected.\n"

    prompt = f"""You are SquatBuddy, a friendly and knowledgeable AI strength coach.
A user just analyzed their {lift_type} form using computer vision and an autoencoder model.

Here are the results:
- Overall verdict: {overall_label}
- Form score: {score if score is not None else 'N/A'}
- Mean reconstruction error (MSE): {mse_mean if mse_mean is not None else 'N/A'}
- AI feedback summary: {ai_feedback_summary}
- Feedback bullets:
  {chr(10).join(f'  - {b}' for b in ai_feedback_bullets)}
- Detected issues:
{issues_text}

Based on these results, provide:
1. A brief (2-3 sentence) overall assessment of their form
2. 3-4 specific, actionable tips to improve their {lift_type} technique
3. One encouraging note to keep them motivated

Keep your response concise, friendly, and practical. Use simple language a gym-goer would understand.
Do NOT use markdown headers — just write naturally with numbered tips. Keep the total response under 200 words."""

    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        response = model.generate_content(prompt)
        return response.text or "Could not generate coaching advice."
    except Exception as e:
        log.error("Gemini API error: %s", e)
        return f"AI coaching temporarily unavailable: {e}"
