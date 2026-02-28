"""HenShack 2026 — FastAPI backend for lift form analysis."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .schemas import AnalyzeResponse
from .pipeline import analyze

# Configure logging so pipeline modules emit to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-36s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(title="HenShack Lift Analyzer", version="0.1.0")

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_OUTPUTS_DIR = Path(__file__).resolve().parent / "artifacts" / "outputs"
_ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}


# ── Endpoints ───────────────────────────────────────────────

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze/video", response_model=AnalyzeResponse)
async def analyze_video(
    file: UploadFile = File(...),
    lift_type: Literal["squat", "bench", "deadlift"] = Form(...),
    return_artifacts: bool = Form(True),
):
    # Validate extension
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Accepted: {_ALLOWED_EXTENSIONS}",
        )

    video_bytes = await file.read()
    if not video_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    result = analyze.run(
        video_bytes=video_bytes,
        original_filename=file.filename or "upload.mp4",
        lift_type=lift_type,
        return_artifacts=return_artifacts,
    )
    return result


@app.get("/artifacts/{filename:path}")
def serve_artifact(filename: str):
    filepath = _OUTPUTS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return FileResponse(filepath, media_type="video/mp4")
